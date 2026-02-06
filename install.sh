#!/bin/bash

# 微信公众号自动运营系统 - 安装脚本

set -e

echo "╔═════════════════════════════════════════╗"
echo "║  WeChat Auto Operation System           ║"
echo "║  安装脚本                                ║"
echo "╚═════════════════════════════════════════╝"
echo ""

# 检查Python版本
echo "📦 检查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "✅ 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建.env文件
if [ ! -f ".env" ]; then
    echo "📝 创建.env配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑.env文件，填入您的API密钥和配置"
    echo "   必填项："
    echo "   - ANTHROPIC_API_KEY (Claude API密钥)"
    echo "   - WECHAT_APP_ID (微信公众号AppID)"
    echo "   - WECHAT_APP_SECRET (微信公众号AppSecret)"
    echo "   - WECHAT_TOKEN (微信Token)"
    echo "   - WECHAT_ENCODING_AES_KEY (微信加密密钥)"
fi

# 创建输出目录
echo "📁 创建输出目录..."
mkdir -p output/{drafts,published,media,reports}
mkdir -p logs

# 初始化数据库
echo "🗄️  初始化数据库..."
echo "⚠️  请确保PostgreSQL已安装并运行"
echo "   默认连接: postgresql://wechat_user:password@localhost:5432/wechat_auto"
echo "   如需修改，请编辑.env文件中的DATABASE_URL"

# 检查Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker已安装"
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose已安装"
        echo ""
        echo "🐳 使用Docker启动："
        echo "   docker-compose up -d"
    else
        echo "⚠️  Docker Compose未安装"
    fi
else
    echo "⚠️  Docker未安装（可选）"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "🚀 启动方式："
echo "   方式1（本地开发）:"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "   方式2（Docker）:"
echo "   docker-compose up -d"
echo ""
echo "📚 更多信息请查看README.md"
