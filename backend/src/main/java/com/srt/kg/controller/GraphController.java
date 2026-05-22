package com.srt.kg.controller;

import com.srt.kg.service.Neo4jService;
import com.alibaba.fastjson.JSONArray;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class GraphController {

    @Autowired
    private Neo4jService neo4jService;

    @GetMapping("/graph/all")
    public Map<String, Object> getAllGraph() {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.getAllGraph());
        return result;
    }

    @GetMapping("/graph/search")
    public Map<String, Object> search(@RequestParam String keyword) {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.searchNode(keyword));
        return result;
    }

    @GetMapping("/graph/filter")
    public Map<String, Object> filter(
            @RequestParam String startTime,
            @RequestParam String endTime,
            @RequestParam(required = false) String industry) {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.filterByTime(startTime, endTime, industry));
        return result;
    }

    @PostMapping("/import")
    public Map<String, Object> importTriples(@RequestBody Map<String, Object> body) {
        List<?> rawTriples = (List<?>) body.get("triples");
        JSONArray triples = new JSONArray(rawTriples);
        neo4jService.importTriples(triples);
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "导入成功");
        result.put("data", Map.of("count", triples.size()));
        return result;
    }

    @PostMapping("/import-industry")
    public Map<String, Object> importIndustry(@RequestBody Map<String, Object> body) {
        List<?> raw = (List<?>) body.get("industries");
        JSONArray industries = new JSONArray(raw);
        neo4jService.importIndustryData(industries);
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "行业数据导入成功");
        result.put("data", Map.of("count", industries.size()));
        return result;
    }

    @GetMapping("/statistics")
    public Map<String, Object> statistics() {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.getStatistics());
        return result;
    }

    @GetMapping("/graph/reinvestment")
    public Map<String, Object> reInvestmentPattern() {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.getReInvestmentPattern());
        return result;
    }

    @GetMapping("/analytics/heatmap")
    public Map<String, Object> heatmap(
            @RequestParam String startYear,
            @RequestParam String endYear) {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.getCrossIndustryInvestment(startYear, endYear));
        return result;
    }

    @GetMapping("/enterprise/{name}/history")
    public Map<String, Object> enterpriseHistory(@PathVariable String name) {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.getEnterpriseHistory(name));
        return result;
    }

    @GetMapping("/risk/path")
    public Map<String, Object> riskPath(
            @RequestParam String source,
            @RequestParam(defaultValue = "3") int depth) {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", neo4jService.getRiskPath(source, depth));
        return result;
    }
}
