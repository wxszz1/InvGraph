# 融合时序特征的投融资风险知识图谱可视化系统 — 实现计划

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- []`) syntax for tracking.

**Goal:** 从零搭建一个投融资时序知识图谱可视化系统，包含数据采集、NLP实体识别/关系抽取、Neo4j图谱构建、Vue 3可视化前端、Spring Boot后端。

**架构:** 四层架构——Vue 3 前端 ↔ Spring Boot 后端 ↔ Neo4j 图数据库，Python FastAPI 提供 ML 服务（HanLP + 规则模板）。

**Tech Stack:** Vue 3, vis.js, Element Plus, Spring Boot, MyBatis, MySQL 8.0, Neo4j 5.x, Python 3.9+, FastAPI, HanLP

---

## 文件结构总览

```
project/
├── frontend/                    # 李炜：Vue 3 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── router/index.js
│   │   ├── api/index.js         # axios 封装
│   │   ├── views/
│   │   │   ├── GraphView.vue    # 图谱总览页
│   │   │   └── ExtractView.vue  # 文本抽取页
│   │   └── components/
│   │       ├── GraphNetwork.vue # vis.js 图谱组件
│   │       ├── NodeDetail.vue   # 节点详情侧边栏
│   │       ├── SearchBar.vue    # 搜索框
│   │       └── TimeFilter.vue   # 时间轴筛选
│   └── index.html
│
├── backend/                     # 潘文宝：Spring Boot 后端
│   ├── pom.xml
│   └── src/main/java/com/srt/kg/
│       ├── Application.java
│       ├── controller/
│       │   ├── GraphController.java
│       │   └── ExtractController.java
│       ├── service/
│       │   ├── GraphService.java
│       │   ├── Neo4jService.java
│       │   └── NlpClientService.java
│       ├── mapper/
│       │   ├── EnterpriseMapper.java
│       │   ├── InvestorMapper.java
│       │   └── InvestmentEventMapper.java
│       ├── entity/
│       │   ├── Enterprise.java
│       │   ├── Investor.java
│       │   ├── Industry.java
│       │   └── InvestmentEvent.java
│       └── config/
│           ├── CorsConfig.java
│           └── Neo4jConfig.java
│
├── ml-service/                  # 王翊舟：Python ML 服务
│   ├── requirements.txt
│   ├── main.py                  # FastAPI 入口
│   ├── ner/
│   │   ├── __init__.py
│   │   ├── recognizer.py        # HanLP 实体识别
│   │   └── keywords.py          # 金融领域关键词表
│   ├── relation/
│   │   ├── __init__.py
│   │   └── extractor.py         # 规则模板关系抽取
│   └── schemas.py               # Pydantic 请求/响应模型
│
├── data/                        # 邹凯城：数据
│   ├── raw/                     # 原始数据
│   ├── processed/               # 清洗后数据
│   └── scripts/
│       ├── collect.py           # 数据采集脚本
│       └── clean.py             # 数据清洗脚本
│
├── sql/
│   ├── init.sql                 # MySQL 建表脚本
│   └── seed.sql                 # 初始数据
│
└── docs/
    ├── design-doc.md
    └── plan.md
```

---

## 任务清单

### 任务1：项目初始化与环境搭建

**负责人：** 全员

**文件：**
- Create: `frontend/package.json`
- Create: `backend/pom.xml`
- Create: `ml-service/requirements.txt`
- Create: `sql/init.sql`

- [ ] **Step 1.1: 创建 Git 仓库和项目目录结构**

```bash
mkdir -p project/{frontend,backend,ml-service,data/{raw,processed,scripts},sql,docs}
cd project
git init
echo "node_modules/\n__pycache__/\n*.class\ntarget/\n.env\n.idea/" > .gitignore
git add .gitignore
git commit -m "chore: init project structure"
```

- [ ] **Step 1.2: 初始化前端项目（Vue 3 + Vite）**

```bash
cd frontend
npm create vite@latest . -- --template vue
npm install
npm install vis-network axios element-plus
```

- [ ] **Step 1.3: 创建 Spring Boot 项目骨架**

创建 `backend/pom.xml`：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.srt</groupId>
    <artifactId>kg-backend</artifactId>
    <version>1.0.0</version>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
            <version>3.0.3</version>
        </dependency>
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
        </dependency>
        <dependency>
            <groupId>org.neo4j.driver</groupId>
            <artifactId>neo4j-java-driver</artifactId>
            <version>5.15.0</version>
        </dependency>
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>fastjson</artifactId>
            <version>2.0.43</version>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 1.4: 创建 ML 服务 requirements.txt**

```
fastapi==0.109.0
uvicorn==0.27.0
hanlp==2.1.0b50
pydantic==2.5.3
```

- [ ] **Step 1.5: 创建 MySQL 建表脚本**

创建 `sql/init.sql`：
```sql
CREATE DATABASE IF NOT EXISTS srt_kg DEFAULT CHARSET utf8mb4;
USE srt_kg;

CREATE TABLE industry (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE enterprise (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    industry_id INT,
    description TEXT,
    FOREIGN KEY (industry_id) REFERENCES industry(id)
);

CREATE TABLE investor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50),
    description TEXT
);

