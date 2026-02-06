# 微信公众号自动运营系统

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker)](https://www.docker.com/)
[![Claude AI](https://img.shields.io/badge/Claude%20AI-3.5%20Sonnet-purple.svg)](https://www.anthropic.com/claude)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agents-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

基于 AI Agent 的微信公众号全流程自动化运营系统，实现内容生成、粉丝互动、数据分析等核心功能。

## ✨ 核心特性

### 🤖 多Agent协作
- **Coordinator Agent** - 主控路由，意图识别
- **Chat Agent** - 智能对话，FAQ匹配
- **Content Agent** - AI内容生成
- **Analytics Agent** - 数据分析，洞察生成
- **Scheduler Agent** - 定时任务，内容调度

### 📝 AI内容生成
- Claude 3.5 Sonnet 驱动的高质量内容生成
- 自动生成大纲、正文、标题
- A/B测试标题优化
- 内容质量检测

### 💬 智能对话
- 实时意图识别
- FAQ知识库匹配
- 多轮对话上下文记忆
- 用户画像自动更新

### 📊 数据分析
- 自动采集微信数据
- KPI指标计算
- AI生成洞察报告
- 用户画像构建

### ⏰ 自动化运营
- 定时发布内容
- 每日数据报告
- 热点话题监控
- 用户互动统计

## 🏗️ 技术架构

```
微信消息 → Webhook → Coordinator Agent → 路由到相应Agent
                                      ↓
                              Chat / Content / Analytics
                                      ↓
                            Claude AI + PostgreSQL + Redis
                                      ↓
                              生成响应 → 返回微信
```

### 技术栈
- **语言**: Python 3.10+
- **Agent框架**: LangGraph
- **AI模型**: Claude 3.5 Sonnet (Anthropic)
- **Web框架**: FastAPI
- **数据库**: PostgreSQL + Redis
- **任务队列**: Celery
- **微信SDK**: WeChatPy
- **部署**: Docker Compose

## 📦 安装部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat-auto
```

### 2. 安装依赖

```bash
# 运行安装脚本
./install.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并填入配置：

```bash
cp .env.example .env
```

必填配置：
```bash
# 数据库
DATABASE_URL=postgresql://wechat_user:password@localhost:5432/wechat_auto

# Redis
REDIS_URL=redis://localhost:6379/0

# Claude API
ANTHROPIC_API_KEY=sk-ant-your-key

# 微信公众号
WECHAT_APP_ID=your-app-id
WECHAT_APP_SECRET=your-app-secret
WECHAT_TOKEN=your-token
WECHAT_ENCODING_AES_KEY=your-key

# 安全
SECRET_KEY=your-secret-key
```

### 4. 初始化数据库

```bash
# 使用Docker（推荐）
docker-compose up postgres redis -d

# 或使用本地PostgreSQL
createdb wechat_auto
```

### 5. 启动服务

**方式1: Docker Compose（推荐）**
```bash
docker-compose up -d
```

**方式2: 本地开发**
```bash
# 启动API服务
python run.py

# 启动Celery Worker
celery -A src.tasks.celery_app worker --loglevel=info

# 启动Celery Beat
celery -A src.tasks.celery_app beat --loglevel=info
```

### 6. 配置微信公众号

1. 登录微信公众平台
2. 进入"开发 → 基本配置"
3. 服务器地址填写: `https://your-domain.com/api/wechat/webhook`
4. 填写Token和EncodingAESKey（与.env一致）
5. 点击"提交"验证

### 7. 测试连接

访问 `http://localhost:8000/api/wechat/test` 测试微信API连接

## 📁 项目结构

```
wechat-auto/
├── api/                    # FastAPI接口
│   ├── app.py             # 应用入口
│   └── routes/
│       └── wechat.py      # 微信Webhook
├── config/                 # 配置文件
│   ├── config.yaml        # 主配置
│   └── prompts.yaml       # AI提示词
├── src/
│   ├── agents/            # Agent实现
│   │   ├── base_agent.py
│   │   ├── coordinator_agent.py
│   │   ├── chat_agent.py
│   │   ├── content_agent.py
│   │   ├── analytics_agent.py
│   │   └── scheduler_agent.py
│   ├── cache/             # Redis缓存
│   │   └── redis_client.py
│   ├── database/          # 数据库
│   │   ├── models.py      # ORM模型
│   │   ├── crud.py        # CRUD操作
│   │   └── session.py     # 会话管理
│   ├── graph/             # LangGraph工作流
│   │   ├── state.py       # 状态定义
│   │   └── workflow.py    # 主工作流
│   ├── tasks/             # Celery任务
│   │   ├── celery_app.py
│   │   ├── content_tasks.py
│   │   └── analytics_tasks.py
│   └── wechat/            # 微信API
│       └── api_client.py
├── output/                # 输出目录
├── logs/                  # 日志目录
├── docker-compose.yml     # Docker编排
├── Dockerfile             # Docker镜像
├── requirements.txt       # Python依赖
├── install.sh             # 安装脚本
└── run.py                 # 启动入口
```

## 🚀 使用指南

### 内容生成

发送消息给公众号：
```
帮我写一篇关于"AI工具提升效率"的文章，目标读者是创业者，1500字
```

系统会自动：
1. 生成文章大纲
2. 撰写正文内容
3. 提供5个标题选项
4. 保存为草稿

### 数据分析

```
查看本周数据报告
```

系统会返回：
- 核心指标（粉丝增长、阅读量等）
- 数据洞察
- 优化建议

### 调度发布

```
把草稿1定在明天晚上8点发布
```

系统会：
1. 创建调度任务
2. 到时间自动发布

### FAQ管理

编辑 `.env` 文件，或在数据库中添加FAQ：

```python
from src.database.crud import FAQCRUD
from src.database.session import db_manager

with db_manager.get_session() as db:
    FAQCRUD.create_faq(
        db,
        question="如何购买产品？",
        answer="您可以访问我们的官网...",
        category="purchase",
        keywords=["购买", "下单", "价格"]
    )
```

## 🔧 配置说明

### 内容生成配置

编辑 `config/prompts.yaml` 自定义AI提示词。

### 定时任务配置

编辑 `src/tasks/celery_app.py` 中的 `beat_schedule`。

### Agent路由配置

编辑 `src/agents/coordinator_agent.py` 中的 `agent_registry`。

## 📊 监控和日志

### Flower监控

访问 `http://localhost:5555` 查看Celery任务状态。

### 日志文件

- API日志: `logs/api.log`
- Celery日志: `logs/celery.log`
- 错误日志: `logs/error.log`

## 🧪 测试

### 单元测试

```bash
pytest tests/
```

### 微信Webhook测试

使用ngrok暴露本地端口：
```bash
ngrok http 8000
```

将ngrok URL配置到微信后台。

## 🔒 安全建议

1. **不要提交`.env`文件到Git**
2. **定期更新依赖包**
3. **使用HTTPS**
4. **设置API速率限制**
5. **定期备份数据库**

## 📈 性能优化

- Redis缓存命中率 >80%
- API响应时间 <500ms
- 数据库查询优化（索引）
- Claude API调用优化（缓存）

## 🐛 常见问题

### 1. 微信验证失败

检查 `.env` 中的 `WECHAT_TOKEN` 是否与微信后台一致。

### 2. 数据库连接失败

确保PostgreSQL正在运行，检查 `DATABASE_URL` 配置。

### 3. Claude API调用失败

检查 `ANTHROPIC_API_KEY` 是否正确，账户是否有余额。

### 4. Celery任务不执行

检查Redis连接，确保Broker URL配置正确。

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

- Issues: [GitHub Issues](link)
- Email: 915374524@qq.com

## 🎯 路线图

- [ ] Web管理界面
- [ ] 多账号管理
- [ ] 短视频联动（视频号）
- [ ] 更丰富的数据分析
- [ ] 知识库增强

---

**注意**: 本系统仅供学习和个人使用，请遵守微信公众平台服务条款。
