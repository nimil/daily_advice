# 使用Python官方镜像作为基础镜像，指定平台为 linux/amd64
FROM --platform=linux/amd64 python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs && chmod 777 logs
# 暴露端口
EXPOSE 8090

# 启动应用
CMD ["python", "app.py"] 