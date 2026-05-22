# 融合时序特征的投融资风险知识图谱可视化系统 — 设计文档

> 基于张华《基于时序知识图谱的投资决策研究与实现》论文，SRT大学生研究训练计划项目
> 技术栈：Vue 3 + Java (Spring Boot) + Python (FastAPI) + Neo4j + HanLP
> 团队：5人，周期8周

---

## 1. 项目概述

本项目构建一个融合时序特征的投融资知识图谱可视化系统，核心功能：
- 从投融资领域文本/结构化数据中抽取实体和关系
- 构建带时间属性的知识图谱
- 通过可视化界面展示投融资关系网络和时序演化

核心创新点：**时序四元组**（主体-关系-客体-时间），支持按时间维度分析投融资关系。

## 2. 系统架构

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│  Vue 3 前端  │◄──►│  Spring Boot API  │◄──►│  Neo4j 图库  │
│  vis.js      │    │  Java            │    │  时序知识图谱  │
└─────────────┘    └────────┬─────────┘    └─────────────┘
                            │ REST
                            ▼
                     ┌──────────────────┐
                     │  FastAPI ML服务   │
                     │  HanLP + 规则     │
                     └──────────────────┘

数据流：前端 ↔ Spring Boot ↔ Neo4j（读写图谱）
       前端 → Spring Boot → FastAPI（调用NLP服务）
       Spring Boot → Neo4j（将NLP结果写入图谱）
```

### 技术选型

| 层级 | 技术 | 负责人 |
|------|------|--------|
| 前端 | Vue 3 + vis.js + Element Plus | 李炜 |
| 后端 | Spring Boot + MyBatis | 潘文宝 |
| ML服务 | Python + FastAPI + HanLP | 王翊舟 |
| 图数据库 | Neo4j Community Edition | 潘文宝 |
| 关系数据库 | MySQL 8.0 | 潘文宝 |
| 数据采集 | Python (requests/爬虫) | 邹凯城 |

## 3. 模块详细设计

### 3.1 数据层（邹凯城）

**数据源**：
- IT桔子/鲸准 API（投融资事件数据）
- 张华论文 IFTKG 数据集（基础数据集补充）
- 公开财经新闻/企业公告

**数据字段标准**：
```json
{
  "enterprise": "美团",
  "investor": "IDG资本",
  "round": "A轮",
  "amount": "1000万美元",
  "date": "2017-10-19",
  "industry": "本地生活",
  "description": "IDG资本领投美团A轮融资"
}
```

**MySQL 表结构**：
- `enterprise` (id, name, industry_id, description)
- `investor` (id, name, type, description)
- `industry` (id, name)
- `investment_event` (id, enterprise_id, investor_id, round, amount, event_date, description)

### 3.2 NLP模型（王翊舟）

**实体识别**：
- 使用 HanLP 预训练 NER 模型
- 自定义实体类型：Enterprise（企业）、Investor（投资机构）、Round（融资轮次）、Industry（行业）
- 预训练覆盖：PER、ORG、LOC 等通用类型
- 领域扩展：通过关键词表+正则补充金融领域实体

**关系抽取**：
- 基于规则模板的方法
- 关系类型：
  - INVEST（投资）："投资""注资""融资""获投"
  - ACQUIRE（并购）："收购""并购""兼并"
  - LEAD（领投）："领投""牵头"
  - FOLLOW（跟投）："跟投""联合投资"
- 模板示例：`{Investor} + 关键词 + {Enterprise}` 匹配投资关系

**FastAPI 接口**：
```
POST /api/ner
Request: {"text": "IDG资本投资美团1000万美元"}
Response: {"entities": [{"name": "IDG资本", "type": "Investor"}, {"name": "美团", "type": "Enterprise"}]}

POST /api/relation
Request: {"text": "IDG资本投资美团1000万美元", "entities": [...]}
Response: {"relations": [{"head": "IDG资本", "relation": "INVEST", "tail": "美团"}]}

POST /api/extract
Request: {"text": "IDG资本投资美团1000万美元"}
Response: {"entities": [...], "relations": [...], "triples": [{"head": "IDG资本", "relation": "INVEST", "tail": "美团", "time": "2017-10"}]}
```

> /api/ner 负责实体识别，/api/relation 负责关系抽取，/api/extract 是一站式调用（先识别再抽取，返回完整结果）。

### 3.3 知识图谱（潘文宝 + 邹凯城）

**Neo4j 节点类型**：
```cypher
// 企业节点
(:Enterprise {name, description})

// 投资方节点
(:Investor {name, type, description})

// 融资轮次节点（每轮次为独立实例，关联具体企业）
(:Round {id, round_name, time, amount})

// 行业节点
(:Industry {name})
```

**Neo4j 关系类型**（带时间属性）：
```cypher
// 投资关系
(:Investor)-[:INVEST {time, amount, round}]->(:Enterprise)

// 并购关系
(:Investor)-[:ACQUIRE {time, amount}]->(:Enterprise)

// 所属行业
(:Enterprise)-[:BELONGS_TO]->(:Industry)

// 领投（指向具体融资轮次事件）
(:Investor)-[:LEADS {time}]->(:Round)<-[:HAS_ROUND {time, amount}]-(:Enterprise)

