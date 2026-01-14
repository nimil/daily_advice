# 使用Python官方镜像作为基础镜像，指定平台为 linux/amd64
FROM alibaba-cloud-linux-3-registry.cn-hangzhou.cr.aliyuncs.com/alinux3/python:3.11.1
# 设置时区为北京时间
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
# 安装依赖
RUN pip install -r requirements.txt

# 复制应用代码（排除敏感文件）
COPY . .

# 删除敏感文件（如果存在）
RUN rm -f .env .env.local .env.production .env.staging

# 创建日志目录
RUN mkdir -p logs && chmod 777 logs
# 暴露端口
EXPOSE 8090

# 启动应用
CMD ["python", "app.py"] 