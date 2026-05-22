# 融合时序特征的投融资风险知识图谱可视化系统 — 完善计划 v2

> **目标：** 将当前基础原型系统逐步完善为符合SRT提案要求的完整系统
>
> **硬件：** RTX 4060 8GB VRAM
>
> **当前状态：** 基础原型（规则NER + 简单抽取 + Neo4j + Vue可视化）
>
> **修订记录：** v2 — 经10轮审查后修正，补全了Schema定义、文件清单、风险应对等

---

## 总体架构（完善后）

```
┌─────────────────────────────────────────────────────────┐
│                     前端 Vue 3 + ECharts                  │
│  ┌──────────┬──────────┬──────────┬──────────┬────────┐  │
│  │ 数据概览  │ 知识图谱  │ 时序分析  │ 风险传导  │ 文本抽取│  │
│  │Dashboard │ Graph    │Timeline  │RiskPath  │Extract │  │
│  ├──────────┴──────────┴──────────┴──────────┴────────┤  │
│  │  投资热度 Heatmap │ 企业融资历史 EnterpriseTimeline  │  │
│  └─────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                 后端 Spring Boot 3.2 + MyBatis            │
│  ┌──────────┬──────────┬──────────┬──────────────────┐   │
│  │Graph API │Data API  │Analytics │ NLP Proxy        │   │
│  │(Neo4j)   │(MySQL)   │API       │ (→ ML Service)   │   │
│  └──────────┴──────────┴──────────┴──────────────────┘   │
├──────────────────────┬──────────────────────────────────┤
│       Neo4j 5.x      │       ML 服务 FastAPI             │
│  ┌────────────────┐  │  ┌──────┬────────┬────────────┐  │
│  │ 时序图谱存储    │  │  │HanLP │SPN+PLM │ FTRLIM     │  │
│  │ 三级模式层      │  │  │2.x  │+融合   │ +MTTR      │  │
│  │ 时序Cypher查询  │  │  │NER  │RelExt  │ EntityLink │  │
│  └────────────────┘  │  └──────┴────────┴────────────┘  │
├──────────────────────┴──────────────────────────────────┤
│                    MySQL 8.0                              │
│    原始数据 + 抽取结果 + 行业分类 + 企业属性 + 配置        │
└─────────────────────────────────────────────────────────┘
```

## 数据流设计

```
数据源（财经新闻/企业公告/DuIE2.0）
         │
         ▼
    [数据采集] ──→ data/raw/
         │
         ▼
    [数据清洗] ──→ data/processed/
         │
         ▼
    [HanLP NER + SPN+PLM 关系抽取 + 时序四元组]
         │
    ┌────┴────┐
    ▼         ▼
  MySQL     Neo4j
  (明细存储)  (图谱查询)
    │         │
    └────┬────┘
         ▼
    [FTRLIM 实体对齐] ──→ 合并后回写 MySQL + Neo4j
         │
         ▼
    [前端可视化消费]
```

**MySQL-Neo4j同步策略：**
- MySQL 为主数据源（master），存储完整明细数据
- Neo4j 为查询副本（read replica），存储图谱关系
- 导入流程：先写MySQL → 再同步到Neo4j
- FTRLIM对齐后：先更新MySQL → 再更新Neo4j
- 不做实时双向同步，只做单向批量同步

---

## 分阶段计划

### 第一阶段：本体设计 + HanLP + 数据基础（约2.5周）

**目标：** 定义三级本体，替换规则NER为HanLP 2.x，集成MySQL，开始数据采集