// 跟投
(:Investor)-[:FOLLOWS {time}]->(:Round)<-[:HAS_ROUND {time, amount}]-(:Enterprise)
```

> 说明：LEADS/FOLLOWS 通过 Round 节点关联，与 INVEST 关系互补。INVEST 表示"谁投了谁"，LEADS/FOLLOWS 表示"在同一轮融资中的角色"。

**时间字段规范**：统一使用字符串格式 `"YYYY-MM"` 存储，便于前缀匹配查询。如需精确到日则用 `"YYYY-MM-DD"`。

**时序查询示例**：
```cypher
// 查询2022年所有投资关系
MATCH (i:Investor)-[r:INVEST]->(e:Enterprise)
WHERE r.time STARTS WITH '2022'
RETURN i, r, e

// 查询某企业的投资历史
MATCH (i:Investor)-[r:INVEST]->(e:Enterprise {name: '美团'})
RETURN i.name, r.time, r.amount, r.round
ORDER BY r.time
```

### 3.4 后端API（潘文宝）

**Spring Boot 接口清单**：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/graph/all` | GET | 获取全图谱数据 |
| `/api/graph/node/{id}` | GET | 获取节点详情及关联关系 |
| `/api/graph/search` | GET | 按名称搜索节点 |
| `/api/graph/filter` | GET | 按时间范围/行业筛选，参数：`startTime`, `endTime`, `industry` |
| `/api/extract` | POST | 调用ML服务抽取实体关系，参数：`text` |
| `/api/import` | POST | 将NLP抽取结果导入Neo4j，参数：`triples` (JSON数组) |
| `/api/import/batch` | POST | 批量从MySQL导入全部数据到Neo4j |
| `/api/statistics` | GET | 图谱统计信息，返回：节点数、关系数、行业分布 |

### 3.5 前端可视化（李炜）

**页面结构**：

```
├── 首页（图谱总览）
│   ├── 力导向图（vis.js Network）
│   ├── 左侧：节点类型筛选面板
│   ├── 右侧：时间轴筛选滑块
│   └── 顶部：搜索框
│
├── 节点详情页（弹窗/侧边栏）
│   ├── 节点属性卡片
│   └── 关联关系列表
│
└── 文本抽取页
    ├── 输入文本框
    ├── 抽取结果展示（实体+关系）
    └── 一键导入图谱按钮
```

**vis.js 配置要点**：
- 节点按类型着色（企业=蓝色，投资方=绿色，行业=橙色，融资轮次=灰色小节点）
- 边带箭头表示投资方向
- 边标签显示投资金额和时间
- 支持点击节点展开侧边栏详情，双击聚焦居中
- 时间轴拖拽筛选实时更新图谱

### 3.6 系统集成（文子昂协调）

**端到端流程**：
1. 用户在"文本抽取页"输入投融资新闻文本
2. 前端调用后端 `/api/extract` 接口
3. 后端转发到 Python ML 服务进行实体识别+关系抽取
4. ML 服务返回时序四元组
5. 用户确认后点击"导入图谱"
6. 后端将四元组写入 Neo4j
7. 前端图谱自动刷新，展示新增节点和关系

## 4. 时间规划（8周）

| 周次 | 阶段 | 邹凯城 | 王翊舟 | 潘文宝 | 李炜 | 文子昂 |
|------|------|--------|--------|--------|------|--------|
| 1 | 启动 | 数据源调研 | HanLP环境搭建+测试 | Neo4j部署 | Vue框架搭建 | 技术选型、Git仓库 |
| 2 | 数据 | 数据采集+清洗 | 实体类型定义+关键词表 | MySQL建表+CRUD | 页面布局+路由 | 接口文档规范 |
| 3 | 开发 | 数据导入MySQL | 实体识别Pipeline | 数据接口API | 图谱总览页(v1) | 协调联调 |
| 4 | 开发 | 人工标注+校验数据 | 关系抽取规则模板 | Neo4j批量导入脚本 | 节点详情侧边栏 | 接口联调 |
| 5 | 核心 | 数据量扩充 | 模型API封装(FastAPI) | 后端API全部接口 | 时序筛选+搜索 | 前后端对接 |
| 6 | 集成 | 数据维护+补充 | ML服务集成+联调 | 图谱查询优化 | 文本抽取页 | 端到端联调 |
| 7 | 完善 | 数据完善+文档 | 模型调优+测试 | 部署+API完善 | 整体UI美化 | 测试修复 |
| 8 | 验收 | 数据归档 | 模型文档 | 部署文档 | 演示Demo | 研究报告 |

## 5. 开发规范

- **版本控制**：Git + GitHub/Gitee，按模块分分支（feature/data, feature/nlp, feature/kg, feature/frontend）
- **接口格式**：统一 JSON 响应，`{"code": 200, "msg": "success", "data": {...}}`
- **错误处理**：接口超时返回 500 + 错误信息，NLP 服务异常时后端返回降级提示
- **跨域**：Spring Boot 配置 CORS，FastAPI 配置 CORS
- **开发环境统一**：
  - Python 3.9+，Java 17，Node.js 18+
  - Neo4j 5.x Community Edition
  - MySQL 8.0
- **部署**：开发阶段各自本地部署；验收阶段准备一台服务器统一部署（或用 Docker）

## 6. 验收标准

- 图谱包含 **500+ 企业节点、200+ 投资方节点、1000+ 投资事件**
- 实体识别准确率 **≥ 80%**，关系抽取准确率 **≥ 70%**
- 可视化页面支持：图谱展示、节点筛选、时序查询、搜索
- 支持端到端流程：输入文本 → NLP抽取 → 自动建图 → 可视化
- 系统可本地部署运行

## 7. 预期成果

1. **投融资时序知识图谱可视化系统**（可运行的Web应用）
2. **研究报告**（SRT验收文档）
3. **软件著作权**（如时间允许）
