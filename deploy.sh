#!/bin/bash

# 部署脚本 - 用于部署微信客服应用
# 使用方法: ./deploy.sh

set -e  # 遇到错误立即退出

echo "🚀 开始部署微信客服应用..."

# 检查文件是否存在
if [ ! -f "/home/lighthouse/wecom-kf.tar" ]; then
    echo "❌ 错误: 找不到 /home/lighthouse/wecom-kf.tar 文件"
    exit 1
fi

echo "📦 移动Docker镜像文件..."
mv /home/lighthouse/wecom-kf.tar ./

echo "🐳 加载Docker镜像..."
docker load -i wecom-kf.tar

echo "🚀 启动Docker容器..."
docker-compose up -d

echo "✅ 部署完成！"
echo "📊 查看容器状态: docker-compose ps"
echo "📋 查看日志: docker-compose logs -f"