#### 1.1 "行业-企业-投资"三级本体设计 ★（从阶段三提前）
- 文件：`ml-service/schema/ontology.py`（新建）
- 文件：`ml-service/schema/__init__.py`（新建）
- 实体类型及属性定义：
  ```python
  ENTITY_TYPES = {
      "Enterprise": ["name", "founding_date", "industry", "valuation", "status", "description"],
      "Investor":   ["name", "type", "aum", "focus_industry", "description"],  # type: VC/PE/Angel
      "Round":      ["name", "sequence"],  # A轮/B轮/天使轮/C轮/Pre-IPO
      "Industry":   ["name", "policy_date", "hotness_score"],
  }
  RELATION_TYPES = {
      "INVEST":    "Investor → Enterprise",
      "LEAD":      "Investor → Enterprise (领投)",
      "FOLLOW":    "Investor → Enterprise (跟投)",
      "ACQUIRE":   "Investor → Enterprise (收购)",
      "BELONGS_TO":"Enterprise → Industry",
      "COMPETE":   "Enterprise ↔ Enterprise",
      "CO_INVEST": "Investor ↔ Investor",
  }
  # 时间属性分类
  TIME_SENSITIVE = ["valuation", "investment_amount", "round", "hotness_score"]
  TIME_CONSTANT  = ["industry", "type", "founding_date", "name"]
  ```
- 本体文件供后续所有模块引用（NER输出类型、关系抽取关系类型、Neo4j节点标签）

#### 1.2 ML服务 — HanLP 2.x集成
- 文件：`ml-service/ner/recognizer.py`（重写）
- 文件：`ml-service/ner/keywords.py`（更新，扩充轮次和行业关键词）
- 文件：`ml-service/schemas.py`（更新，新增实体/关系类型）
- 文件：`ml-service/requirements.txt`（更新，新增依赖）
- 实现：
  - 安装 `hanlp` 2.x（`pip install hanlp`，使用预训练模型 `hanlp/pretrain`）
  - HanLP分词 + NER（PER/ORG/LOC/GPE）
  - 投融资领域实体类型映射：
    - ORG → 查询投资机构字典 → 匹配则Investor，否则Enterprise
    - PER → Person（暂不处理）
    - LOC/GPE → Location（暂不处理）
  - 融资轮次关键词匹配（天使轮/Pre-A/A/B/C/D/Pre-IPO/IPO）
  - 行业分类关键词匹配（互联网/新能源/芯片/消费/医疗等）
  - 金额提取（正则匹配"X亿元"/"X万美元"等）
  - 时间敏感/非敏感属性区分（绑定时间戳 vs 标记"constant"）
- requirements.txt新增依赖：
  ```
  hanlp>=2.1
  torch>=2.0
  transformers>=4.30
  ```

#### 1.3 后端 — MySQL集成
- 文件：`sql/init.sql`（新建，建表脚本）
- 文件：`backend/src/main/java/com/srt/kg/entity/Enterprise.java`
- 文件：`backend/src/main/java/com/srt/kg/entity/Investor.java`
- 文件：`backend/src/main/java/com/srt/kg/entity/InvestmentEvent.java`
- 文件：`backend/src/main/java/com/srt/kg/entity/Industry.java`
- 文件：`backend/src/main/java/com/srt/kg/mapper/EnterpriseMapper.java`
- 文件：`backend/src/main/java/com/srt/kg/mapper/InvestorMapper.java`
- 文件：`backend/src/main/java/com/srt/kg/mapper/InvestmentEventMapper.java`
- 文件：`backend/src/main/java/com/srt/kg/mapper/IndustryMapper.java`
- 文件：`backend/src/main/resources/mapper/EnterpriseMapper.xml`
- 文件：`backend/src/main/resources/mapper/InvestorMapper.xml`
- 文件：`backend/src/main/resources/mapper/InvestmentEventMapper.xml`
- 文件：`backend/src/main/resources/mapper/IndustryMapper.xml`
- 文件：`backend/src/main/java/com/srt/kg/controller/DataController.java`
- 文件：`backend/src/main/resources/application.yml`（更新MyBatis mapper-locations）