CREATE TABLE investment_event (
    id INT PRIMARY KEY AUTO_INCREMENT,
    enterprise_id INT NOT NULL,
    investor_id INT NOT NULL,
    round VARCHAR(50),
    amount VARCHAR(100),
    event_date VARCHAR(20),
    description TEXT,
    FOREIGN KEY (enterprise_id) REFERENCES enterprise(id),
    FOREIGN KEY (investor_id) REFERENCES investor(id)
);
```

- [ ] **Step 1.6: 验证环境**

```bash
cd backend && mvn compile    # Java 编译通过
cd ../ml-service && pip install -r requirements.txt  # Python 依赖安装
cd ../frontend && npm run dev  # 前端能启动
mysql -u root -p < ../sql/init.sql  # 数据库建表成功
neo4j start  # Neo4j 能启动
```

- [ ] **Step 1.7: 提交**

```bash
git add -A
git commit -m "chore: init project with frontend, backend, ml-service, sql"
```

---

### 任务2：数据采集与清洗（邹凯城）

**文件：**
- Create: `data/scripts/collect.py`
- Create: `data/scripts/clean.py`
- Create: `data/scripts/import_mysql.py`

- [ ] **Step 2.1: 编写数据采集脚本**

创建 `data/scripts/collect.py`：
```python
"""从公开数据源采集投融资事件数据"""
import json
import os

# 示例：从已有CSV/JSON数据集加载
# 实际开发时替换为爬虫或API调用
SAMPLE_DATA = [
    {
        "enterprise": "美团",
        "investor": "IDG资本",
        "round": "A轮",
        "amount": "1000万美元",
        "date": "2017-10-19",
        "industry": "本地生活",
        "description": "IDG资本领投美团A轮融资"
    },
    {
        "enterprise": "字节跳动",
        "investor": "红杉资本",
        "round": "A轮",
        "amount": "500万美元",
        "date": "2012-03-01",
        "industry": "互联网",
        "description": "红杉资本投资字节跳动A轮"
    }
]

def collect_data():
    """采集数据并保存为JSON"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'investment_events.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_DATA, f, ensure_ascii=False, indent=2)
    print(f"已采集 {len(SAMPLE_DATA)} 条数据，保存至 {output_path}")

if __name__ == '__main__':
    collect_data()
```

- [ ] **Step 2.2: 编写数据清洗脚本**

创建 `data/scripts/clean.py`：
```python
"""数据清洗：去重、格式标准化"""
import json
import os

def clean_data(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 去重（按 enterprise+investor+round+date 去重）
    seen = set()
    cleaned = []
    for item in data:
        key = f"{item['enterprise']}|{item['investor']}|{item['round']}|{item['date']}"
        if key not in seen:
            seen.add(key)
            # 标准化日期格式
            item['date'] = item['date'].replace('/', '-')
            cleaned.append(item)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"清洗完成：{len(data)} -> {len(cleaned)} 条")

if __name__ == '__main__':
    base = os.path.join(os.path.dirname(__file__), '..')
    clean_data(
        os.path.join(base, 'raw', 'investment_events.json'),
        os.path.join(base, 'processed', 'investment_events_clean.json')
    )
```

- [ ] **Step 2.3: 编写数据导入 MySQL 脚本**

创建 `data/scripts/import_mysql.py`：
```python
"""将清洗后的数据导入MySQL"""
import json
import pymysql

def import_to_mysql(json_path, db_config):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = pymysql.connect(**db_config, charset='utf8mb4')
    cursor = conn.cursor()

    for item in data:
        # 插入行业
        cursor.execute("INSERT IGNORE INTO industry (name) VALUES (%s)", (item['industry'],))
        cursor.execute("SELECT id FROM industry WHERE name=%s", (item['industry'],))
        industry_id = cursor.fetchone()[0]

        # 插入企业
        cursor.execute(
            "INSERT INTO enterprise (name, industry_id, description) VALUES (%s, %s, %s)",
            (item['enterprise'], industry_id, item.get('description', ''))
        )
        enterprise_id = cursor.lastrowid

        # 插入投资方
        cursor.execute("INSERT INTO investor (name, type) VALUES (%s, %s)", (item['investor'], '投资机构'))
        investor_id = cursor.lastrowid

        # 插入投资事件
        cursor.execute(
            "INSERT INTO investment_event (enterprise_id, investor_id, round, amount, event_date, description) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (enterprise_id, investor_id, item['round'], item['amount'], item['date'], item['description'])
        )

    conn.commit()
    conn.close()
    print(f"已导入 {len(data)} 条投资事件")

if __name__ == '__main__':
    import_to_mysql(
        '../processed/investment_events_clean.json',
        {'host': 'localhost', 'user': 'root', 'password': 'root', 'database': 'srt_kg'}
    )
```

- [ ] **Step 2.4: 运行验证**

```bash
cd data/scripts
python collect.py      # 生成 raw/investment_events.json
python clean.py        # 生成 processed/investment_events_clean.json
python import_mysql.py # 导入MySQL
```

- [ ] **Step 2.5: 提交**

```bash
git add data/ sql/
git commit -m "feat(data): add data collection, cleaning and import scripts"
```

---

### 任务3：ML服务 — 实体识别（王翊舟）

**文件：**
- Create: `ml-service/main.py`
- Create: `ml-service/schemas.py`
- Create: `ml-service/ner/__init__.py`
- Create: `ml-service/ner/recognizer.py`
- Create: `ml-service/ner/keywords.py`

- [ ] **Step 3.1: 定义请求/响应模型**

创建 `ml-service/schemas.py`：
```python
from pydantic import BaseModel
from typing import List, Optional

class Entity(BaseModel):
    name: str
    type: str  # Enterprise, Investor, Round, Industry

class Relation(BaseModel):
    head: str
    relation: str  # INVEST, ACQUIRE, LEAD, FOLLOW
    tail: str

class Triple(BaseModel):
    head: str
    relation: str
    tail: str
    time: Optional[str] = None

class NerRequest(BaseModel):
    text: str

class NerResponse(BaseModel):
    entities: List[Entity]

class RelationRequest(BaseModel):
    text: str
    entities: List[Entity]

class RelationResponse(BaseModel):
    relations: List[Relation]

class ExtractRequest(BaseModel):
    text: str

class ExtractResponse(BaseModel):
    entities: List[Entity]
    relations: List[Relation]
    triples: List[Triple]
```

- [ ] **Step 3.2: 编写金融领域关键词表**

创建 `ml-service/ner/keywords.py`：
```python
"""金融投融资领域关键词表"""

# 融资轮次关键词
ROUND_KEYWORDS = [
    "天使轮", "种子轮", "Pre-A轮", "A轮", "A+轮",
    "B轮", "B+轮", "C轮", "D轮", "E轮", "F轮",
    "IPO", "Pre-IPO", "战略投资", "并购"
]

# 行业关键词
INDUSTRY_KEYWORDS = [
    "互联网", "人工智能", "医疗健康", "新能源", "金融科技",
    "电子商务", "本地生活", "企业服务", "教育", "游戏",
    "硬件", "汽车交通", "房产服务", "物流", "社交"
]

# 投资机构常见后缀
INVESTOR_SUFFIXES = ["资本", "基金", "投资", "创投", "风投", "VC", "PE"]

# 投资动作关键词
INVEST_KEYWORDS = ["投资", "注资", "融资", "获投", "获得"]
ACQUIRE_KEYWORDS = ["收购", "并购", "兼并", "买下"]
LEAD_KEYWORDS = ["领投", "牵头", "领投方"]
FOLLOW_KEYWORDS = ["跟投", "联合投资", "参投"]
```

- [ ] **Step 3.3: 编写 HanLP 实体识别器**

创建 `ml-service/ner/recognizer.py`：
```python
"""基于 HanLP 的实体识别"""
import hanlp
from ml_service.ner.keywords import ROUND_KEYWORDS, INDUSTRY_KEYWORDS, INVESTOR_SUFFIXES
from ml_service.schemas import Entity

class NerRecognizer:
    def __init__(self):
        # 加载 HanLP 预训练 NER 模型
        self.tokenizer = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
        self.ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_ELECTRA_SMALL_ZH)

    def recognize(self, text: str) -> list[Entity]:
        """从文本中识别实体"""
        tokens = self.tokenizer(text)
        ner_results = self.ner(tokens)

        entities = []
        seen = set()

        # 处理 HanLP NER 结果
        for item in ner_results:
            if isinstance(item, tuple) and len(item) >= 2:
                name, ner_type = item[0], item[1]
            else:
                continue

            if name in seen:
                continue
            seen.add(name)

            # 映射 HanLP 类型到项目类型
            if ner_type == 'NR':  # 人名 -> 可能是投资人
                entities.append(Entity(name=name, type='Investor'))
            elif ner_type == 'NT':  # 机构名 -> 企业或投资方
                entity_type = self._classify_org(name)
                entities.append(Entity(name=name, type=entity_type))

        # 关键词补充识别
        entities.extend(self._keyword_match(text, seen))

        return entities

    def _classify_org(self, name: str) -> str:
        """根据名称后缀判断机构类型"""
        for suffix in INVESTOR_SUFFIXES:
            if name.endswith(suffix):
                return 'Investor'
        return 'Enterprise'

    def _keyword_match(self, text: str, seen: set) -> list[Entity]:
        """通过关键词表补充识别"""
        entities = []
        for kw in ROUND_KEYWORDS:
            if kw in text and kw not in seen:
                seen.add(kw)
                entities.append(Entity(name=kw, type='Round'))
        for kw in INDUSTRY_KEYWORDS:
            if kw in text and kw not in seen:
                seen.add(kw)
                entities.append(Entity(name=kw, type='Industry'))
        return entities
```

- [ ] **Step 3.4: 编写 FastAPI 入口**

创建 `ml-service/main.py`：
```python
"""ML服务 FastAPI 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml_service.schemas import (
    NerRequest, NerResponse, RelationRequest, RelationResponse,
    ExtractRequest, ExtractResponse
)
from ml_service.ner.recognizer import NerRecognizer
from ml_service.relation.extractor import RelationExtractor

