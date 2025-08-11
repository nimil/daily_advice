# 部署指南

## 本地开发环境

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp env.example .env

# 编辑配置文件，填入正确的值
vim .env
```

### 3. 验证配置

```bash
# 运行配置验证脚本
python validate_config.py
```

### 4. 启动服务

```bash
# 直接运行
python app.py

# 或使用Flask开发服务器
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=8090
```

## Docker 部署

### 1. 构建镜像

```bash
# 构建镜像
docker build -t wecom-kf:latest .

# 或指定平台（用于跨平台部署）
docker build --platform linux/amd64 -t wecom-kf:latest .
```

### 2. 使用环境变量运行

```bash
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  -e CORP_ID="your_corp_id" \
  -e CORP_SECRET="your_corp_secret" \
  -e OPEN_KFID="your_open_kfid" \
  -e EXTERNAL_USERID="your_external_userid" \
  -e SOLAR_TERMS_API_KEY="your_api_key" \
  -e ALMANAC_API_KEY="your_api_key" \
  -e GLM4_API_KEY="your_api_key" \
  -e LIFE_SUGGESTION_API_KEY="your_api_key" \
  -e DEEPSEEK_API_KEY="your_api_key" \
  -e HOLIDAY_API_KEY="your_api_key" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  wecom-kf:latest
```

### 3. 使用环境文件运行

```bash
# 创建环境文件
cp env.example .env
# 编辑 .env 文件，填入正确的值

# 使用环境文件运行
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  wecom-kf:latest
```

### 4. 使用 Docker Compose

```bash
# 设置环境变量
export CORP_ID="your_corp_id"
export CORP_SECRET="your_corp_secret"
export OPEN_KFID="your_open_kfid"
export EXTERNAL_USERID="your_external_userid"
export SOLAR_TERMS_API_KEY="your_api_key"
export ALMANAC_API_KEY="your_api_key"
export GLM4_API_KEY="your_api_key"
export LIFE_SUGGESTION_API_KEY="your_api_key"
export DEEPSEEK_API_KEY="your_api_key"
export HOLIDAY_API_KEY="your_api_key"

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 生产环境部署

### 1. 服务器准备

```bash
# 创建应用目录
sudo mkdir -p /opt/wecom-kf
sudo mkdir -p /opt/wecom-kf/data
sudo mkdir -p /opt/wecom-kf/logs

# 设置权限
sudo chown -R $USER:$USER /opt/wecom-kf
```

### 2. 上传文件

```bash
# 上传项目文件到服务器
scp -r . user@server:/opt/wecom-kf/

# 或使用git克隆
git clone <repository_url> /opt/wecom-kf
cd /opt/wecom-kf
```

### 3. 配置环境

```bash
cd /opt/wecom-kf

# 复制并编辑配置文件
cp env.example .env
vim .env

# 验证配置
python validate_config.py
```

### 4. 部署服务

```bash
# 构建镜像
docker build -t wecom-kf:latest .

# 启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps
docker-compose logs -f
```

### 5. 设置开机自启

```bash
# 启用Docker服务开机自启
sudo systemctl enable docker

# 使用Docker Compose的restart策略
# 在docker-compose.yml中已设置 restart: always
```

## 监控和维护

### 1. 查看日志

```bash
# Docker日志
docker logs wecom-kf-app -f

# 应用日志
tail -f /opt/wecom-kf/logs/access.log

# Docker Compose日志
docker-compose logs -f
```

### 2. 健康检查

```bash
# 检查服务状态
curl http://localhost:8090/api/daily_advice

# 检查容器状态
docker ps | grep wecom-kf
```

### 3. 备份数据

```bash
# 备份数据库文件
cp -r /opt/wecom-kf/data /backup/wecom-kf-$(date +%Y%m%d)

# 备份日志
cp -r /opt/wecom-kf/logs /backup/wecom-kf-logs-$(date +%Y%m%d)
```

### 4. 更新服务

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 故障排除

### 常见问题

1. **配置验证失败**
   - 检查 `.env` 文件是否存在
   - 确认所有必需的配置项都已设置
   - 运行 `python validate_config.py` 查看详细错误

2. **服务无法启动**
   - 检查端口是否被占用：`netstat -tlnp | grep 8090`
   - 查看Docker日志：`docker logs wecom-kf-app`
   - 检查配置文件格式是否正确

3. **API调用失败**
   - 验证API密钥是否正确
   - 检查网络连接
   - 查看应用日志中的错误信息

4. **数据库连接问题**
   - 确认数据库文件权限正确
   - 检查磁盘空间是否充足
   - 验证数据库文件是否损坏

### 日志分析

```bash
# 查看错误日志
grep ERROR /opt/wecom-kf/logs/access.log

# 查看最近的请求
tail -100 /opt/wecom-kf/logs/access.log

# 统计请求数量
grep "Request:" /opt/wecom-kf/logs/access.log | wc -l
```