**MySQL表结构：**
```sql
-- 行业分类表
CREATE TABLE industry (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    policy_date VARCHAR(20),
    hotness_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 企业表
CREATE TABLE enterprise (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    founding_date VARCHAR(20),
    industry_id BIGINT,
    valuation DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'active',  -- active/acquired/ipo/bankrupt
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (industry_id) REFERENCES industry(id)
);

-- 投资机构表
CREATE TABLE investor (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20),  -- VC/PE/Angel/Government
    aum DECIMAL(15,2),  -- 管理规模
    focus_industry VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 投资事件表
CREATE TABLE investment_event (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    investor_id BIGINT NOT NULL,
    enterprise_id BIGINT NOT NULL,
    round VARCHAR(50),  -- 天使轮/A轮/B轮/C轮/Pre-IPO
    amount DECIMAL(15,2),
    time VARCHAR(20),  -- 投资时间（年份或日期）
    lead_flag TINYINT DEFAULT 0,  -- 1=领投 0=跟投
    relation VARCHAR(20) DEFAULT 'INVEST',  -- INVEST/LEAD/FOLLOW/ACQUIRE
    source TEXT,  -- 数据来源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (investor_id) REFERENCES investor(id),
    FOREIGN KEY (enterprise_id) REFERENCES enterprise(id)
);
```

**DataController API：**
- `GET /api/data/enterprises?page=1&size=20&keyword=xxx` — 企业列表（带分页和搜索）
- `GET /api/data/investors?page=1&size=20` — 投资机构列表
- `GET /api/data/industries` — 行业列表
- `POST /api/data/import` — 批量导入数据到MySQL并同步到Neo4j
- 响应格式统一：`{ code: 200, msg: "success", data: {...} }`

#### 1.4 数据采集（从阶段五提前）
- 文件：`data/scripts/collect.py`（新建）
- 文件：`data/scripts/clean.py`（新建）
- 数据源优先级：
  1. DuIE2.0数据集（百度开源，GitHub直接下载）
  2. 公开投融资数据（鲸准/IT桔子公开数据）
  3. 财经新闻爬取（36氪、虎嗅，基础requests+BeautifulSoup）
- 采集量目标：初期200+企业，500+投资事件
- 输出格式：JSON（适配后续模型训练和MySQL导入）

#### 验收标准
- [ ] HanLP 2.x能从文本识别出ORG/PER/LOC/时间/金额
- [ ] 实体类型映射准确（Enterprise/Investor/Round/Industry）
- [ ] MySQL四张表建好，能CRUD，MyBatis映射正确
- [ ] 三级本体定义完成，可供后续模块引用
- [ ] 数据采集200+企业，500+投资事件
- [ ] DuIE2.0数据集下载并筛选投融资相关子集完成

---

### 第二阶段：SPN+PL-Marker融合关系抽取 + MTTR（约5-6周）

**目标：** 实现深度学习关系抽取模型，生成时序四元组，MTTR时序推理

#### 2.0 数据预处理
- 文件：`ml-service/relation/data/preprocess.py`（新建）
- 文件：`ml-service/relation/data/duie_to_plmarker.py`（新建）
- 文件：`ml-service/relation/data/duie_to_spn.py`（新建）
- 文件：`ml-service/relation/data/config.py`（新建，训练超参数）
- 功能：
  - DuIE2.0原始JSON → PL-Marker训练格式（entity span标注 + relation label）
  - DuIE2.0原始JSON → SPN训练格式（三元组集合）
  - 投融资领域数据增强（同义替换、实体替换）
  - 训练/验证/测试集划分（8:1:1）
- 训练配置：
  ```python
  TRAIN_CONFIG = {
      "model_name": "bert-base-chinese",
      "max_seq_len": 256,
      "batch_size": 16,
      "learning_rate": 2e-5,
      "epochs": 30,
      "fp16": True,  # PyTorch AMP
      "gradient_accumulation_steps": 2,
      "warmup_ratio": 0.1,
  }
  ```