app = FastAPI(title="投融资NLP服务")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recognizer = NerRecognizer()
extractor = RelationExtractor()

@app.post("/api/ner", response_model=NerResponse)
def ner(request: NerRequest):
    entities = recognizer.recognize(request.text)
    return NerResponse(entities=entities)

@app.post("/api/relation", response_model=RelationResponse)
def relation(request: RelationRequest):
    relations = extractor.extract(request.text, request.entities)
    return RelationResponse(relations=relations)

@app.post("/api/extract", response_model=ExtractResponse)
def extract(request: ExtractRequest):
    entities = recognizer.recognize(request.text)
    relations = extractor.extract(request.text, entities)
    # 组装时序四元组
    triples = [
        {"head": r.head, "relation": r.relation, "tail": r.tail, "time": None}
        for r in relations
    ]
    return ExtractResponse(entities=entities, relations=relations, triples=triples)
```

- [ ] **Step 3.5: 测试 ML 服务**

```bash
cd ml-service
uvicorn main:app --reload --port 8000

# 测试
curl -X POST http://localhost:8000/api/ner \
  -H "Content-Type: application/json" \
  -d '{"text": "IDG资本投资美团1000万美元"}'
```

- [ ] **Step 3.6: 提交**

```bash
git add ml-service/
git commit -m "feat(ml): add NER service with HanLP and FastAPI"
```

---

### 任务4：ML服务 — 关系抽取（王翊舟）

**文件：**
- Create: `ml-service/relation/__init__.py`
- Create: `ml-service/relation/extractor.py`

- [ ] **Step 4.1: 编写规则模板关系抽取器**

创建 `ml-service/relation/extractor.py`：
```python
"""基于规则模板的关系抽取"""
import re
from ml_service.schemas import Entity, Relation
from ml_service.ner.keywords import (
    INVEST_KEYWORDS, ACQUIRE_KEYWORDS, LEAD_KEYWORDS, FOLLOW_KEYWORDS
)

