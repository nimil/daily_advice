# 每日建议服务

一个基于Flask的每日建议服务，提供节气养生、老黄历、天气等信息，支持JSON和HTML格式输出。

## 配置说明

### 环境变量配置

项目使用环境变量来管理敏感信息。请按照以下步骤配置：

1. **复制配置模板**：
   ```bash
   cp env.example .env
   ```

2. **编辑配置文件**：
   在 `.env` 文件中填入正确的配置值：
   ```bash
   # 企业微信配置
   CORP_ID=your_corp_id_here
   CORP_SECRET=your_corp_secret_here
   OPEN_KFID=your_open_kfid_here
   EXTERNAL_USERID=your_external_userid_here
   
   # API密钥配置
   SOLAR_TERMS_API_KEY=your_solar_terms_api_key_here
   ALMANAC_API_KEY=your_almanac_api_key_here
   GLM4_API_KEY=your_glm4_api_key_here
   LIFE_SUGGESTION_API_KEY=your_life_suggestion_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   HOLIDAY_API_KEY=your_holiday_api_key_here
   ```

3. **验证配置**：
   ```bash
   python validate_config.py
   ```

### 安全注意事项

- ⚠️ **不要将 `.env` 文件提交到版本控制系统**
- ⚠️ **不要将API密钥硬编码在代码中**
- ✅ **使用环境变量或配置文件管理敏感信息**
- ✅ **定期轮换API密钥**

## 功能特性

- 🌤️ 实时天气信息查询
- 📅 老黄历宜忌查询
- 🌿 节气养生建议
- 🍽️ 时令饮食建议
- 📧 HTML邮件格式支持
- 🔄 自动缓存机制
- ⏰ 定时任务调度

## Docker 部署

### macOS 本地构建

在macOS上构建镜像并打包：

```bash
# 构建镜像（指定linux/amd64平台）
docker build --platform linux/amd64 -t wecom-kf:latest .

# 保存镜像为tar文件
docker save -o wecom-kf.tar wecom-kf:latest

# 查看生成的tar文件大小
ls -lh wecom-kf.tar
```

### Linux 服务器部署

将tar文件上传到Linux服务器后：

```bash
# 加载镜像
docker load -i wecom-kf.tar

# 运行容器
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  -e SOLAR_TERMS_API_KEY="your_api_key" \
  -e ALMANAC_API_KEY="your_api_key" \
  -e GLM4_API_KEY="your_api_key" \
  -e DEEPSEEK_API_KEY="your_api_key" \
  -e LIFE_SUGGESTION_API_KEY="your_api_key" \
  -v /path/to/data:/app/data \
  -v /path/to/logs:/app/logs \
  wecom-kf:latest

# 查看容器状态
docker ps

# 查看容器日志
docker logs wecom-kf-app

# 停止容器
docker stop wecom-kf-app

# 删除容器
docker rm wecom-kf-app
```

### 一键部署脚本

创建 `deploy.sh` 脚本：

```bash
#!/bin/bash

# 部署脚本
echo "开始部署每日建议服务..."

# 停止并删除旧容器
docker stop wecom-kf-app 2>/dev/null || true
docker rm wecom-kf-app 2>/dev/null || true

# 加载镜像
echo "加载Docker镜像..."
docker load -i wecom-kf.tar

# 运行新容器
echo "启动容器..."
docker run -d \
  --name wecom-kf-app \
  -p 8090:8090 \
  -e SOLAR_TERMS_API_KEY="${SOLAR_TERMS_API_KEY}" \
  -e ALMANAC_API_KEY="${ALMANAC_API_KEY}" \
  -e GLM4_API_KEY="${GLM4_API_KEY}" \
  -e DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}" \
  -e LIFE_SUGGESTION_API_KEY="${LIFE_SUGGESTION_API_KEY}" \
  -v /opt/wecom-kf/data:/app/data \
  -v /opt/wecom-kf/logs:/app/logs \
  --restart unless-stopped \
  wecom-kf:latest

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
if curl -f http://localhost:8090/api/daily_advice >/dev/null 2>&1; then
    echo "✅ 服务部署成功！"
    echo "访问地址: http://localhost:8090"
else
    echo "❌ 服务启动失败，请检查日志"
    docker logs wecom-kf-app
fi
```