#### 2.1 PL-Marker实现
- 文件：`ml-service/relation/pl_marker/__init__.py`
- 文件：`ml-service/relation/pl_marker/model.py` — BERT + PL-Marker模型定义
- 文件：`ml-service/relation/pl_marker/layers.py` — 实体span标注层 + 关系分类层
- 文件：`ml-service/relation/pl_marker/data_loader.py` — 数据加载器
- 文件：`ml-service/relation/pl_marker/train.py` — 训练脚本
- 文件：`ml-service/relation/pl_marker/evaluate.py` — 评估脚本（F1/P/R）
- 文件：`ml-service/relation/pl_marker/inference.py` — 推理接口
- 模型结构：
  - Backbone: BERT-base-chinese（110M参数，适配8GB显存）
  - 实体识别: PL-Marker的entity span标记方式（head/tail marker）
  - 关系分类: 对匹配到的实体对做关系分类
  - 使用fp16混合精度训练（PyTorch `torch.cuda.amp`）
  - gradient_accumulation_steps=2 等效batch_size=32

#### 2.2 SPN（Set Prediction Network）实现
- 文件：`ml-service/relation/spn/__init__.py`
- 文件：`ml-service/relation/spn/model.py` — SPN模型定义
- 文件：`ml-service/relation/spn/matcher.py` — Hungarian二分匹配
- 文件：`ml-service/relation/spn/loss.py` — 匹配损失 + 集合预测损失
- 文件：`ml-service/relation/spn/data_loader.py`
- 文件：`ml-service/relation/spn/train.py`
- 文件：`ml-service/relation/spn/evaluate.py`
- 文件：`ml-service/relation/spn/inference.py`
- 模型结构：
  - Backbone: BERT-base-chinese
  - 并行Decoder: N个query slot并行输出(head, relation, tail)
  - Hungarian Matching: 计算预测集合与真实集合的最优匹配
  - 损失函数: L_match + L_relation + L_entity

#### 2.3 融合框架（单层Stacking）
- 文件：`ml-service/relation/fusion/__init__.py`
- 文件：`ml-service/relation/fusion/fusion.py` — Stacking融合主逻辑
- 文件：`ml-service/relation/fusion/scorer.py` — 融合评分器
- 实现思路：
  - SPN输出候选三元组集合（含置信度分数）
  - PL-Marker输出候选三元组集合（含置信度分数）
  - 特征拼接：[SPN_score, PLM_score, entity_overlap, relation_match]
  - 分类器（LogisticRegression/小MLP）判定最终保留/丢弃
  - 去重：同一(h,r,t)取融合后最高分
  - 输出最终三元组集合

#### 2.4 时序四元组生成
- 文件：`ml-service/temporal/__init__.py`
- 文件：`ml-service/temporal/extractor.py` — 时间提取与四元组生成
- 文件：`ml-service/temporal/normalizer.py` — 时间规范化
- 实现：
  - HanLP时间词识别（`hanlp.load(hanlp.pretrained.ner.MSRA_NER_BERT_BASE_ZH)`中的时间实体）
  - 正则匹配补充（"2023年Q3"/"去年"/"近期"等）
  - 时间关联策略：将时间关联到最近的三元组（基于句子位置）
  - 时间规范化："2023年"→"2023"，"2023年Q3"→"2023Q3"，"去年"→当前年-1
  - 输出格式：`{ head, relation, tail, time }`

#### 2.5 MTTR多任务时序推理
- 文件：`ml-service/temporal/mttr/__init__.py`
- 文件：`ml-service/temporal/mttr/model.py` — MTTR模型定义
- 文件：`ml-service/temporal/mttr/reasoner.py` — 时序推理逻辑
- 实现思路：
  - 多任务学习：同时预测关系类型 + 时间先后顺序
  - 时序关系分类：before / after / overlap / simultaneous
  - 基于BERT的时序编码：对(time_i, relation_i, time_j, relation_j)做时序关系预测
  - 推理：给定时序四元组集合，推理事件间的时序逻辑关系
  - 投融资场景约束：
    - 融资轮次递进性：天使轮 before A轮 before B轮 before C轮
    - 同一轮次内，领投与跟投同时发生
    - 投资时间不早于企业成立时间

#### 2.6 ML服务API更新
- 文件：`ml-service/main.py`（更新）
- 接口变更：
  - `POST /api/ner` — 更新为HanLP 2.x实现
  - `POST /api/relation` — 新增，SPN+PL-Marker融合抽取
  - `POST /api/extract` — 更新为完整管线（NER→关系抽取→时序四元组→MTTR推理）
  - `POST /api/train` — 新增，异步触发模型训练
  - `GET /api/model/status` — 新增，查询训练进度和模型状态
