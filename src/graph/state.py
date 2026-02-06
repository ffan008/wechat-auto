"""
LangGraph状态定义
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """Agent状态定义"""

    # 输入信息
    user_id: Optional[str]  # 用户OpenID
    message: str  # 用户消息
    message_type: str  # 消息类型 (text, image, voice, event)
    event_type: Optional[str]  # 事件类型 (subscribe, unsubscribe, click)

    # 对话上下文
    conversation_id: Optional[int]  # 会话ID
    chat_history: List[Dict[str, str]]  # 对话历史
    user_profile: Optional[Dict[str, Any]]  # 用户画像

    # Agent处理结果
    intent: Optional[str]  # 识别的意图
    confidence: float  # 置信度
    entities: Dict[str, Any]  # 提取的实体

    # Agent路由信息
    current_agent: Optional[str]  # 当前执行的Agent
    agent_chain: List[str]  # Agent调用链
    next_agent: Optional[str]  # 下一个要调用的Agent

    # Content Agent相关
    content_outline: Optional[Dict[str, Any]]  # 内容大纲
    content_draft: Optional[str]  # 内容草稿
    content_variants: List[str]  # 内容变体（如标题）

    # Chat Agent相关
    chat_response: Optional[str]  # 聊天回复
    faq_matches: List[Dict[str, Any]]  # 匹配的FAQ

    # Analytics Agent相关
    analytics_data: Optional[Dict[str, Any]]  # 分析数据
    insights: List[str]  # 洞察列表

    # Scheduler Agent相关
    schedule_time: Optional[datetime]  # 调度时间
    scheduled_tasks: List[Dict[str, Any]]  # 调度任务列表

    # 输出
    response_message: Optional[str]  # 返回给用户的响应
    metadata: Dict[str, Any]  # 元数据

    # 错误处理
    error: Optional[str]  # 错误信息
    retry_count: int  # 重试次数

    # 辅助字段（用于状态合并）
    messages: Annotated[List[str], operator.add]  # 消息累加器


class ContentState(TypedDict):
    """内容生成状态"""
    topic: str  # 选题
    content_type: str  # 内容类型
    target_audience: str  # 目标受众
    word_count: int  # 字数

    outline: Optional[Dict[str, Any]]  # 大纲
    titles: List[str]  # 标题选项
    content: Optional[str]  # 正文内容
    media_id: Optional[str]  # 微信素材ID

    status: str  # 状态: draft, generating, reviewing, scheduled, published


class ChatState(TypedDict):
    """对话状态"""
    user_id: str
    current_message: str
    conversation_history: List[Dict[str, str]]

    intent: str
    confidence: float
    entities: Dict[str, Any]

    matched_faq: Optional[Dict[str, Any]]
    response: Optional[str]

    # 用户画像更新
    update_profile: bool
    new_tags: List[str]


class AnalyticsState(TypedDict):
    """分析状态"""
    date_range: Dict[str, str]  # 日期范围
    metrics: Dict[str, Any]  # 指标数据

    insights: List[str]  # 洞察
    recommendations: List[str]  # 建议
    report: Optional[str]  # 报告内容


class SchedulerState(TypedDict):
    """调度状态"""
    content_id: Optional[int]
    publish_time: Optional[datetime]

    calendar: List[Dict[str, Any]]  # 内容日历
    pending_tasks: List[Dict[str, Any]]  # 待处理任务