class RelationExtractor:
    def __init__(self):
        self.relation_patterns = [
            (INVEST_KEYWORDS, "INVEST"),
            (ACQUIRE_KEYWORDS, "ACQUIRE"),
            (LEAD_KEYWORDS, "LEAD"),
            (FOLLOW_KEYWORDS, "FOLLOW"),
        ]

    def extract(self, text: str, entities: list[Entity]) -> list[Relation]:
        """从文本和已有实体中抽取关系"""
        relations = []
        seen = set()

        # 按实体类型分组
        investors = [e for e in entities if e.type == 'Investor']
        enterprises = [e for e in entities if e.type == 'Enterprise']

        for keywords, rel_type in self.relation_patterns:
            for kw in keywords:
                if kw not in text:
                    continue
                # 匹配模式：Investor + 关键词 + Enterprise
                for inv in investors:
                    for ent in enterprises:
                        pattern1 = f"{inv.name}.*?{kw}.*?{ent.name}"
                        pattern2 = f"{ent.name}.*?{kw}.*?{inv.name}"
                        if re.search(pattern1, text) or re.search(pattern2, text):
                            key = f"{inv.name}|{rel_type}|{ent.name}"
                            if key not in seen:
                                seen.add(key)
                                relations.append(Relation(
                                    head=inv.name,
                                    relation=rel_type,
                                    tail=ent.name
                                ))
        return relations
```

- [ ] **Step 4.2: 测试关系抽取**

```bash
cd ml-service
uvicorn main:app --reload --port 8000

curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "2022年3月，红杉资本领投字节跳动B轮融资，金额达5亿美元"}'
```

预期输出：
```json
{
  "entities": [
    {"name": "红杉资本", "type": "Investor"},
    {"name": "字节跳动", "type": "Enterprise"},
    {"name": "B轮", "type": "Round"}
  ],
  "relations": [
    {"head": "红杉资本", "relation": "LEAD", "tail": "字节跳动"}
  ],
  "triples": [
    {"head": "红杉资本", "relation": "LEAD", "tail": "字节跳动", "time": null}
  ]
}
```

- [ ] **Step 4.3: 提交**

```bash
git add ml-service/relation/
git commit -m "feat(ml): add rule-based relation extraction"
```

---

### 任务5：Neo4j 图谱构建（潘文宝 + 邹凯城）

**文件：**
- Create: `data/scripts/import_neo4j.py`

- [ ] **Step 5.1: 编写 MySQL→Neo4j 数据导入脚本**

创建 `data/scripts/import_neo4j.py`：
```python
"""从MySQL导入数据到Neo4j图数据库"""
import pymysql
from neo4j import GraphDatabase

class Neo4jImporter:
    def __init__(self, mysql_config, neo4j_uri, neo4j_user, neo4j_password):
        self.mysql_conn = pymysql.connect(**mysql_config, charset='utf8mb4')
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def import_all(self):
        """导入全部数据到Neo4j"""
        with self.driver.session() as session:
            # 清空图谱
            session.run("MATCH (n) DETACH DELETE n")

            self._import_industries(session)
            self._import_enterprises(session)
            self._import_investors(session)
            self._import_events(session)

        print("数据导入Neo4j完成")

    def _import_industries(self, session):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT id, name FROM industry")
        for row in cursor.fetchall():
            session.run(
                "CREATE (i:Industry {mysql_id: $id, name: $name})",
                id=row[0], name=row[1]
            )
        print(f"导入 {cursor.rowcount} 个行业节点")

    def _import_enterprises(self, session):
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT e.id, e.name, e.description, i.name as industry_name
            FROM enterprise e LEFT JOIN industry i ON e.industry_id = i.id
        """)
        for row in cursor.fetchall():
            session.run(
                "CREATE (e:Enterprise {mysql_id: $id, name: $name, description: $desc})",
                id=row['id'], name=row['name'], desc=row['description'] or ''
            )
            if row['industry_name']:
                session.run(
                    "MATCH (e:Enterprise {mysql_id: $eid}), (i:Industry {name: $iname}) "
                    "CREATE (e)-[:BELONGS_TO]->(i)",
                    eid=row['id'], iname=row['industry_name']
                )

    def _import_investors(self, session):
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, name, type, description FROM investor")
        for row in cursor.fetchall():
            session.run(
                "CREATE (i:Investor {mysql_id: $id, name: $name, type: $type, description: $desc})",
                id=row['id'], name=row['name'], type=row['type'] or '', desc=row['description'] or ''
            )

    def _import_events(self, session):
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT ev.enterprise_id, ev.investor_id, ev.round, ev.amount,
                   ev.event_date, ev.description,
                   e.name as enterprise_name, i.name as investor_name
            FROM investment_event ev
            JOIN enterprise e ON ev.enterprise_id = e.id
            JOIN investor i ON ev.investor_id = i.id
        """)
        for row in cursor.fetchall():
            # 创建 INVEST 关系（带时序属性）
            session.run(
                "MATCH (inv:Investor {mysql_id: $iid}), (ent:Enterprise {mysql_id: $eid}) "
                "CREATE (inv)-[:INVEST {time: $time, amount: $amount, round: $round}]->(ent)",
                iid=row['investor_id'], eid=row['enterprise_id'],
                time=row['event_date'], amount=row['amount'], round=row['round']
            )

    def close(self):
        self.mysql_conn.close()
        self.driver.close()

if __name__ == '__main__':
    importer = Neo4jImporter(
        mysql_config={'host': 'localhost', 'user': 'root', 'password': 'root', 'database': 'srt_kg'},
        neo4j_uri='bolt://localhost:7687',
        neo4j_user='neo4j',
        neo4j_password='password'
    )
    importer.import_all()
    importer.close()