- 训练接口异步处理：使用 `asyncio` + `threading`，后台训练，前端轮询状态
- 模型存储目录：`ml-service/models/`
  ```
  models/
  ├── pl_marker/
  │   └── best_model.bin
  ├── spn/
  │   └── best_model.bin
  ├── fusion/
  │   └── scorer.pkl
  └── mttr/
      └── best_model.bin
  ```

#### 验收标准
- [ ] PL-Marker在DuIE2.0投融资子集上F1 > 60%
- [ ] SPN并行抽取正常工作，F1 > 55%
- [ ] 融合框架F1 > 单模型最高F1
- [ ] 时序四元组生成准确率 > 80%
- [ ] MTTR能正确判断融资轮次递进关系
- [ ] 训练接口能异步触发并查询进度
- [ ] 所有模型产物保存到models/目录

---

### 第三阶段：FTRLIM实体对齐 + Neo4j时序扩展（约2周）

**目标：** 实现知识融合、实体对齐，扩展Neo4j时序查询能力

#### 3.1 FTRLIM实体匹配
- 文件：`ml-service/entity_link/__init__.py`
- 文件：`ml-service/entity_link/blocker.py` — MultiObj分块算法
- 文件：`ml-service/entity_link/similarity.py` — 相似度计算
- 文件：`ml-service/entity_link/matcher.py` — FTRL在线学习模型
- 文件：`ml-service/entity_link/aligner.py` — 实体对齐主流程
- 文件：`ml-service/entity_link/validator.py` — 时序约束验证

**blocker.py：**
- 按实体类型分块（只有同类型的实体才比较）
- 按名称首字母/拼音分桶
- 减少候选对数量（从O(n²)降到O(n·k)）

**similarity.py：**
- 最小编辑距离（名称相似度，归一化到0-1）
- Jaccard系数（属性集合相似度）
- 字符级n-gram相似度
- 类型一致性（0或1）

**matcher.py：**
- FTRL (Follow The Regularized Leader) 在线学习
- 特征向量：[edit_dist, jaccard, ngram_sim, type_match, co_occurrence]
- 每次有新标注数据时增量更新权重
- 输出：匹配概率 > 阈值 → 合并

**validator.py（新增 — FTRLIM时序约束）：**
- 融资轮次递进性检查：A轮时间 < B轮时间
- 投资时间合理性：投资时间 >= 企业成立时间
- 同一轮次时间一致性：同一轮融资的不同投资方时间应接近
- 异常数据标记而非直接删除（保留审计）

#### 3.2 Neo4j时序扩展
- 文件：`backend/src/main/java/com/srt/kg/service/Neo4jService.java`（更新）
- 文件：`backend/src/main/java/com/srt/kg/controller/GraphController.java`（更新）
- 时间属性扩展：
  - 关系属性增加：`start_time`, `end_time`, `update_freq`
  - 节点属性增加：`founding_date`（Enterprise）, `first_invest_time`（Investor）
- 新增Cypher时序查询：
  ```cypher
  -- 时间范围查询（已有filterByTime扩展）
  MATCH (i:Investor)-[r:INVEST]->(e:Enterprise)
  WHERE r.time >= $start AND r.time <= $end
  RETURN i, r, e

  -- 投资方追投模式查询
  MATCH (i:Investor)-[r1:INVEST]->(e:Enterprise)<-[r2:INVEST]-(i)
  WHERE r1.time < r2.time
  RETURN i, e, r1, r2

  -- 跨行业投资查询
  MATCH (i:Investor)-[r:INVEST]->(e:Enterprise)-[:BELONGS_TO]->(ind:Industry)
  WHERE r.time >= $start AND r.time <= $end
  RETURN ind.name, count(r) as invest_count
  ORDER BY invest_count DESC
  ```
- 时序约束检查：在importTriples时调用validator.py验证

