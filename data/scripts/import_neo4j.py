"""从MySQL导入数据到Neo4j图数据库"""
import pymysql
from neo4j import GraphDatabase
from decimal import Decimal


class Neo4jImporter:
    def __init__(self, mysql_config, neo4j_uri, neo4j_user, neo4j_password):
        self.mysql_conn = pymysql.connect(**mysql_config, charset='utf8mb4')
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def import_all(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            self._import_industries(session)
            self._import_enterprises(session)
            self._import_investors(session)
            self._import_events(session)
        print("数据导入Neo4j完成")

    def _import_industries(self, session):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT id, name FROM industry")
        rows = cursor.fetchall()
        for row in rows:
            session.run("CREATE (i:Industry {mysql_id: $id, name: $name})", id=row[0], name=row[1])
        print(f"导入 {len(rows)} 个行业节点")

    def _import_enterprises(self, session):
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT e.id, e.name, e.description, e.status, i.name as industry_name "
            "FROM enterprise e LEFT JOIN industry i ON e.industry_id = i.id"
        )
        rows = cursor.fetchall()
        for row in rows:
            session.run(
                "CREATE (e:Enterprise {mysql_id: $id, name: $name, description: $desc, status: $status})",
                id=row['id'], name=row['name'], desc=row['description'] or '', status=row['status'] or 'active'
            )
            if row['industry_name']:
                session.run(
                    "MATCH (e:Enterprise {mysql_id: $eid}), (i:Industry {name: $iname}) "
                    "CREATE (e)-[:BELONGS_TO]->(i)",
                    eid=row['id'], iname=row['industry_name']
                )
        print(f"导入 {len(rows)} 个企业节点")

    def _import_investors(self, session):
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, name, type, description FROM investor")
        rows = cursor.fetchall()
        for row in rows:
            session.run(
                "CREATE (i:Investor {mysql_id: $id, name: $name, type: $type, description: $desc})",
                id=row['id'], name=row['name'], type=row['type'] or '', desc=row['description'] or ''
            )
        print(f"导入 {len(rows)} 个投资方节点")

    def _import_events(self, session):
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT ev.enterprise_id, ev.investor_id, ev.round, ev.amount, ev.time, "
            "ev.lead_flag, ev.relation, e.name as enterprise_name, i.name as investor_name "
            "FROM investment_event ev "
            "JOIN enterprise e ON ev.enterprise_id = e.id "
            "JOIN investor i ON ev.investor_id = i.id"
        )
        rows = cursor.fetchall()
        for row in rows:
            rel_type = row['relation'] or 'INVEST'
            amount = float(row['amount']) if row['amount'] is not None else None
            # Neo4j不支持参数化关系类型，需要用字符串格式化
            cypher = (
                f"MATCH (inv:Investor {{mysql_id: $iid}}), (ent:Enterprise {{mysql_id: $eid}}) "
                f"CREATE (inv)-[:{rel_type} {{time: $time, amount: $amount, round: $round, lead_flag: $lead}}]->(ent)"
            )
            session.run(
                cypher,
                iid=row['investor_id'], eid=row['enterprise_id'],
                time=row['time'], amount=amount, round=row['round'],
                lead=row['lead_flag']
            )
        print(f"导入 {len(rows)} 条投资关系")

    def close(self):
        self.mysql_conn.close()
        self.driver.close()


if __name__ == '__main__':
    importer = Neo4jImporter(
        mysql_config={'host': 'localhost', 'user': 'root', 'password': '123456', 'database': 'srt_kg'},
        neo4j_uri='bolt://localhost:7687', neo4j_user='neo4j', neo4j_password='password'
    )
    importer.import_all()
    importer.close()