```

- [ ] **Step 5.2: 运行并验证**

```bash
python data/scripts/import_neo4j.py
# 打开 Neo4j Browser (http://localhost:7474)
# 执行 MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 50 验证图谱
```

- [ ] **Step 5.3: 提交**

```bash
git add data/scripts/import_neo4j.py
git commit -m "feat(kg): add MySQL to Neo4j import script"
```

---

### 任务6：Spring Boot 后端 API（潘文宝）

**文件：**
- Create: `backend/src/main/java/com/srt/kg/Application.java`
- Create: `backend/src/main/java/com/srt/kg/config/CorsConfig.java`
- Create: `backend/src/main/java/com/srt/kg/config/Neo4jConfig.java`
- Create: `backend/src/main/java/com/srt/kg/entity/Enterprise.java`
- Create: `backend/src/main/java/com/srt/kg/entity/Investor.java`
- Create: `backend/src/main/java/com/srt/kg/entity/Industry.java`
- Create: `backend/src/main/java/com/srt/kg/entity/InvestmentEvent.java`
- Create: `backend/src/main/java/com/srt/kg/mapper/EnterpriseMapper.java`
- Create: `backend/src/main/java/com/srt/kg/mapper/InvestorMapper.java`
- Create: `backend/src/main/java/com/srt/kg/mapper/InvestmentEventMapper.java`
- Create: `backend/src/main/java/com/srt/kg/service/Neo4jService.java`
- Create: `backend/src/main/java/com/srt/kg/service/NlpClientService.java`
- Create: `backend/src/main/java/com/srt/kg/service/GraphService.java`
- Create: `backend/src/main/java/com/srt/kg/controller/GraphController.java`
- Create: `backend/src/main/java/com/srt/kg/controller/ExtractController.java`
- Create: `backend/src/main/resources/application.yml`
- Create: `backend/src/main/resources/mapper/EnterpriseMapper.xml`

- [ ] **Step 6.1: 创建启动类和配置**

`backend/src/main/java/com/srt/kg/Application.java`：
```java
package com.srt.kg;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

`backend/src/main/resources/application.yml`：
```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/srt_kg?useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: root
    driver-class-name: com.mysql.cj.jdbc.Driver

mybatis:
  mapper-locations: classpath:mapper/*.xml

neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  password: password

nlp:
  service:
    url: http://localhost:8000
```

`backend/src/main/java/com/srt/kg/config/CorsConfig.java`：
```java
package com.srt.kg.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class CorsConfig {
    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.addAllowedOrigin("*");
        config.addAllowedMethod("*");
        config.addAllowedHeader("*");
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}
```

- [ ] **Step 6.2: 创建实体类**

`backend/src/main/java/com/srt/kg/entity/Enterprise.java`：
```java
package com.srt.kg.entity;

public class Enterprise {
    private Integer id;
    private String name;
    private Integer industryId;
    private String description;

    // getters and setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Integer getIndustryId() { return industryId; }
    public void setIndustryId(Integer industryId) { this.industryId = industryId; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
```

（Investor、Industry、InvestmentEvent 实体类类似，按设计文档字段定义）

- [ ] **Step 6.3: 创建 Neo4j 服务**

`backend/src/main/java/com/srt/kg/service/Neo4jService.java`：
```java
package com.srt.kg.service;

import org.neo4j.driver.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.util.*;

@Service
public class Neo4jService {

    @Value("${neo4j.uri}")
    private String uri;
    @Value("${neo4j.username}")
    private String username;
    @Value("${neo4j.password}")
    private String password;

    private Driver driver;

    @PostConstruct
    public void init() {
        driver = GraphDatabase.driver(uri, AuthTokens.basic(username, password));
    }

    @PreDestroy
    public void close() {
        if (driver != null) driver.close();
    }

    /** 获取全图谱数据（nodes + edges 格式供 vis.js 使用）*/
    public Map<String, Object> getAllGraph() {
        try (Session session = driver.session()) {
            String cypher = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 500";
            Result result = session.run(cypher);

            Set<String> nodeIds = new LinkedHashSet<>();
            List<Map<String, Object>> nodes = new ArrayList<>();
            List<Map<String, Object>> edges = new ArrayList<>();

            while (result.hasNext()) {
                Record record = result.next();
                org.neo4j.driver.types.Node n = record.get("n").asNode();
                org.neo4j.driver.types.Node m = record.get("m").asNode();
                org.neo4j.driver.types.Relationship r = record.get("r").asRelationship();

                addNode(nodes, nodeIds, n);
                addNode(nodes, nodeIds, m);
                addEdge(edges, r, n, m);
            }

            Map<String, Object> graph = new HashMap<>();
            graph.put("nodes", nodes);
            graph.put("edges", edges);
            return graph;
        }
    }

    /** 按名称搜索节点 */
    public Map<String, Object> searchNode(String keyword) {
        try (Session session = driver.session()) {
            String cypher = "MATCH (n) WHERE n.name CONTAINS $keyword RETURN n LIMIT 20";
            Result result = session.run(cypher, Map.of("keyword", keyword));

            List<Map<String, Object>> nodes = new ArrayList<>();
            while (result.hasNext()) {
                Record record = result.next();
                org.neo4j.driver.types.Node n = record.get("n").asNode();
                Map<String, Object> node = new HashMap<>();
                node.put("id", String.valueOf(n.id()));
                node.put("label", n.labels().iterator().next());
                node.put("properties", n.asMap());
                nodes.add(node);
            }

            Map<String, Object> data = new HashMap<>();
            data.put("nodes", nodes);
            return data;
        }
    }

    /** 按时间范围筛选 */
    public Map<String, Object> filterByTime(String startTime, String endTime, String industry) {
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

            cypher.append("RETURN i, r, e LIMIT 200");
            Result result = session.run(cypher.toString(), params);

            Set<String> nodeIds = new LinkedHashSet<>();
            List<Map<String, Object>> nodes = new ArrayList<>();
            List<Map<String, Object>> edges = new ArrayList<>();

            while (result.hasNext()) {
                Record record = result.next();
                org.neo4j.driver.types.Node n = record.get("i").asNode();
                org.neo4j.driver.types.Node m = record.get("e").asNode();
                org.neo4j.driver.types.Relationship r = record.get("r").asRelationship();

                addNode(nodes, nodeIds, n);
                addNode(nodes, nodeIds, m);
                addEdge(edges, r, n, m);
            }

            Map<String, Object> graph = new HashMap<>();
            graph.put("nodes", nodes);
            graph.put("edges", edges);
            return graph;
        }
    }

    /** 导入NLP抽取的三元组到Neo4j */
    public void importTriples(JSONArray triples) {
        try (Session session = driver.session()) {
            for (int i = 0; i < triples.size(); i++) {
                JSONObject triple = triples.getJSONObject(i);
                String head = triple.getString("head");
                String relation = triple.getString("relation");
                String tail = triple.getString("tail");
                String time = triple.getString("time");

                // 根据关系类型创建不同节点
                String headLabel = "Investor";
                String tailLabel = "Enterprise";

                String cypher = "MERGE (h:" + headLabel + " {name: $head}) "
                    + "MERGE (t:" + tailLabel + " {name: $tail}) "
                    + "MERGE (h)-[:" + relation + " {time: $time}]->(t)";
                session.run(cypher, Map.of("head", head, "tail", tail, "time", time != null ? time : ""));
            }
        }
    }

    /** 获取图谱统计信息 */
    public Map<String, Object> getStatistics() {
        try (Session session = driver.session()) {
            Map<String, Object> stats = new HashMap<>();
            stats.put("enterpriseCount",
                session.run("MATCH (n:Enterprise) RETURN count(n) as c").single().get("c").asInt());
            stats.put("investorCount",
                session.run("MATCH (n:Investor) RETURN count(n) as c").single().get("c").asInt());
            stats.put("relationCount",
                session.run("MATCH ()-[r]->() RETURN count(r) as c").single().get("c").asInt());
            return stats;
        }
    }

    private void addNode(List<Map<String, Object>> nodes, Set<String> nodeIds, org.neo4j.driver.types.Node node) {
        String id = String.valueOf(node.id());
        if (nodeIds.add(id)) {
            Map<String, Object> n = new HashMap<>();
            n.put("id", id);
            n.put("label", node.labels().iterator().next());
            n.put("properties", node.asMap());
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
        edge.put("properties", rel.asMap());
        edges.add(edge);
    }
}
```

