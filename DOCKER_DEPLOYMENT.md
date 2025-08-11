# Docker部署详细说明

## 环境变量处理方式

### 1. 构建时 vs 运行时

**重要概念**：
- **构建时（Build Time）**：Docker镜像构建过程中
- **运行时（Runtime）**：容器启动和运行过程中

### 2. 当前配置说明

#### .env文件不会被自动打包到镜像中

**原因**：
1. `.dockerignore` 文件排除了 `.env` 文件
2. Dockerfile中明确删除了敏感文件
3. 这是安全最佳实践

**优势**：
- ✅ 敏感信息不会永久写入镜像
- ✅ 可以为不同环境使用不同配置
- ✅ 支持动态密钥管理

## 部署方式

### 方式1：使用环境变量（推荐）

```bash
# 构建镜像
docker build -t wecom-kf:latest .

# 运行容器（使用环境变量）
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  -e CORP_ID="ww8d0bc98c6b966cf4" \
  -e CORP_SECRET="Pw_w55Hntaij1rVTy7HFrl1fV__PuJis3J1L_PpHxMk" \
  -e OPEN_KFID="wkKQtxcgAAEXTp-hZClvh9MGzFu92U_A" \
  -e EXTERNAL_USERID="wmKQtxcgAAnCwRlXcu2VynAeNNIc334g" \
  -e SOLAR_TERMS_API_KEY="5b71ee4243a804d6601641093d8a4cbe" \
  -e ALMANAC_API_KEY="68c8a6c0be8e9cd53cd92235fb99b287" \
  -e GLM4_API_KEY="8d783a649af942118b12a6f0ea324cec.7qjKtcWVy09w7wY4" \
  -e LIFE_SUGGESTION_API_KEY="SEuAOXtlQ5l9R7URP" \
  -e DEEPSEEK_API_KEY="sk-wjUom5rvhLqk6P4bnyddnHe1HQ05brJhSVxfTzlAzb7BhAhm" \
  -e HOLIDAY_API_KEY="1a14f196bfb12cb84b609a8272f750d4" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  wecom-kf:latest
```

### 方式2：使用环境文件

```bash
# 构建镜像
docker build -t wecom-kf:latest .

# 运行容器（使用环境文件）
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  wecom-kf:latest
```

### 方式3：使用Docker Compose（推荐）

```bash
# 设置环境变量
export CORP_ID="ww8d0bc98c6b966cf4"
export CORP_SECRET="Pw_w55Hntaij1rVTy7HFrl1fV__PuJis3J1L_PpHxMk"
export OPEN_KFID="wkKQtxcgAAEXTp-hZClvh9MGzFu92U_A"
export EXTERNAL_USERID="wmKQtxcgAAnCwRlXcu2VynAeNNIc334g"
export SOLAR_TERMS_API_KEY="5b71ee4243a804d6601641093d8a4cbe"
export ALMANAC_API_KEY="68c8a6c0be8e9cd53cd92235fb99b287"
export GLM4_API_KEY="8d783a649af942118b12a6f0ea324cec.7qjKtcWVy09w7wY4"
export LIFE_SUGGESTION_API_KEY="SEuAOXtlQ5l9R7URP"
export DEEPSEEK_API_KEY="sk-wjUom5rvhLqk6P4bnyddnHe1HQ05brJhSVxfTzlAzb7BhAhm"
export HOLIDAY_API_KEY="1a14f196bfb12cb84b609a8272f750d4"

# 启动服务
docker-compose up -d
```

## 生产环境部署

### 1. 服务器部署脚本

创建 `deploy.sh` 脚本：

```bash
#!/bin/bash

# 部署脚本
echo "开始部署每日建议服务..."

# 停止并删除旧容器
docker stop wecom-kf-app 2>/dev/null || true
docker rm wecom-kf-app 2>/dev/null || true

# 构建镜像
echo "构建Docker镜像..."
docker build -t wecom-kf:latest .

# 运行新容器
echo "启动容器..."
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  -e CORP_ID="${CORP_ID}" \
  -e CORP_SECRET="${CORP_SECRET}" \
  -e OPEN_KFID="${OPEN_KFID}" \
  -e EXTERNAL_USERID="${EXTERNAL_USERID}" \
  -e SOLAR_TERMS_API_KEY="${SOLAR_TERMS_API_KEY}" \
  -e ALMANAC_API_KEY="${ALMANAC_API_KEY}" \
  -e GLM4_API_KEY="${GLM4_API_KEY}" \
  -e LIFE_SUGGESTION_API_KEY="${LIFE_SUGGESTION_API_KEY}" \
  -e DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}" \
  -e HOLIDAY_API_KEY="${HOLIDAY_API_KEY}" \
  -v /opt/wecom-kf/data:/app/data \
  -v /opt/wecom-kf/logs:/app/logs \
  --restart unless-stopped \
  wecom-kf:latest

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
if curl -f http://localhost:8090/api/daily_advice > /dev/null 2>&1; then
    echo "✅ 服务启动成功！"
else
    echo "❌ 服务启动失败，请检查日志"
    docker logs wecom-kf-app
fi
```

## 验证部署

### 1. 检查容器状态
```bash
# 查看容器状态
docker ps | grep wecom-kf

# 查看容器日志
docker logs wecom-kf-app -f
```

### 2. 测试API接口
```bash
# 测试健康检查
curl http://localhost:8090/api/daily_advice

# 测试其他接口
curl http://localhost:8090/api/weather
curl http://localhost:8090/api/almanac
```

### 3. 检查环境变量
```bash
# 查看容器中的环境变量
docker exec wecom-kf-app env | grep -E "(CORP_|API_KEY)"

# 进入容器检查
docker exec -it wecom-kf-app bash
```

## 安全最佳实践

### 1. 密钥管理
- ✅ 使用环境变量而不是硬编码
- ✅ 使用密钥管理服务（AWS Secrets Manager、Azure Key Vault等）
- ✅ 定期轮换密钥
- ✅ 限制密钥访问权限

### 2. 镜像安全
- ✅ 不将敏感信息写入镜像
- ✅ 使用多阶段构建
- ✅ 定期更新基础镜像
- ✅ 扫描镜像漏洞

### 3. 运行时安全
- ✅ 使用非root用户运行容器
- ✅ 限制容器权限
- ✅ 使用只读文件系统
- ✅ 监控容器行为

## 故障排除

### 1. 环境变量未生效
```bash
# 检查环境变量是否正确传递
docker exec wecom-kf-app env | grep CORP_ID

# 检查应用日志
docker logs wecom-kf-app | grep -i error
```

### 2. 配置验证失败
```bash
# 进入容器验证配置
docker exec -it wecom-kf-app python validate_config.py

# 检查配置文件
docker exec wecom-kf-app cat /app/config.py
```

### 3. 网络连接问题
```bash
# 检查端口映射
docker port wecom-kf-app

# 检查网络配置
docker network inspect bridge
```

## 总结

- **`.env` 文件不会被自动打包到Docker镜像中**
- **推荐使用环境变量或密钥管理服务**
- **确保敏感信息的安全性**
- **支持不同环境的配置隔离**
