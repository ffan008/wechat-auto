#!/bin/bash

# 快速启动和测试脚本

set -e

echo "╔═════════════════════════════════════════╗"
echo "║  WeChat Auto - 快速启动                 ║"
echo "╚═════════════════════════════════════════╝"
echo ""

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ 未找到.env文件"
    echo "请先运行: ./install.sh"
    exit 1
fi

# 启动Docker服务
echo "🐳 启动Docker服务..."
docker-compose up -d postgres redis

echo "⏳ 等待数据库启动..."
sleep 5

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 基础服务已启动"
echo ""
echo "🚀 启动应用:"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "🐳 或使用Docker:"
echo "   docker-compose up -d"
echo ""
echo "📖 查看日志:"
echo "   docker-compose logs -f api"
echo ""
echo "🧪 测试连接:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/api/wechat/test"
