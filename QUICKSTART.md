# 快速开始指南

## 🎯 系统概述

本系统是一个基于AI Agent的微信公众号自动运营系统，实现了：

1. **智能对话** - AI自动回复用户消息
2. **内容生成** - 自动生成公众号文章
3. **数据分析** - 自动采集和分析运营数据
4. **定时发布** - 自动调度和发布内容

## 📋 前置要求

- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- Claude API密钥
- 微信公众号（服务号或订阅号）

## 🚀 快速开始（5分钟）

### 步骤1：安装依赖

```bash
cd wechat-auto
./install.sh
```

### 步骤2：配置环境变量

编辑 `.env` 文件，填入以下信息：

```bash
# 必填项
ANTHROPIC_API_KEY=sk-ant-xxx          # Claude API密钥
WECHAT_APP_ID=wx1234567890abcdef      # 微信AppID
WECHAT_APP_SECRET=xxx                 # 微信AppSecret
WECHAT_TOKEN=mytoken                  # 自定义Token
WECHAT_ENCODING_AES_KEY=xxx           # 微信加密密钥

# 数据库（使用Docker可保持默认）
DATABASE_URL=postgresql://wechat_user:wechat_password@localhost:5432/wechat_auto
REDIS_URL=redis://localhost:6379/0
```

**获取微信配置：**
1. 登录微信公众平台：https://mp.weixin.qq.com
2. 进入"开发 → 基本配置"
3. 复制 AppID 和 AppSecret
4. 设置 Token（任意字符串，自己定义即可）
5. 点击"生成"按钮获取 EncodingAESKey

### 步骤3：启动服务

**方式A：使用Docker（推荐）**

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

**方式B：本地开发**

```bash
# 启动数据库（Docker）
docker-compose up -d postgres redis

# 激活虚拟环境
source venv/bin/activate

# 启动API服务
python run.py

# 另一个终端启动Celery
celery -A src.tasks.celery_app worker --loglevel=info
```

### 步骤4：配置微信服务器URL

1. 确保你的服务器有公网IP或使用内网穿透（如ngrok）
2. 启动ngrok（本地测试）：
   ```bash
   ngrok http 8000
   ```
3. 复制ngrok提供的HTTPS URL（如：https://abc123.ngrok.io）
4. 在微信后台的"服务器配置"中：
   - URL: `https://abc123.ngrok.io/api/wechat/webhook`
   - Token: 与.env中一致
   - EncodingAESKey: 与.env中一致
5. 点击"提交"，验证成功后即可

### 步骤5：测试系统

```bash
# 测试API
curl http://localhost:8000/health

# 测试微信连接
curl http://localhost:8000/api/wechat/test

# 运行系统测试
python test_system.py
```

## 💬 使用场景示例

### 场景1：用户对话

用户发送消息："你好"
```
系统回复：欢迎关注我们的公众号！🎉
我是AI助手，可以帮您：
• 回答问题和咨询
• 提供产品信息
• 生成内容（如果需要）
• 查看数据分析
```

### 场景2：生成文章

用户发送："帮我写一篇关于AI的文章"
```
系统回复：
内容已生成！📝

主题：AI

标题选项：
1. AI正在改变我们的生活方式
2. 揭秘AI：从原理到应用
3. 为什么现在必须学习AI？
4. AI工具推荐：提升效率的秘密武器
5. AI时代：普通人如何抓住机遇

摘要：AI生成的文章大纲...

内容已保存为草稿（ID: 1）。您可以预览、编辑或调度发布。
```

### 场景3：查看数据

用户发送："查看本周数据"
```
系统回复：
数据分析报告 📊

核心指标：
- Total Views: 5000
- Total Likes: 300
- Engagement Rate: 8.5%

关键洞察：
• 文章阅读量相比上周增长15%
• 用户互动率保持在较高水平
• 周三发布的内容表现最佳
• 建议增加视频内容以提升互动
```

### 场景4：定时发布

用户发送："把草稿1定在明天晚上8点发布"
```
系统回复：
内容发布已调度！✅

内容ID: 1
发布时间: 2025-01-15 20:00

系统将在指定时间自动发布。您可以随时取消或修改。
```

## 📊 监控和管理

### Flower监控

访问 http://localhost:5555 查看Celery任务状态

### 日志查看

```bash
# API日志
tail -f logs/api.log

# Celery日志
docker-compose logs -f celery_worker
```

### 数据库管理

```bash
# 连接数据库
docker exec -it wechat_postgres psql -U wechat_user -d wechat_auto

# 查看用户
SELECT * FROM users;

# 查看内容
SELECT * FROM content;
```

## 🔧 常见问题

### Q: 微信验证失败？

A: 检查以下几项：
1. .env中的WECHAT_TOKEN与微信后台是否一致
2. 服务器URL是否可以访问（使用curl测试）
3. 服务器端口是否开放（8000端口）

### Q: Claude API调用失败？

A: 检查以下几项：
1. ANTHROPIC_API_KEY是否正确
2. API账户是否有余额
3. 网络是否能访问anthropic.com

### Q: 数据库连接失败？

A: 检查以下几项：
1. PostgreSQL是否正在运行
2. DATABASE_URL格式是否正确
3. 数据库用户和密码是否正确

### Q: Celery任务不执行？

A: 检查以下几项：
1. Redis是否正在运行
2. Celery Worker是否启动
3. 使用Flower查看任务状态

## 📚 进阶配置

### 自定义AI提示词

编辑 `config/prompts.yaml`，修改内容生成、对话回复等提示词。

### 添加FAQ知识库

```python
from src.database.crud import FAQCRUD
from src.database.session import db_manager

with db_manager.get_session() as db:
    FAQCRUD.create_faq(
        db,
        question="如何退款？",
        answer="您可以在订单页面申请退款...",
        category="售后",
        keywords=["退款", "退货", "取消订单"]
    )
```

### 自定义定时任务

编辑 `src/tasks/celery_app.py`，添加新的定时任务。

### 修改Agent路由

编辑 `src/agents/coordinator_agent.py`，修改agent_registry。

## 🎓 下一步

- 查看 README.md 了解完整文档
- 查看 test_system.py 了解系统测试
- 查看 src/ 目录了解代码结构
- 查看 config/ 目录了解配置选项

## 🆘 获取帮助

- GitHub Issues
- 邮件支持
- 在线文档

---

**祝你使用愉快！** 🎉