## API 接口

### 基础接口

| 接口 | 方法 | 描述 | 返回格式 |
|------|------|------|----------|
| `/api/daily_advice` | GET | 获取每日建议 | JSON |
| `/api/daily_advice_html` | GET | 获取每日建议HTML | HTML |
| `/api/weather` | GET | 获取天气信息 | JSON |
| `/api/food_advice` | GET | 获取饮食建议 | JSON |
| `/api/almanac` | GET | 获取老黄历信息 | JSON |

### 使用示例

```bash
# 获取每日建议 (JSON)
curl http://localhost:8090/api/daily_advice

# 获取每日建议 (HTML)
curl http://localhost:8090/api/daily_advice_html

# 获取天气信息
curl http://localhost:8090/api/weather

# 获取饮食建议
curl "http://localhost:8090/api/food_advice?province=山东&term=立秋"
```

## 环境变量配置

在Linux服务器上设置环境变量：

```bash
# 编辑环境变量文件
sudo nano /etc/environment

# 添加以下内容
SOLAR_TERMS_API_KEY=your_api_key
ALMANAC_API_KEY=your_api_key
GLM4_API_KEY=your_api_key
DEEPSEEK_API_KEY=your_api_key
LIFE_SUGGESTION_API_KEY=your_api_key

# 重新加载环境变量
source /etc/environment
```

## 数据持久化

创建数据目录：

```bash
# 创建数据目录
sudo mkdir -p /opt/wecom-kf/data
sudo mkdir -p /opt/wecom-kf/logs

# 设置权限
sudo chown -R 1000:1000 /opt/wecom-kf
sudo chmod -R 755 /opt/wecom-kf
```

## 监控和维护

### 查看服务状态

```bash
# 查看容器状态
docker ps -a | grep wecom-kf

# 查看资源使用情况
docker stats wecom-kf-app

# 查看日志
docker logs -f wecom-kf-app

# 查看日志文件
tail -f /opt/wecom-kf/logs/access.log
```

### 备份和恢复

```bash
# 备份数据
tar -czf wecom-kf-backup-$(date +%Y%m%d).tar.gz /opt/wecom-kf/data

# 备份镜像
docker save -o wecom-kf-backup-$(date +%Y%m%d).tar wecom-kf:latest
```

### 更新服务

```bash
# 停止服务
docker stop wecom-kf-app

# 备份当前镜像
docker tag wecom-kf:latest wecom-kf:backup-$(date +%Y%m%d)

# 加载新镜像
docker load -i wecom-kf-new.tar

# 重新部署
./deploy.sh
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看详细错误信息
   docker logs wecom-kf-app
   
   # 检查端口占用
   netstat -tlnp | grep 8090
   ```

2. **API密钥错误**
   ```bash
   # 检查环境变量
   docker exec wecom-kf-app env | grep API_KEY
   ```

3. **数据目录权限问题**
   ```bash
   # 修复权限
   sudo chown -R 1000:1000 /opt/wecom-kf
   ```

### 性能优化

```bash
# 限制容器资源使用
docker run -d \
  --name wecom-kf-app \
  --memory=512m \
  --cpus=1.0 \
  -p 8090:8090 \
  wecom-kf:latest
```

## 注意事项

1. **平台兼容性**: 使用 `--platform linux/amd64` 确保在macOS上构建的镜像能在Linux服务器上运行
2. **数据持久化**: 使用卷挂载确保数据不丢失
3. **环境变量**: 确保所有必要的API密钥都已正确配置
4. **网络配置**: 确保8090端口在防火墙中开放
5. **日志管理**: 定期清理日志文件避免磁盘空间不足

---

**部署流程总结**:
1. macOS构建: `docker build --platform linux/amd64 -t wecom-kf:latest .`
2. 打包镜像: `docker save -o wecom-kf.tar wecom-kf:latest`
3. 上传到Linux服务器
4. Linux加载: `docker load -i wecom-kf.tar`
5. 运行容器: `docker run -d --name wecom-kf-app -p 8090:8090 wecom-kf:latest`
