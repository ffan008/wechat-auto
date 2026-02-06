"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, DateTime, Boolean,
    ForeignKey, JSON, Float, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class LifecycleStage(enum.Enum):
    """用户生命周期阶段"""
    NEW = "new"  # 新用户
    ACTIVE = "active"  # 活跃用户
    DORMANT = "dormant"  # 沉睡用户
    CHURNED = "churned"  # 流失用户


class RFMSegment(enum.Enum):
    """RFM分层"""
    CHAMPIONS = "champions"  # 核心价值用户
    LOYAL = "loyal"  # 忠诚用户
    POTENTIAL = "potential"  # 潜力用户
    PRICE_SENSITIVE = "price_sensitive"  # 价格敏感
    HIBERNATING = "hibernating"  # 休眠用户
    LOST = "lost"  # 流失用户


class User(Base):
    """用户表（粉丝信息）"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    openid = Column(String(100), unique=True, nullable=False, index=True)
    unionid = Column(String(100), index=True)
    nickname = Column(String(200))
    avatar_url = Column(String(500))
    subscribe_time = Column(DateTime, default=datetime.utcnow)
    unsubscribe_time = Column(DateTime)
    is_subscribed = Column(Boolean, default=True, index=True)

    # 用户画像
    lifecycle_stage = Column(SQLEnum(LifecycleStage), default=LifecycleStage.NEW)
    rfm_segment = Column(SQLEnum(RFMSegment))
    tags = Column(JSON, default=list)
    attributes = Column(JSON, default=dict)  # 扩展属性

    # 统计数据
    total_interactions = Column(Integer, default=0)
    last_interaction_time = Column(DateTime)
    sentiment_score = Column(Float, default=0.0)  # -1到1，负数负面，正数正面

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    conversations = relationship("Conversation", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")

    __table_args__ = (
        Index('idx_users_lifecycle', 'lifecycle_stage'),
        Index('idx_users_rfm', 'rfm_segment'),
    )


class Content(Base):
    """内容表（文章）"""
    __tablename__ = "content"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)

    # 微信相关
    wechat_media_id = Column(String(100))  # 微信素材ID
    wechat_article_id = Column(String(100))  # 微信文章ID

    # 状态
    status = Column(String(50), default="draft")  # draft, scheduled, published, failed
    publish_time = Column(DateTime, index=True)

    # 内容分类
    content_type = Column(String(50))  # tutorial, analysis, case, hot, casual
    topic = Column(String(200))
    keywords = Column(JSON, default=list)

    # A/B测试
    is_ab_test = Column(Boolean, default=False)
    title_variants = Column(JSON, default=list)  # [title1, title2, ...]

    # 统计数据
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    favorites = Column(Integer, default=0)

    # AI生成相关
    ai_generated = Column(Boolean, default=True)
    ai_model = Column(String(50))  # claude-3.5-sonnet
    outline = Column(JSON)  # 文章大纲
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    schedules = relationship("ContentSchedule", back_populates="content")
    interactions = relationship("UserInteraction", back_populates="content")

    __table_args__ = (
        Index('idx_content_status', 'status'),
        Index('idx_content_publish_time', 'publish_time'),
        Index('idx_content_type', 'content_type'),
    )


class ContentSchedule(Base):
    """内容发布计划表"""
    __tablename__ = "content_schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content_id = Column(BigInteger, ForeignKey("content.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False, index=True)

    # 执行状态
    status = Column(String(50), default="pending")  # pending, publishing, success, failed
    executed_at = Column(DateTime)
    error_message = Column(Text)

    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    content = relationship("Content", back_populates="schedules")


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # 会话状态
    status = Column(String(50), default="active")  # active, closed, transferred
    last_message_time = Column(DateTime, index=True)

    # Agent处理记录
    agent_route = Column(String(100))  # chat_agent, content_agent, etc.
    intent = Column(String(100))  # 主要意图

    # 统计
    message_count = Column(Integer, default=0)
    satisfaction_score = Column(Float)  # 满意度评分

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """消息表（对话历史）"""
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # 消息内容
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    msg_type = Column(String(20), default="text")  # text, image, voice, etc.

    # AI处理
    intent = Column(String(100))  # 识别的意图
    confidence = Column(Float)  # 置信度
    agent_used = Column(String(100))  # 使用的Agent

    # 微信消息ID
    wechat_msg_id = Column(String(100))

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index('idx_messages_conversation', 'conversation_id'),
        Index('idx_messages_created', 'created_at'),
    )


class UserInteraction(Base):
    """用户互动记录表"""
    __tablename__ = "user_interactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(BigInteger, ForeignKey("content.id"))

    # 互动类型
    interaction_type = Column(String(50), nullable=False)  # view, like, share, comment, etc.
    intent = Column(String(100))  # 意图分类
    sentiment = Column(String(50))  # positive, negative, neutral

    # 元数据
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = relationship("User", back_populates="interactions")
    content = relationship("Content", back_populates="interactions")

    __table_args__ = (
        Index('idx_interactions_type', 'interaction_type'),
        Index('idx_interactions_user_time', 'user_id', 'created_at'),
    )


class AnalyticsSnapshot(Base):
    """数据快照表"""
    __tablename__ = "analytics_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    snapshot_type = Column(String(50), nullable=False)  # daily, weekly, monthly

    # 粉丝数据
    total_followers = Column(Integer, default=0)
    new_followers = Column(Integer, default=0)
    lost_followers = Column(Integer, default=0)

    # 内容数据
    total_articles = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)

    # 互动数据
    total_interactions = Column(Integer, default=0)
    avg_engagement_rate = Column(Float)

    # AI数据
    ai_generated_articles = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_snapshots_date_type', 'snapshot_date', 'snapshot_type'),
    )


class AgentWorkflow(Base):
    """Agent工作流历史表"""
    __tablename__ = "agent_workflows"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(String(100), unique=True, nullable=False, index=True)

    # 工作流信息
    agent_type = Column(String(100), nullable=False)  # coordinator, content, chat, etc.
    input_data = Column(JSON)
    output_data = Column(JSON)

    # 执行状态
    status = Column(String(50), default="running")  # running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # 错误信息
    error_message = Column(Text)
    error_traceback = Column(Text)

    # 性能指标
    tokens_used = Column(Integer)
    cost_estimate = Column(Float)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_workflows_agent', 'agent_type'),
        Index('idx_workflows_status', 'status'),
        Index('idx_workflows_started', 'started_at'),
    )


class FAQ(Base):
    """常见问题库"""
    __tablename__ = "faqs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)

    # 分类
    category = Column(String(100))
    keywords = Column(JSON, default=list)
    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高

    # 使用统计
    hit_count = Column(Integer, default=0)
    last_hit_time = Column(DateTime)
    effectiveness_score = Column(Float)  # 有效性评分

    # 状态
    is_active = Column(Boolean, default=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_faqs_category', 'category'),
        Index('idx_faqs_active', 'is_active'),
    )