- [ ] **Step 6.4: 创建 NLP 调用服务**

`backend/src/main/java/com/srt/kg/service/NlpClientService.java`：
```java
package com.srt.kg.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.alibaba.fastjson.JSONObject;

@Service
public class NlpClientService {

    @Value("${nlp.service.url}")
    private String nlpUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public JSONObject extractEntitiesAndRelations(String text) {
        JSONObject request = new JSONObject();
        request.put("text", text);
        String response = restTemplate.postForObject(nlpUrl + "/api/extract", request, String.class);
        return JSONObject.parseObject(response);
    }
}
```

- [ ] **Step 6.5: 创建控制器**

`backend/src/main/java/com/srt/kg/controller/GraphController.java`：
```java
package com.srt.kg.controller;

import com.srt.kg.service.Neo4jService;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class GraphController {

    @Autowired
    private Neo4jService neo4jService;

    @GetMapping("/graph/all")
    public Map<String, Object> getAllGraph() {
        return neo4jService.getAllGraph();
    }

    @GetMapping("/graph/search")
    public Map<String, Object> search(@RequestParam String keyword) {
        return neo4jService.searchNode(keyword);
    }

    @GetMapping("/graph/filter")
    public Map<String, Object> filter(
            @RequestParam String startTime,
            @RequestParam String endTime,
            @RequestParam(required = false) String industry) {
        return neo4jService.filterByTime(startTime, endTime, industry);
    }

    @PostMapping("/import")
    public Map<String, Object> importTriples(@RequestBody JSONObject body) {
        JSONArray triples = body.getJSONArray("triples");
        neo4jService.importTriples(triples);
        return Map.of("code", 200, "msg", "导入成功", "data", Map.of("count", triples.size()));
    }

    @GetMapping("/statistics")
    public Map<String, Object> statistics() {
        return Map.of("code", 200, "msg", "success", "data", neo4jService.getStatistics());
    }
}
```

`backend/src/main/java/com/srt/kg/controller/ExtractController.java`：
```java
package com.srt.kg.controller;

import com.srt.kg.service.NlpClientService;
import com.alibaba.fastjson.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ExtractController {

    @Autowired
    private NlpClientService nlpClientService;

    @PostMapping("/extract")
    public Map<String, Object> extract(@RequestBody JSONObject body) {
        String text = body.getString("text");
        JSONObject result = nlpClientService.extractEntitiesAndRelations(text);
        return Map.of("code", 200, "msg", "success", "data", result);
    }
}
```

- [ ] **Step 6.6: 验证后端**

```bash
cd backend
mvn spring-boot:run

# 测试接口
curl http://localhost:8080/api/graph/all
curl http://localhost:8080/api/statistics
curl -X POST http://localhost:8080/api/extract -H "Content-Type: application/json" -d '{"text": "红杉资本投资美团"}'
```

- [ ] **Step 6.7: 提交**

```bash
git add backend/
git commit -m "feat(backend): add Spring Boot API for graph CRUD and NLP integration"
```

---

### 任务7：前端图谱可视化（李炜）

**文件：**
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/views/GraphView.vue`
- Create: `frontend/src/views/ExtractView.vue`
- Create: `frontend/src/components/GraphNetwork.vue`
- Create: `frontend/src/components/NodeDetail.vue`
- Create: `frontend/src/components/SearchBar.vue`
- Create: `frontend/src/components/TimeFilter.vue`

- [ ] **Step 7.1: 配置路由和 API 封装**

`frontend/src/router/index.js`：
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import GraphView from '../views/GraphView.vue'
import ExtractView from '../views/ExtractView.vue'

const routes = [
  { path: '/', name: 'graph', component: GraphView },
  { path: '/extract', name: 'extract', component: ExtractView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

`frontend/src/api/index.js`：
```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8080/api',
  timeout: 10000
})

