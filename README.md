# 智能新闻汇总服务

一个基于Flask的智能新闻汇总服务，集成多个新闻源，使用AI进行新闻整合、去重和分类，支持飞书机器人推送和HTML格式展示。

## 功能特性

### 📰 新闻功能
- 🔄 **多源新闻整合**：支持金十数据、财联社、华尔街见闻等多个新闻源
- 🤖 **AI智能处理**：使用GLM4进行新闻去重、分类和影响分析
- 📊 **影响分析**：自动分析新闻对经济的影响（正向/负向）
- 📱 **飞书推送**：支持富文本和交互式消息格式
- 🌐 **HTML展示**：生成美观的HTML新闻页面
- ⏰ **定时推送**：支持定时发送新闻汇总

### 🕐 时间管理
- 🌍 **时区统一**：统一使用北京时间（Asia/Shanghai）
- 📅 **定时任务**：支持自定义时间发送新闻
- 🔄 **自动调度**：基于APScheduler的任务调度

### 🏗️ 技术特性
- 🐳 **Docker部署**：完整的容器化部署方案
- 📝 **日志管理**：详细的日志记录和监控
- 🔧 **配置管理**：环境变量配置，安全可靠
- 📊 **性能监控**：接口性能统计和分析

## 快速开始

### 环境要求
- Python 3.8+
- Docker & Docker Compose
- 相关API密钥（GLM4、飞书等）

### 1. 克隆项目
```bash
git clone <repository-url>
cd wecometest
```

### 2. 配置环境变量
```bash
# 复制配置模板
cp env.example .env

# 编辑配置文件，填入必要的API密钥
vim .env
```

### 3. 使用Docker部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 配置说明

### 环境变量配置

项目使用环境变量管理配置，主要包含：

```bash
# 飞书机器人配置
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_CHAT_ID=your_chat_id

# AI服务配置
GLM4_API_KEY=your_glm4_api_key

# 其他服务配置
SOLAR_TERMS_API_KEY=your_api_key
ALMANAC_API_KEY=your_api_key
LIFE_SUGGESTION_API_KEY=your_api_key
DEEPSEEK_API_KEY=your_api_key
HOLIDAY_API_KEY=your_api_key
```

### 安全注意事项
- ⚠️ **不要将 `.env` 文件提交到版本控制系统**
- ⚠️ **不要将API密钥硬编码在代码中**
- ✅ **使用环境变量管理敏感信息**
- ✅ **定期轮换API密钥**

## API 接口

### 新闻相关接口

| 接口 | 方法 | 描述 | 返回格式 |
|------|------|------|----------|
| `/news/integrated` | GET | 获取整合后的新闻数据 | JSON |
| `/news/html` | GET | 获取新闻HTML页面 | HTML |
| `/news/feishu/test` | POST | 测试飞书新闻推送 | JSON |
| `/news/sources` | GET | 获取支持的新闻源 | JSON |
| `/news/health` | GET | 新闻服务健康检查 | JSON |

### 其他功能接口

| 接口 | 方法 | 描述 | 返回格式 |
|------|------|------|----------|
| `/api/daily_advice` | GET | 获取每日建议 | JSON |
| `/api/daily_advice_html` | GET | 获取每日建议HTML | HTML |
| `/api/weather` | GET | 获取天气信息 | JSON |
| `/api/food_advice` | GET | 获取饮食建议 | JSON |
| `/api/almanac` | GET | 获取老黄历信息 | JSON |

### 使用示例

```bash
# 获取整合新闻数据
curl http://localhost:8090/news/integrated

# 获取新闻HTML页面
curl http://localhost:8090/news/html

# 测试飞书推送
curl -X POST http://localhost:8090/news/feishu/test \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"your_chat_id"}'

# 获取每日建议
curl http://localhost:8090/api/daily_advice
```

## 定时任务

### 配置说明
服务支持定时发送新闻汇总，默认配置：

- **早上10:00** - 发送早间新闻汇总
- **下午14:30** - 发送午间新闻汇总
- **每小时第10分钟** - 刷新缓存数据

### 自定义配置
可以通过修改 `scheduler.py` 中的CronTrigger来调整执行时间：