#### 验收标准
- [ ] FTRLIM能识别同名异义（"小米"=手机 vs "小米"=农业）和异名同义（"字节跳动"="ByteDance中国"）
- [ ] 时序约束validator能发现融资轮次倒置等异常
- [ ] Neo4j支持时间范围查询、追投模式查询
- [ ] 对齐后的实体在MySQL和Neo4j中一致

---

### 第四阶段：可视化增强（约3周）

**目标：** 实现提案中的高级可视化功能

#### 4.1 风险传导路径可视化
- 文件：`frontend/src/views/RiskPathView.vue`（新建）
- 文件：`backend/src/main/java/com/srt/kg/controller/RiskController.java`（新建）
- 后端API：
  - `GET /api/risk/path?source={name}&depth={1-5}` — 风险传导路径查询
  - 使用Neo4j `shortestPath` / `allShortestPaths` 查询
  - 返回：路径节点、边、传导层数、关键节点标记
- 前端功能：
  - 搜索框选择源节点（投资方或企业）
  - 滑块设置传导深度（1-5层）
  - 力导向图展示传导路径（高亮关键节点和瓶颈）
  - 传导强度用边粗细和颜色深浅表示
  - 点击路径节点查看详情

#### 4.2 跨行业投资热度时序看板
- 文件：`frontend/src/views/HeatmapView.vue`（新建）
- 文件：`backend/src/main/java/com/srt/kg/controller/AnalyticsController.java`（新建）
- 后端API：
  - `GET /api/analytics/heatmap?startYear={year}&endYear={year}` — 行业×年份热度矩阵
  - `GET /api/analytics/industry/{name}/events?year={year}` — 某行业某年事件列表
- 前端功能：
  - ECharts热力图：X轴=年份，Y轴=行业，颜色深度=投资热度
  - 切换维度：投资数量 / 投资金额
  - 点击格子下钻查看具体事件列表
  - 时间范围选择器

#### 4.3 企业融资历史关联图
- 文件：`frontend/src/views/EnterpriseTimeline.vue`（新建）
- 后端API：
  - `GET /api/enterprise/{id}/history` — 企业融资时间线
- 前端功能：
  - 搜索框选择企业
  - 甘特图式时间线展示融资历程
  - 每轮融资卡片：轮次、投资方、估值、金额
  - 右侧面板展示同轮次其他企业（对比）

#### 4.4 前端集成更新
- 文件：`frontend/src/router/index.js`（更新，新增3个路由）
- 文件：`frontend/src/App.vue`（更新，侧边栏增加3个导航项）
- 文件：`frontend/src/api/index.js`（更新，新增API方法）
- 文件：`frontend/package.json`（更新，新增echarts依赖）

**新增路由：**
```js
{ path: '/risk', name: 'risk', component: RiskPathView },
{ path: '/heatmap', name: 'heatmap', component: HeatmapView },
{ path: '/enterprise', name: 'enterprise', component: EnterpriseTimeline },
```

**侧边栏导航（7项）：**
1. 数据概览 Dashboard
2. 知识图谱 Graph
3. 时序分析 Timeline
4. 风险传导 Risk Path ← 新增
5. 投资热度 Heatmap ← 新增
6. 企业融资 Enterprise ← 新增
7. 文本抽取 Extract

**api/index.js新增：**
```js
getRiskPath: (source, depth) => api.get('/risk/path', { params: { source, depth } }),
getHeatmap: (startYear, endYear) => api.get('/analytics/heatmap', { params: { startYear, endYear } }),
getIndustryEvents: (industry, year) => api.get(`/analytics/industry/${industry}/events`, { params: { year } }),
getEnterpriseHistory: (id) => api.get(`/enterprise/${id}/history`),
```

**package.json新增：**
```json
"dependencies": {
  "echarts": "^5.4.0"
}
```

#### 验收标准
- [ ] 风险传导路径能正确展示2-3层传导关系
- [ ] 热力图能按行业×年份展示投资热度，支持维度切换
- [ ] 企业融资历史时间线完整展示轮次序列
- [ ] 所有新页面与现有深色主题UI风格一致
- [ ] 侧边栏7个导航项全部可用