export default {
  getGraph: () => api.get('/graph/all'),
  searchNode: (keyword) => api.get('/graph/search', { params: { keyword } }),
  filterGraph: (startTime, endTime, industry) =>
    api.get('/graph/filter', { params: { startTime, endTime, industry } }),
  extract: (text) => api.post('/extract', { text }),
  importTriples: (triples) => api.post('/import', { triples }),
  getStatistics: () => api.get('/statistics')
}
```

- [ ] **Step 7.2: 创建 vis.js 图谱组件**

`frontend/src/components/GraphNetwork.vue`：
```vue
<template>
  <div ref="container" class="graph-container"></div>
</template>

<script>
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'

export default {
  name: 'GraphNetwork',
  props: {
    nodes: { type: Array, default: () => [] },
    edges: { type: Array, default: () => [] }
  },
  data() {
    return { network: null }
  },
  watch: {
    nodes: 'renderGraph',
    edges: 'renderGraph'
  },
  mounted() {
    this.renderGraph()
  },
  methods: {
    renderGraph() {
      const nodeColors = {
        Enterprise: '#409EFF',
        Investor: '#67C23A',
        Industry: '#E6A23C',
        Round: '#909399'
      }

      const visNodes = new DataSet(
        this.nodes.map(n => ({
          id: n.id,
          label: n.properties?.name || n.id,
          color: nodeColors[n.label] || '#909399',
          shape: n.label === 'Round' ? 'dot' : 'dot',
          size: n.label === 'Round' ? 10 : 20,
          font: { color: '#333' }
        }))
      )

      const visEdges = new DataSet(
        this.edges.map(e => ({
          id: e.id,
          from: e.from,
          to: e.to,
          label: e.properties?.amount || e.label,
          arrows: 'to',
          font: { size: 10, color: '#666' },
          color: { color: '#999' }
        }))
      )

      const options = {
        physics: { solver: 'forceAtlas2Based', stabilization: { iterations: 100 } },
        interaction: { hover: true, tooltipDelay: 200 },
        nodes: { font: { size: 14 } },
        edges: { smooth: { type: 'continuous' } }
      }

      if (this.network) this.network.destroy()
      this.network = new Network(this.$refs.container, { nodes: visNodes, edges: visEdges }, options)

      this.network.on('click', (params) => {
        if (params.nodes.length > 0) {
          this.$emit('node-click', params.nodes[0])
        }
      })
    }
  },
  beforeUnmount() {
    if (this.network) this.network.destroy()
  }
}
</script>

<style scoped>
.graph-container { width: 100%; height: 100%; min-height: 500px; }
</style>
```

- [ ] **Step 7.3: 创建图谱总览页**

`frontend/src/views/GraphView.vue`：
```vue
<template>
  <div class="graph-view">
    <div class="toolbar">
      <SearchBar @search="handleSearch" />
      <TimeFilter @filter="handleFilter" />
      <router-link to="/extract" class="btn-extract">文本抽取</router-link>
    </div>
    <div class="main-content">
      <GraphNetwork
        :nodes="graphData.nodes"
        :edges="graphData.edges"
        @node-click="showNodeDetail"
      />
      <NodeDetail v-if="selectedNode" :node="selectedNode" @close="selectedNode = null" />
    </div>
  </div>
</template>

<script>
import api from '../api'
import GraphNetwork from '../components/GraphNetwork.vue'
import NodeDetail from '../components/NodeDetail.vue'
import SearchBar from '../components/SearchBar.vue'
import TimeFilter from '../components/TimeFilter.vue'

export default {
  components: { GraphNetwork, NodeDetail, SearchBar, TimeFilter },
  data() {
    return {
      graphData: { nodes: [], edges: [] },
      selectedNode: null
    }
  },
  async mounted() {
    await this.loadGraph()
  },
  methods: {
    async loadGraph() {
      const res = await api.getGraph()
      this.graphData = res.data.data
    },
    async handleSearch(keyword) {
      const res = await api.searchNode(keyword)
      this.graphData = res.data.data
    },
    async handleFilter(startTime, endTime, industry) {
      const res = await api.filterGraph(startTime, endTime, industry)
      this.graphData = res.data.data
    },
    showNodeDetail(nodeId) {
      const node = this.graphData.nodes.find(n => n.id === nodeId)
      this.selectedNode = node
    }
  }
}
</script>
```

- [ ] **Step 7.4: 创建搜索框、时间筛选、节点详情组件**

`frontend/src/components/SearchBar.vue`：
```vue
<template>
  <div class="search-bar">
    <input v-model="keyword" placeholder="搜索企业或投资方..." @keyup.enter="search" />
    <button @click="search">搜索</button>
  </div>
</template>
<script>
export default {
  data() { return { keyword: '' } },
  methods: {
    search() { if (this.keyword.trim()) this.$emit('search', this.keyword.trim()) }
  }
}
</script>
```

`frontend/src/components/TimeFilter.vue`：
```vue
<template>
  <div class="time-filter">
    <input type="month" v-model="startTime" />
    <span>至</span>
    <input type="month" v-model="endTime" />
    <button @click="filter">筛选</button>
    <button @click="reset">重置</button>
  </div>
