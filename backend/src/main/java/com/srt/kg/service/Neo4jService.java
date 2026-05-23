package com.srt.kg.service;

import org.neo4j.driver.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.util.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class Neo4jService {

    private static final Logger log = LoggerFactory.getLogger(Neo4jService.class);

    @Value("${neo4j.uri}")
    private String uri;
    @Value("${neo4j.username}")
    private String username;
    @Value("${neo4j.password}")
    private String password;

    private Driver driver;
    private boolean available = false;

    @PostConstruct
    public void init() {
        try {
            driver = GraphDatabase.driver(uri, AuthTokens.basic(username, password));
            driver.verifyConnectivity();
            available = true;
            log.info("Neo4j connected successfully: {}", uri);
        } catch (Exception e) {
            log.warn("Neo4j not available: {}. Running in fallback mode.", e.getMessage());
            available = false;
        }
    }

    @PreDestroy
    public void close() {
        if (driver != null) driver.close();
    }

    private Map<String, Object> emptyGraph() {
        Map<String, Object> graph = new HashMap<>();
        graph.put("nodes", new ArrayList<>());
        graph.put("edges", new ArrayList<>());
        return graph;
    }

    public Map<String, Object> getAllGraph() {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            String cypher = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 500";
            Result result = session.run(cypher);
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j getAllGraph error", e);
            return emptyGraph();
        }
    }

    public Map<String, Object> searchNode(String keyword) {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            String cypher = "MATCH (n) WHERE n.name CONTAINS $keyword OPTIONAL MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 100";
            Result result = session.run(cypher, Map.of("keyword", keyword));
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j searchNode error", e);
            return emptyGraph();
        }
    }

    public Map<String, Object> filterByTime(String startTime, String endTime, String industry) {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            StringBuilder cypher = new StringBuilder(
                "MATCH (i:Investor)-[r:INVEST]->(e:Enterprise) "
                + "WHERE r.time >= $start AND r.time <= $end "
            );
            Map<String, Object> params = new HashMap<>();
            params.put("start", startTime);
            params.put("end", endTime);

            if (industry != null && !industry.isEmpty()) {
                cypher.append("AND EXISTS { MATCH (e)-[:BELONGS_TO]->(:Industry {name: $industry}) } ");
                params.put("industry", industry);
            }

            cypher.append("RETURN i as n, r, e as m LIMIT 200");
            Result result = session.run(cypher.toString(), params);
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j filterByTime error", e);
            return emptyGraph();
        }
    }

    public void importTriples(JSONArray triples) {
        if (!available) {
            log.warn("Neo4j not available, skipping import of {} triples", triples.size());
            return;
        }
        try (Session session = driver.session()) {
            for (int i = 0; i < triples.size(); i++) {
                JSONObject triple = triples.getJSONObject(i);
                String head = triple.getString("head");
                String relation = triple.getString("relation");
                String tail = triple.getString("tail");
                String time = triple.getString("time");
                String headType = triple.getString("headType");
                String tailType = triple.getString("tailType");
                if (headType == null || headType.isEmpty()) headType = "Enterprise";
                if (tailType == null || tailType.isEmpty()) tailType = "Enterprise";

                String round = triple.getString("round");
                String amount = triple.getString("amount");

                String cypher = "MERGE (h:" + headType + " {name: $head}) "
                    + "MERGE (t:" + tailType + " {name: $tail}) "
                    + "MERGE (h)-[rel:" + relation + "]->(t) "
                    + "SET rel.time = $time, rel.round = $round, rel.amount = $amount, "
                    + "rel.start_time = $time, rel.end_time = $time";
                Map<String, Object> params = new HashMap<>();
                params.put("head", head);
                params.put("tail", tail);
                params.put("time", time != null ? time : "");
                params.put("round", round != null ? round : "");
                params.put("amount", amount != null ? amount : "");
                session.run(cypher, params);
            }
        }
    }

    public void importIndustryData(JSONArray industries) {
        if (!available) {
            log.warn("Neo4j not available, skipping industry import");
            return;
        }
        try (Session session = driver.session()) {
            for (int i = 0; i < industries.size(); i++) {
                JSONObject item = industries.getJSONObject(i);
                String industry = item.getString("industry");
                JSONArray enterprises = item.getJSONArray("enterprises");
                session.run("MERGE (ind:Industry {name: $name})",
                    Map.of("name", industry));
                for (int j = 0; j < enterprises.size(); j++) {
                    String entName = enterprises.getString(j);
                    session.run(
                        "MERGE (e:Enterprise {name: $ent}) "
                        + "MERGE (ind:Industry {name: $ind}) "
                        + "MERGE (e)-[:BELONGS_TO]->(ind)",
                        Map.of("ent", entName, "ind", industry)
                    );
                }
            }
        }
    }

    /** 投资方追投模式查询：同一投资方多次投资同一企业 */
    public Map<String, Object> getReInvestmentPattern() {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            String cypher = "MATCH (i:Investor)-[r1:INVEST]->(e:Enterprise)<-[r2:INVEST]-(i) "
                + "WHERE r1.time < r2.time "
                + "RETURN i AS n, r1 AS r, e AS m LIMIT 100";
            Result result = session.run(cypher);
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j getReInvestmentPattern error", e);
            return emptyGraph();
        }
    }

    /** 跨行业投资统计：按行业聚合投资数量和金额 */
    public List<Map<String, Object>> getCrossIndustryInvestment(String startTime, String endTime) {
        if (!available) return new ArrayList<>();
        try (Session session = driver.session()) {
            String cypher = "MATCH (i:Investor)-[r:INVEST]->(e:Enterprise)-[:BELONGS_TO]->(ind:Industry) "
                + "WHERE r.time >= $start AND r.time <= $end "
                + "RETURN ind.name as industry, count(r) as investCount, "
                + "sum(CASE WHEN r.amount IS NOT NULL THEN toFloat(r.amount) ELSE 0 END) as totalAmount "
                + "ORDER BY investCount DESC";
            Result result = session.run(cypher, Map.of("start", startTime, "end", endTime));
            List<Map<String, Object>> list = new ArrayList<>();
            while (result.hasNext()) {
                org.neo4j.driver.Record rec = result.next();
                Map<String, Object> item = new HashMap<>();
                item.put("industry", rec.get("industry").asString());
                item.put("investCount", rec.get("investCount").asInt());
                item.put("totalAmount", rec.get("totalAmount").asNumber());
                list.add(item);
            }
            return list;
        } catch (Exception e) {
            log.error("Neo4j getCrossIndustryInvestment error", e);
            return new ArrayList<>();
        }
    }

    /** 企业融资历史查询 */
    public Map<String, Object> getEnterpriseHistory(String enterpriseName) {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            String cypher = "MATCH (i:Investor)-[r:INVEST]->(e:Enterprise {name: $name}) "
                + "RETURN i AS n, r, e AS m ORDER BY r.start_time ASC";
            Result result = session.run(cypher, Map.of("name", enterpriseName));
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j getEnterpriseHistory error", e);
            return emptyGraph();
        }
    }

    /** 时序范围查询：按start_time/end_time过滤关系 */
    public Map<String, Object> filterByTemporalRange(String startTime, String endTime) {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            String cypher = "MATCH (n)-[r]->(m) "
                + "WHERE r.start_time >= $start AND r.start_time <= $end "
                + "RETURN n, r, m ORDER BY r.start_time ASC LIMIT 300";
            Result result = session.run(cypher, Map.of("start", startTime, "end", endTime));
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j filterByTemporalRange error", e);
            return emptyGraph();
        }
    }

    /** 某行业某年的投资事件列表 */
    public List<Map<String, Object>> getIndustryEvents(String industryName, String year) {
        if (!available) return new ArrayList<>();
        try (Session session = driver.session()) {
            StringBuilder cypher = new StringBuilder(
                "MATCH (i:Investor)-[r:INVEST]->(e:Enterprise)-[:BELONGS_TO]->(ind:Industry {name: $name}) "
            );
            Map<String, Object> params = new HashMap<>();
            params.put("name", industryName);
            if (year != null && !year.isEmpty()) {
                cypher.append("WHERE r.time STARTS WITH $year ");
                params.put("year", year);
            }
            cypher.append("RETURN e.name as name, r.round as round, r.amount as amount, r.time as time "
                + "ORDER BY r.time DESC LIMIT 50");
            Result result = session.run(cypher.toString(), params);
            List<Map<String, Object>> list = new ArrayList<>();
            while (result.hasNext()) {
                org.neo4j.driver.Record rec = result.next();
                Map<String, Object> item = new HashMap<>();
                item.put("name", rec.get("name").asString());
                item.put("round", rec.get("round").isNull() ? "" : rec.get("round").asString());
                item.put("amount", rec.get("amount").isNull() ? "" : rec.get("amount").asString());
                item.put("time", rec.get("time").isNull() ? "" : rec.get("time").asString());
                list.add(item);
            }
            return list;
        } catch (Exception e) {
            log.error("Neo4j getIndustryEvents error", e);
            return new ArrayList<>();
        }
    }

    /** 风险传导路径查询 */
    public Map<String, Object> getRiskPath(String sourceName, int depth) {
        if (!available) return emptyGraph();
        try (Session session = driver.session()) {
            String cypher = "MATCH (s)-[r*1.." + depth + "]->(t) "
                + "WHERE s.name = $source "
                + "RETURN s AS n, last(r) AS r, t AS m LIMIT 100";
            Result result = session.run(cypher, Map.of("source", sourceName));
            return buildGraphFromResult(result);
        } catch (Exception e) {
            log.error("Neo4j getRiskPath error", e);
            return emptyGraph();
        }
    }

    public Map<String, Object> getStatistics() {
        if (!available) {
            Map<String, Object> stats = new HashMap<>();
            stats.put("enterpriseCount", 0);
            stats.put("investorCount", 0);
            stats.put("industryCount", 0);
            stats.put("relationCount", 0);
            stats.put("neo4jAvailable", false);
            return stats;
        }
        try (Session session = driver.session()) {
            Map<String, Object> stats = new HashMap<>();
            stats.put("enterpriseCount", session.run("MATCH (n:Enterprise) RETURN count(n) as c").single().get("c").asInt());
            stats.put("investorCount", session.run("MATCH (n:Investor) RETURN count(n) as c").single().get("c").asInt());
            stats.put("industryCount", session.run("MATCH (n:Industry) RETURN count(n) as c").single().get("c").asInt());
            stats.put("relationCount", session.run("MATCH ()-[r]->() RETURN count(r) as c").single().get("c").asInt());
            stats.put("neo4jAvailable", true);
            return stats;
        } catch (Exception e) {
            log.error("Neo4j getStatistics error", e);
            Map<String, Object> stats = new HashMap<>();
            stats.put("enterpriseCount", 0);
            stats.put("investorCount", 0);
            stats.put("industryCount", 0);
            stats.put("relationCount", 0);
            stats.put("neo4jAvailable", false);
            return stats;
        }
    }

    private Map<String, Object> buildGraphFromResult(Result result) {
        Set<String> nodeIds = new LinkedHashSet<>();
        List<Map<String, Object>> nodes = new ArrayList<>();
        List<Map<String, Object>> edges = new ArrayList<>();

        while (result.hasNext()) {
            org.neo4j.driver.Record record = result.next();

            if (record.containsKey("n") && !record.get("n").isNull()) {
                org.neo4j.driver.types.Node n = record.get("n").asNode();
                addNode(nodes, nodeIds, n);
            }
            if (record.containsKey("m") && !record.get("m").isNull()) {
                org.neo4j.driver.types.Node m = record.get("m").asNode();
                addNode(nodes, nodeIds, m);
            }
            if (record.containsKey("r") && !record.get("r").isNull()) {
                org.neo4j.driver.types.Relationship r = record.get("r").asRelationship();
                if (record.containsKey("n") && !record.get("n").isNull() && record.containsKey("m") && !record.get("m").isNull()) {
                    addEdge(edges, r, record.get("n").asNode(), record.get("m").asNode());
                }
            }
        }

        Map<String, Object> graph = new HashMap<>();
        graph.put("nodes", nodes);
        graph.put("edges", edges);
        return graph;
    }

    private void addNode(List<Map<String, Object>> nodes, Set<String> nodeIds, org.neo4j.driver.types.Node node) {
        String id = String.valueOf(node.id());
        if (nodeIds.add(id)) {
            Map<String, Object> n = new HashMap<>();
            n.put("id", id);
            n.put("label", node.labels().iterator().next());
            Map<String, Object> props = new HashMap<>(node.asMap());
            n.put("properties", props);
            nodes.add(n);
        }
    }

    private void addEdge(List<Map<String, Object>> edges, org.neo4j.driver.types.Relationship rel,
                          org.neo4j.driver.types.Node from, org.neo4j.driver.types.Node to) {
        Map<String, Object> edge = new HashMap<>();
        edge.put("id", String.valueOf(rel.id()));
        edge.put("from", String.valueOf(from.id()));
        edge.put("to", String.valueOf(to.id()));
        edge.put("label", rel.type());
        Map<String, Object> props = new HashMap<>(rel.asMap());
        edge.put("properties", props);
        edges.add(edge);
    }
}