---

### 第五阶段：数据扩充 + 系统联调（约2-3周）

**目标：** 扩充真实数据，全系统联调测试

#### 5.1 数据批量导入
- 文件：`data/scripts/import_mysql.py`（新建）
- 文件：`data/scripts/import_neo4j.py`（新建）
- 数据导入流程：
  1. 清洗后的JSON数据 → import_mysql.py → MySQL
  2. MySQL → import_neo4j.py → Neo4j
  3. 使用FTRLIM对齐后去重
- 目标数据量：500+企业，200+投资机构，2000+投资事件，10+行业

#### 5.2 ML模型部署
- 训练好的模型加载到ML服务
- 模型预热（首次请求不等待冷启动）
- 模型版本管理：`models/{model_name}/version.txt`

#### 5.3 全系统联调
- 端到端测试：文本输入 → HanLP NER → SPN+PLM关系抽取 → 时序四元组 → 导入Neo4j → 前端展示
- API完整性测试：所有后端+ML服务接口
- 前端全页面功能测试：7个页面逐一验证
- 性能优化：
  - 大图谱（500+节点）渲染性能
  - Neo4j查询响应时间优化（索引）
  - ECharts大数据量热力图渲染

#### 验收标准
- [ ] 系统数据量达到500+企业，2000+关系
- [ ] 全流程无报错：文本输入 → NER → 关系抽取 → 四元组 → 图谱 → 可视化
- [ ] 7个前端页面全部可用
- [ ] 大图谱（500+节点）渲染流畅（<3秒）
- [ ] ML模型推理延迟 < 2秒（单条文本）

---

## 技术选型汇总

| 组件 | 技术方案 | 版本 |
|------|---------|------|
| NER | HanLP 2.x | >=2.1 |
| 关系抽取(流水线) | PL-Marker (BERT-base-chinese) | transformers>=4.30 |
| 关系抽取(联合) | SPN (Set Prediction Network) | PyTorch>=2.0 |
| 融合 | Stacking单层融合（LogisticRegression） | sklearn |
| 实体对齐 | FTRL在线学习 + 编辑距离/Jaccard | 自实现 |
| 时序推理 | MTTR多任务时序推理 | PyTorch |
| 时序抽取 | HanLP时间词识别 + 正则 | hanlp>=2.1 |
| 图谱存储 | Neo4j 5.x | Neo4j Desktop |
| 关系存储 | MySQL 8.0 | 8.0+ |
| 后端 | Spring Boot 3.2 + MyBatis | Java 23 |
| ML服务 | FastAPI + PyTorch + Transformers | Python 3.13 |
| 前端 | Vue 3 + vis-network + ECharts 5 | Node 18+ |
| 深度学习 | PyTorch 2.x, BERT-base-chinese | CUDA 12.x |
| GPU | RTX 4060 8GB | fp16混合精度 |
| 训练优化 | gradient_accumulation=2, AMP | torch.cuda.amp |

## 文件清单汇总