</template>
<script>
export default {
  data() { return { startTime: '2015-01', endTime: '2025-12' } },
  methods: {
    filter() { this.$emit('filter', this.startTime, this.endTime, null) },
    reset() {
      this.startTime = '2015-01'; this.endTime = '2025-12'
      this.$emit('filter', this.startTime, this.endTime, null)
    }
  }
}
</script>
```

`frontend/src/components/NodeDetail.vue`：
```vue
<template>
  <div class="node-detail">
    <button class="close" @click="$emit('close')">X</button>
    <h3>{{ node?.properties?.name || '节点详情' }}</h3>
    <p>类型：{{ node?.label }}</p>
    <div v-if="node?.properties">
      <p v-for="(val, key) in node.properties" :key="key">{{ key }}: {{ val }}</p>
    </div>
  </div>
</template>
<script>
export default {
  props: { node: Object }
}
</script>
```

- [ ] **Step 7.5: 创建文本抽取页**

`frontend/src/views/ExtractView.vue`：
```vue
<template>
  <div class="extract-view">
    <h2>文本抽取</h2>
    <router-link to="/">返回图谱</router-link>
    <textarea v-model="inputText" placeholder="输入投融资新闻文本..." rows="6"></textarea>
    <button @click="doExtract" :disabled="loading">{{ loading ? '抽取中...' : '开始抽取' }}</button>

    <div v-if="result" class="result">
      <h3>实体</h3>
      <ul>
        <li v-for="(e, i) in result.entities" :key="i">
          {{ e.name }} ({{ e.type }})
        </li>
      </ul>
      <h3>关系</h3>
      <ul>
        <li v-for="(r, i) in result.relations" :key="i">
          {{ r.head }} --[{{ r.relation}}]--> {{ r.tail }}
        </li>
      </ul>
      <button @click="importToGraph" :disabled="importing">
        {{ importing ? '导入中...' : '导入图谱' }}
      </button>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  data() {
    return {
      inputText: '',
      result: null,
      loading: false,
      importing: false
    }
  },
  methods: {
    async doExtract() {
      this.loading = true
      try {
        const res = await api.extract(this.inputText)
        this.result = res.data.data
      } finally {
        this.loading = false
      }
    },
    async importToGraph() {
      if (!this.result?.triples?.length) return
      this.importing = true
      try {
        await api.importTriples(this.result.triples)
        alert('导入成功！')
      } finally {
        this.importing = false
      }
    }
  }
}
</script>
```

- [ ] **Step 7.6: 更新 App.vue 和 main.js**

`frontend/src/main.js`：
```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
```

`frontend/src/App.vue`：
```vue
<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
#app { font-family: 'Microsoft YaHei', sans-serif; }
.toolbar { display: flex; gap: 10px; padding: 10px; background: #f5f5f5; align-items: center; }
.main-content { display: flex; height: calc(100vh - 60px); }
.graph-container { flex: 1; }
.node-detail { width: 300px; padding: 16px; border-left: 1px solid #eee; overflow-y: auto; }
.close { float: right; cursor: pointer; }
.btn-extract { padding: 6px 12px; background: #409EFF; color: white; text-decoration: none; border-radius: 4px; }
.extract-view { max-width: 800px; margin: 20px auto; padding: 20px; }
.extract-view textarea { width: 100%; padding: 10px; font-size: 14px; }
.extract-view button { margin-top: 10px; padding: 8px 16px; }
.extract-view .result { margin-top: 20px; }
.search-bar input { padding: 6px 10px; width: 200px; }
.search-bar button, .time-filter button { padding: 6px 12px; cursor: pointer; }
.time-filter { display: flex; align-items: center; gap: 8px; }
</style>
```

- [ ] **Step 7.7: 验证前端**

```bash
cd frontend
npm run dev
# 浏览器打开 http://localhost:5173
# 验证：图谱展示、搜索、筛选、点击节点、文本抽取
```

- [ ] **Step 7.8: 提交**

```bash
git add frontend/
git commit -m "feat(frontend): add graph visualization with vis.js, search, filter and extract pages"
```

---

### 任务8：系统集成与联调（文子昂）

- [ ] **Step 8.1: 启动全部服务**

终端1：
```bash
cd ml-service && uvicorn main:app --reload --port 8000
```

终端2：
```bash
cd backend && mvn spring-boot:run
```

终端3：
```bash
cd frontend && npm run dev
```

确保 Neo4j 和 MySQL 已启动。

- [ ] **Step 8.2: 端到端测试**

1. 打开前端首页，验证图谱正常展示
2. 搜索"美团"，验证搜索功能
3. 选择时间范围 2017-01 到 2017-12，验证筛选
4. 进入文本抽取页，输入"2022年红杉资本领投字节跳动C轮融资5亿美元"
5. 点击"开始抽取"，验证实体和关系识别结果
6. 点击"导入图谱"，返回首页验证新增节点
7. 点击节点，验证侧边栏显示详情

- [ ] **Step 8.3: 修复联调中发现的问题**

（具体问题根据实际测试结果修复）

- [ ] **Step 8.4: 提交**

```bash
git add -A
git commit -m "fix: resolve integration issues found during e2e testing"
```

---

### 任务9：验收准备（文子昂）

- [ ] **Step 9.1: 补充测试数据**

使用采集脚本扩充数据量至 500+ 企业、1000+ 事件。

- [ ] **Step 9.2: 撰写研究报告**

按 SRT 要求撰写研究报告，包含：
- 研究背景与意义
- 技术方案
- 系统实现
- 测试结果
- 总结与展望

- [ ] **Step 9.3: 编写 README 和部署文档**

创建项目根目录 `README.md`，包含：
- 项目简介
- 技术栈
- 环境要求
- 安装步骤
- 运行方法
- 系统截图

- [ ] **Step 9.4: 准备演示 Demo**

准备演示数据和操作脚本，确保演示流程顺畅：
1. 展示图谱总览
2. 搜索和筛选
3. 文本抽取 → 自动建图
4. 点击节点查看详情

- [ ] **Step 9.5: 最终提交**

```bash
git add -A
git commit -m "docs: add README, deployment guide, and demo preparation"
```