```python
# 示例：修改为早上8点和下午1点半
scheduler.add_job(
    func=send_daily_news_to_feishu,
    trigger=CronTrigger(hour='8', minute='0'),
    id='send_daily_news_to_feishu_morning',
    name='发送每日新闻到飞书（早8点）',
    replace_existing=True
)
```

## Docker 部署

### 本地开发
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f wecom-kf
```

### 生产部署
```bash
# 构建生产镜像
docker build --platform linux/amd64 -t wecom-kf:latest .

# 保存镜像
docker save -o wecom-kf.tar wecom-kf:latest

# 在服务器上加载镜像
docker load -i wecom-kf.tar

# 运行容器
docker run -d \
  --name wecom-kf \
  -p 8090:8090 \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  wecom-kf:latest
```

### 一键部署脚本
```bash
#!/bin/bash
# deploy.sh

echo "开始部署智能新闻汇总服务..."

# 停止旧容器
docker stop wecom-kf 2>/dev/null || true
docker rm wecom-kf 2>/dev/null || true

# 加载镜像
docker load -i wecom-kf.tar

# 启动新容器
docker run -d \
  --name wecom-kf \
  -p 8090:8090 \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  wecom-kf:latest

echo "✅ 服务部署完成！"
echo "访问地址: http://localhost:8090"
```

## 监控和维护

### 查看服务状态
```bash
# 查看容器状态
docker ps -a | grep wecom-kf

# 查看资源使用
docker stats wecom-kf

# 查看实时日志
docker logs -f wecom-kf

# 查看应用日志
tail -f logs/access.log
```

### 健康检查
```bash
# 检查新闻服务健康状态
curl http://localhost:8090/news/health

# 检查整体服务状态
curl http://localhost:8090/api/daily_advice
```

### 备份和恢复
```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# 备份镜像
docker save -o wecom-kf-backup-$(date +%Y%m%d).tar wecom-kf:latest
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看详细错误
   docker logs wecom-kf
   
   # 检查端口占用
   netstat -tlnp | grep 8090
   ```

2. **API密钥错误**
   ```bash
   # 检查环境变量
   docker exec wecom-kf env | grep API_KEY
   ```

3. **时区问题**
   ```bash
   # 检查容器时区
   docker exec wecom-kf date
   docker exec wecom-kf cat /etc/timezone
   ```

4. **飞书推送失败**
   ```bash
   # 检查飞书配置
   docker exec wecom-kf env | grep FEISHU
   
   # 测试飞书推送
   curl -X POST http://localhost:8090/news/feishu/test \
     -H "Content-Type: application/json" \
     -d '{"chat_id":"your_chat_id"}'
   ```

### 性能优化

```bash
# 限制容器资源
docker run -d \
  --name wecom-kf \
  --memory=1g \
  --cpus=1.0 \
  -p 8090:8090 \
  wecom-kf:latest
```

## 项目结构

```
wecometest/
├── app.py                 # 主应用入口
├── app_context.py         # 应用上下文
├── config.py             # 配置管理
├── scheduler.py          # 定时任务调度
├── feishu_bot.py         # 飞书机器人
├── news_integration_api.py # 新闻整合API
├── glm4_query.py         # GLM4 AI查询
├── solar_terms_api.py    # 节气API
├── almanac_query.py      # 老黄历查询
├── holiday_query.py      # 节假日查询
├── life_suggestion_query.py # 生活建议查询
├── deepseek_query.py     # DeepSeek查询
├── requirements.txt      # Python依赖
├── Dockerfile           # Docker镜像配置
├── docker-compose.yml   # Docker编排配置
├── env.example          # 环境变量模板
├── data/               # 数据目录
├── logs/               # 日志目录
└── README.md           # 项目说明
```

## 开发指南

### 本地开发环境
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python app.py
```

### 代码规范
- 使用Python 3.8+
- 遵循PEP 8代码规范
- 添加适当的注释和文档
- 使用类型提示

## 更新日志

### v1.0.0
- ✅ 多源新闻整合功能
- ✅ AI智能新闻处理
- ✅ 飞书机器人推送
- ✅ HTML新闻页面
- ✅ 定时任务调度
- ✅ Docker容器化部署
- ✅ 时区统一配置
- ✅ 性能监控功能

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 项目讨论区

---

**感谢使用智能新闻汇总服务！** 🚀