### 新建文件（37个）
```
ml-service/
├── schema/
│   ├── __init__.py
│   └── ontology.py                    # 三级本体定义
├── ner/
│   └── recognizer.py                  # 重写：HanLP 2.x
├── relation/
│   ├── data/
│   │   ├── config.py                  # 训练超参数
│   │   ├── preprocess.py              # 数据预处理
│   │   ├── duie_to_plmarker.py        # DuIE→PL-Marker格式
│   │   └── duie_to_spn.py            # DuIE→SPN格式
│   ├── pl_marker/
│   │   ├── __init__.py
│   │   ├── model.py                   # PL-Marker模型
│   │   ├── layers.py                  # 实体标注层+关系分类层
│   │   ├── data_loader.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── inference.py
│   ├── spn/
│   │   ├── __init__.py
│   │   ├── model.py                   # SPN模型
│   │   ├── matcher.py                 # Hungarian匹配
│   │   ├── loss.py                    # 匹配损失
│   │   ├── data_loader.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── inference.py
│   └── fusion/
│       ├── __init__.py
│       ├── fusion.py                  # Stacking融合
│       └── scorer.py                  # 融合评分
├── temporal/
│   ├── __init__.py
│   ├── extractor.py                   # 时序四元组生成
│   ├── normalizer.py                  # 时间规范化
│   └── mttr/
│       ├── __init__.py
│       ├── model.py                   # MTTR模型
│       └── reasoner.py                # 时序推理
├── entity_link/
│   ├── __init__.py
│   ├── blocker.py                     # MultiObj分块
│   ├── similarity.py                  # 相似度计算
│   ├── matcher.py                     # FTRL匹配
│   ├── aligner.py                     # 对齐主流程
│   └── validator.py                   # 时序约束验证
├── models/                            # 模型产物存储目录
└── requirements.txt                   # 更新
sql/
└── init.sql                           # MySQL建表脚本
data/
└── scripts/
    ├── collect.py                     # 数据采集
    ├── clean.py                       # 数据清洗
    ├── import_mysql.py                # 导入MySQL
    └── import_neo4j.py                # 导入Neo4j
backend/src/main/java/.../
├── entity/
│   ├── Enterprise.java
│   ├── Investor.java
│   ├── InvestmentEvent.java
│   └── Industry.java
├── mapper/
│   ├── EnterpriseMapper.java
│   ├── InvestorMapper.java
│   ├── InvestmentEventMapper.java
│   └── IndustryMapper.java
├── controller/
│   ├── DataController.java
│   ├── RiskController.java
│   └── AnalyticsController.java
backend/src/main/resources/mapper/
├── EnterpriseMapper.xml
├── InvestorMapper.xml
├── InvestmentEventMapper.xml
└── IndustryMapper.xml
frontend/src/views/
├── RiskPathView.vue
├── HeatmapView.vue
└── EnterpriseTimeline.vue
```

### 需更新的现有文件（10个）
```
ml-service/ner/keywords.py             # 扩充关键词
ml-service/ner/__init__.py             # 导出更新
ml-service/schemas.py                  # 新增类型
ml-service/main.py                     # 新增API
backend/src/main/resources/application.yml  # MyBatis配置
backend/.../service/Neo4jService.java  # 时序查询
backend/.../controller/GraphController.java  # import增强
frontend/src/router/index.js           # 新增路由
frontend/src/App.vue                   # 侧边栏7项
frontend/src/api/index.js              # 新增API方法
frontend/package.json                  # echarts依赖
```

## 实施顺序

```
阶段一（本体+HanLP+MySQL+数据采集）────── 2.5周
     │
阶段二（SPN+PLM+融合+时序+MTTR）──────── 5-6周
     │  同时可进行 → 阶段四（可视化增强）── 3周
     │
阶段三（FTRLIM+Neo4j时序扩展）─────────── 2周
     │
阶段五（数据扩充+联调）────────────────── 2-3周
     │
总计约 12-14 周（含并行阶段四）
```

## 风险应对

| 风险 | 级别 | 应对策略 |
|------|------|---------|
| DuIE2.0获取困难 | 高 | 备用方案：用自建标注数据（从财经新闻手动标注500条）+ 迁移学习 |
| SPN开源实现稀缺 | 高 | 备用方案：简化SPN为multi-head attention并行解码，或只用PL-Marker + 后处理 |
| 8GB显存不足 | 中 | gradient_checkpointing + fp16 + batch_size降到8 + gradient_accumulation=4 |
| 模型F1不达标 | 高 | 数据增强 + 更换backbone（RoBERTa-wwm-ext）+ 调参10轮以上 |
| 数据采集反爬 | 中 | 降低频率 + 用公开数据集为主 + 爬虫为辅 |
| MySQL-Neo4j不一致 | 中 | 以MySQL为准，每次导入前先清Neo4j再重导 |
| 训练时间过长 | 中 | 先用小数据集验证pipeline，再扩大数据量 |
