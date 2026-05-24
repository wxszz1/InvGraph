# InvGraph — 投融资风险知识图谱可视化系统

SRT大学生研究训练计划项目，基于张华《基于时序知识图谱的投资决策研究与实现》论文。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + vis.js + Vite |
| 后端 | Spring Boot 3.2 + MyBatis |
| ML服务 | Python + FastAPI + HanLP + PyTorch |
| 图数据库 | Neo4j 5.x |
| 关系数据库 | MySQL 8.0 |

## 项目结构

```
project/
├── frontend/          # Vue 3 前端
├── backend/           # Spring Boot 后端
├── ml-service/        # Python NLP 服务
│   ├── ner/           # 实体识别模块
│   ├── relation/      # 关系抽取模块
│   │   ├── pl_marker/ # PL-Marker模型
│   │   ├── spn/       # SPN模型
│   │   └── fusion/    # 融合推理
│   ├── temporal/      # 时序分析模块
│   │   └── mttr/      # MTTR时序推理模型
│   └── entity_link/   # 实体对齐模块
├── data/              # 数据采集和处理脚本
│   ├── raw/           # 原始数据
│   ├── processed/     # 清洗后数据
│   └── scripts/       # 采集/清洗/导入脚本
├── sql/               # MySQL 建表脚本
└── docs/              # 文档
    ├── deploy.md      # 部署文档
    └── research-report.md  # 研究报告
```

## 环境要求

- Java 17+
- Python 3.9+
- Node.js 18+
- MySQL 8.0
- Neo4j 5.x Community Edition
- CUDA 11.8+ (可选，用于GPU训练)

## 快速开始

### 1. 数据库初始化

```bash
mysql -u root -p < sql/init.sql
```

### 2. 启动 ML 服务（Python）

```bash
cd ml-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. 启动后端（Java）

```bash
cd backend
mvn spring-boot:run
```

### 4. 启动前端（Node.js）

```bash
cd frontend
npm install
npm run dev
```

### 5. 导入示例数据

```bash
# 采集并清洗数据
cd data/scripts
python collect.py
python clean.py

# 导入MySQL（需先启动MySQL）
python import_mysql.py

# 导入Neo4j（需先启动Neo4j）
python import_neo4j.py
```

## 系统功能

### 核心功能

- **图谱总览**：力导向图展示投融资关系网络，支持缩放拖拽
- **节点搜索**：按企业/投资方名称搜索，高亮关联路径
- **时序筛选**：按时间范围筛选投资事件
- **文本抽取**：输入新闻文本，自动识别实体和关系并导入图谱
- **节点详情**：点击查看节点属性和关联关系

### 高级功能

- **时序分析**：分析投资事件的时间关系（之前、之后、重叠）
- **风险传导**：分析投资网络中的风险传播路径
- **投资热度**：展示行业投资热度分布热力图
- **企业时间线**：展示单个企业的融资历程
- **实体对齐**：自动识别和合并同一实体的不同表述

## NLP能力

### 实体识别

支持的实体类型：
- **Enterprise（企业）**：识别公司全称、简称
- **Investor（投资方）**：识别投资机构
- **Round（轮次）**：识别融资轮次（天使轮、A轮、B轮等）
- **Industry（行业）**：识别所属行业
- **Money（金额）**：识别融资金额
- **Time（时间）**：识别时间表达式

### 关系抽取

支持的关系类型：
- **INVEST（投资）**：一般投资关系
- **LEAD（领投）**：领投关系
- **FOLLOW（跟投）**：跟投关系
- **ACQUIRE（收购）**：收购关系

### 模型训练

系统集成了多个深度学习模型：

```bash
# 训练关系抽取模型
cd ml-service
python -m relation.pl_marker.train  # PL-Marker模型
python -m relation.spn.train        # SPN模型

# 训练时序推理模型
python -m temporal.mttr.gen_data    # 生成训练数据
python -m temporal.mttr.train       # 训练MTTR模型

# 训练实体对齐模型
python data/gen_ftrlim_data.py      # 生成训练数据
python train_ftrlim.py              # 训练FTRLIM模型
```

## 核心创新

### 1. 时序四元组模型

每条投资关系都带有时间属性，支持按时间维度分析投融资关系的演化。

### 2. 多模型融合推理

采用Stacking融合策略，结合PL-Marker（权重0.6）和SPN（权重0.4）的优势。

### 3. 神经时序推理

实现MTTR（Multi-Task Temporal Reasoning）模型，支持复杂的时序关系推理。

### 4. 实体对齐

实现FTRLIM模型，支持中英文实体对齐，自动识别别名（如"红杉资本"和"Sequoia Capital"）。

## 测试

```bash
cd ml-service
python test_all.py
```

测试覆盖：
- 实体识别：34个测试用例
- 关系抽取：13个测试用例
- 系统集成：20个测试用例
- 总计：73个断言，100%通过率

## 数据规模

| 数据类型 | 数量 |
|----------|------|
| 企业 | 388家 |
| 投资机构 | 87家 |
| 行业 | 14个 |
| 投融资事件 | 4388条 |

## 文档

- [部署文档](docs/deploy.md) - 详细的部署指南
- [研究报告](docs/research-report.md) - 完整的研究报告

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ner | POST | 实体识别 |
| /api/relation | POST | 关系抽取 |
| /api/extract | POST | 完整抽取 |
| /api/temporal/analyze | GET | 时序分析 |
| /api/align | POST | 实体对齐 |
| /api/graph/all | GET | 获取全图谱 |
| /api/graph/search | GET | 搜索节点 |
| /api/graph/filter | GET | 筛选图谱 |
| /api/import | POST | 导入三元组 |
| /api/statistics | GET | 获取统计信息 |
| /api/model/status | GET | 模型状态 |
| /api/train | POST | 训练模型 |

## 贡献者

- 王翊舟：ML服务、NLP模型
- 潘文宝：后端服务、数据库
- 李炜：前端可视化
- 邹凯城：数据采集与处理
- 文子昂：系统集成与测试

## 许可证

本项目仅供学术研究使用。
