# 融合时序特征的投融资风险知识图谱可视化系统

SRT大学生研究训练计划项目，基于张华《基于时序知识图谱的投资决策研究与实现》论文。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + vis.js + Vite |
| 后端 | Spring Boot 3.2 + MyBatis |
| ML服务 | Python + FastAPI + HanLP |
| 图数据库 | Neo4j 5.x |
| 关系数据库 | MySQL 8.0 |

## 项目结构

```
project/
├── frontend/          # Vue 3 前端
├── backend/           # Spring Boot 后端
├── ml-service/        # Python NLP 服务
├── data/              # 数据采集和处理脚本
│   ├── raw/           # 原始数据
│   ├── processed/     # 清洗后数据
│   └── scripts/       # 采集/清洗/导入脚本
├── sql/               # MySQL 建表脚本
└── docs/              # 设计文档和计划
```

## 环境要求

- Java 17+
- Python 3.9+
- Node.js 18+
- MySQL 8.0
- Neo4j 5.x Community Edition

## 安装与运行

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

- **图谱总览**：力导向图展示投融资关系网络，支持缩放拖拽
- **节点搜索**：按企业/投资方名称搜索，高亮关联路径
- **时序筛选**：按时间范围筛选投资事件
- **文本抽取**：输入新闻文本，自动识别实体和关系并导入图谱
- **节点详情**：点击查看节点属性和关联关系

## 核心创新

**时序四元组**（主体-关系-客体-时间）：每条投资关系都带有时间属性，支持按时间维度分析投融资关系的演化。
