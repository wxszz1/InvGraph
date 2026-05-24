# InvGraph 部署文档

## 环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Java | 17+ | Spring Boot 后端 |
| Python | 3.9+ | ML 服务 |
| Node.js | 18+ | 前端构建 |
| MySQL | 8.0 | 关系数据库 |
| Neo4j | 5.x | 图数据库 |
| CUDA | 11.8+ | GPU 训练（可选） |

## 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/wxszz1/InvGraph.git
cd InvGraph
```

### 2. 数据库初始化

#### MySQL

```bash
# 启动 MySQL 服务
# Windows: net start mysql80
# Linux: sudo systemctl start mysql

# 创建数据库和表
mysql -u root -p < sql/init.sql

# 导入示例数据（可选）
cd data/scripts
python collect.py
python clean.py
python import_mysql.py
```

#### Neo4j

```bash
# 启动 Neo4j 服务
# Windows: neo4j console
# Linux: sudo systemctl start neo4j

# 默认访问地址: http://localhost:7474
# 默认用户名: neo4j
# 默认密码: password（首次登录需修改）

# 导入数据到 Neo4j
cd data/scripts
python import_neo4j.py
```

### 3. 启动 ML 服务

```bash
cd ml-service

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**验证 ML 服务：**

```bash
# 测试 NER
curl -X POST http://localhost:8000/api/ner \
  -H "Content-Type: application/json" \
  -d '{"text": "红杉资本投资美团"}'

# 测试完整抽取
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "2023年3月高瓴资本领投腾讯A轮融资5亿美元"}'
```

### 4. 启动后端服务

```bash
cd backend

# 配置数据库连接（修改 src/main/resources/application.yml）
# spring.datasource.url: jdbc:mysql://localhost:3306/srt_kg
# spring.datasource.username: root
# spring.datasource.password: your_password
# neo4j.uri: bolt://localhost:7687
# neo4j.username: neo4j
# neo4j.password: your_password

# 编译并启动
mvn spring-boot:run
```

**验证后端服务：**

```bash
# 测试统计接口
curl http://localhost:8080/api/statistics

# 测试图谱查询
curl http://localhost:8080/api/graph/all
```

### 5. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**访问前端：**

- 开发环境：http://localhost:5173
- 生产环境：http://localhost:8080（需构建）

### 6. 构建生产版本

```bash
cd frontend

# 构建
npm run build

# 构建产物在 dist/ 目录
# 可以部署到 Nginx 或其他 Web 服务器
```

## 模型训练（可选）

### 训练关系抽取模型

```bash
cd ml-service

# 训练 PL-Marker 模型
python -m relation.pl_marker.train

# 训练 SPN 模型
python -m relation.spn.train
```

### 训练时序推理模型

```bash
# 生成训练数据
python -m temporal.mttr.gen_data

# 训练 MTTR 模型
python -m temporal.mttr.train
```

### 训练实体对齐模型

```bash
# 生成训练数据
python data/gen_ftrlim_data.py

# 训练 FTRLIM 模型
python train_ftrlim.py
```

## 配置说明

### ML 服务配置

编辑 `ml-service/main.py` 中的配置：

```python
CONFIG = {
    "model_name": "bert-base-chinese",  # 预训练模型
    "max_seq_len": 128,                 # 最大序列长度
    "batch_size": 16,                   # 批次大小
    "learning_rate": 2e-5,              # 学习率
}
```

### 后端配置

编辑 `backend/src/main/resources/application.yml`：

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/srt_kg
    username: root
    password: your_password

neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  password: your_password

nlp:
  service:
    url: http://localhost:8000
```

### 前端配置

编辑 `frontend/src/api/index.js`：

```javascript
const api = axios.create({
  baseURL: 'http://localhost:8080/api',  // 后端地址
  timeout: 10000
})
```

## 常见问题

### 1. Neo4j 连接失败

```
错误: Unable to connect to Neo4j
```

**解决方案：**
- 确认 Neo4j 服务已启动
- 检查端口 7687 是否被占用
- 验证用户名密码是否正确

### 2. MySQL 连接失败

```
错误: Communications link failure
```

**解决方案：**
- 确认 MySQL 服务已启动
- 检查 `srt_kg` 数据库是否存在
- 验证用户名密码是否正确

### 3. ML 服务启动慢

**原因：** 首次启动需要下载 HanLP 模型（约 500MB）

**解决方案：**
- 等待模型下载完成
- 或手动下载模型到缓存目录

### 4. 前端页面空白

**解决方案：**
- 检查浏览器控制台是否有错误
- 确认后端服务是否正常运行
- 检查 CORS 配置是否正确

### 5. GPU 训练失败

```
错误: CUDA out of memory
```

**解决方案：**
- 减小 batch_size
- 使用 CPU 训练（较慢）
- 清理 GPU 显存

## 性能优化

### 1. 数据库优化

```sql
-- 为常用查询添加索引
CREATE INDEX idx_enterprise_name ON enterprise(name);
CREATE INDEX idx_investor_name ON investor(name);
CREATE INDEX idx_event_date ON investment_event(event_date);
```

### 2. Neo4j 优化

```cypher
-- 创建索引
CREATE INDEX enterprise_name FOR (e:Enterprise) ON (e.name);
CREATE INDEX investor_name FOR (i:Investor) ON (i.name);

-- 创建约束
CREATE CONSTRAINT enterprise_id_unique FOR (e:Enterprise) REQUIRE e.mysql_id IS UNIQUE;
```

### 3. 前端优化

- 启用 Vue 生产模式
- 压缩静态资源
- 使用 CDN 加速

## 监控与日志

### ML 服务日志

```bash
# 查看服务日志
tail -f ml-service.log

# 启用调试模式
uvicorn main:app --reload --log-level debug
```

### 后端日志

```bash
# 查看 Spring Boot 日志
tail -f backend.log

# 启用调试模式
mvn spring-boot:run -Dspring-boot.run.jvmArguments="-Ddebug=true"
```

## 备份与恢复

### 数据库备份

```bash
# MySQL 备份
mysqldump -u root -p srt_kg > backup_$(date +%Y%m%d).sql

# Neo4j 备份
neo4j-admin database dump neo4j --to-path=/backup/
```

### 数据库恢复

```bash
# MySQL 恢复
mysql -u root -p srt_kg < backup_20260524.sql

# Neo4j 恢复
neo4j-admin database load neo4j --from-path=/backup/
```

## 生产环境部署

### 使用 Docker（推荐）

```dockerfile
# ML 服务 Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# 前端 Dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # ML 服务
    location /ml {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 联系方式

如有部署问题，请联系项目负责人或查看 GitHub Issues：
- GitHub: https://github.com/wxszz1/InvGraph
