"""
LangGraph主工作流
"""
from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import AgentState
from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.chat_agent import ChatAgent
from src.agents.content_agent import ContentAgent
from src.agents.analytics_agent import AnalyticsAgent
from src.agents.scheduler_agent import SchedulerAgent


# 初始化所有Agent
coordinator = CoordinatorAgent()
chat_agent = ChatAgent()
content_agent = ContentAgent()
analytics_agent = AnalyticsAgent()
scheduler_agent = SchedulerAgent()


# Agent映射
AGENTS = {
    "coordinator": coordinator,
    "chat_agent": chat_agent,
    "content_agent": content_agent,
    "analytics_agent": analytics_agent,
    "scheduler_agent": scheduler_agent,
}


async def coordinator_node(state: AgentState) -> AgentState:
    """Coordinator节点 - 意图识别和路由"""
    return await coordinator.invoke(state)


async def chat_agent_node(state: AgentState) -> AgentState:
    """Chat Agent节点 - 对话处理"""
    return await chat_agent.invoke(state)


async def content_agent_node(state: AgentState) -> AgentState:
    """Content Agent节点 - 内容生成"""
    return await content_agent.invoke(state)


async def analytics_agent_node(state: AgentState) -> AgentState:
    """Analytics Agent节点 - 数据分析"""
    return await analytics_agent.invoke(state)


async def scheduler_agent_node(state: AgentState) -> AgentState:
    """Scheduler Agent节点 - 任务调度"""
    return await scheduler_agent.invoke(state)


def route_next_agent(state: AgentState) -> Literal["chat_agent", "content_agent", "analytics_agent", "scheduler_agent", "end"]:
    """
    根据Coordinator的路由决策，选择下一个Agent

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    next_agent = state.get("next_agent")

    if not next_agent:
        return "end"

    # 检查是否有错误
    if state.get("error"):
        return "end"

    # 根据next_agent字段路由
    if next_agent == "chat_agent":
        return "chat_agent"
    elif next_agent == "content_agent":
        return "content_agent"
    elif next_agent == "analytics_agent":
        return "analytics_agent"
    elif next_agent == "scheduler_agent":
        return "scheduler_agent"
    else:
        return "end"


def create_workflow_graph():
    """
    创建LangGraph工作流图

    Returns:
        编译后的工作流
    """
    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("chat_agent", chat_agent_node)
    workflow.add_node("content_agent", content_agent_node)
    workflow.add_node("analytics_agent", analytics_agent_node)
    workflow.add_node("scheduler_agent", scheduler_agent_node)

    # 设置入口点
    workflow.set_entry_point("coordinator")

    # 添加条件边（从Coordinator路由到各个Agent）
    workflow.add_conditional_edges(
        "coordinator",
        route_next_agent,
        {
            "chat_agent": "chat_agent",
            "content_agent": "content_agent",
            "analytics_agent": "analytics_agent",
            "scheduler_agent": "scheduler_agent",
            "end": END
        }
    )

    # 各个Agent执行完成后，直接结束（简化版）
    # 如果需要Agent之间协作，可以添加更复杂的路由
    workflow.add_edge("chat_agent", END)
    workflow.add_edge("content_agent", END)
    workflow.add_edge("analytics_agent", END)
    workflow.add_edge("scheduler_agent", END)

    # 添加内存保存器（用于检查点和恢复）
    memory = MemorySaver()

    # 编译工作流
    app = workflow.compile(checkpointer=memory)

    return app


# 创建全局工作流实例
workflow_app = create_workflow_graph()


async def run_workflow(user_id: str, message: str, message_type: str = "text",
                       event_type: str = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    运行工作流

    Args:
        user_id: 用户ID
        message: 用户消息
        message_type: 消息类型
        event_type: 事件类型（如果是事件消息）
        config: 配置参数（如thread_id用于会话恢复）

    Returns:
        工作流执行结果
    """
    # 初始化状态
    initial_state: AgentState = {
        "user_id": user_id,
        "message": message,
        "message_type": message_type,
        "event_type": event_type,
        "conversation_id": None,
        "chat_history": [],
        "user_profile": None,
        "intent": None,
        "confidence": 0.0,
        "entities": {},
        "current_agent": None,
        "agent_chain": [],
        "next_agent": None,
        "content_outline": None,
        "content_draft": None,
        "content_variants": [],
        "chat_response": None,
        "faq_matches": [],
        "analytics_data": None,
        "insights": [],
        "schedule_time": None,
        "scheduled_tasks": [],
        "response_message": None,
        "metadata": {},
        "error": None,
        "retry_count": 0,
        "messages": []
    }

    # 配置（用于检查点）
    if config is None:
        config = {"configurable": {"thread_id": user_id}}

    try:
        # 运行工作流
        result = await workflow_app.ainvoke(initial_state, config)

        # 提取关键结果
        output = {
            "success": True,
            "response_message": result.get("response_message"),
            "intent": result.get("intent"),
            "confidence": result.get("confidence"),
            "agent_chain": result.get("agent_chain", []),
            "metadata": result.get("metadata", {})
        }

        return output

    except Exception as e:
        print(f"工作流执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "response_message": "抱歉，系统出现了问题，请稍后再试。"
        }


async def run_workflow_stream(user_id: str, message: str, **kwargs):
    """
    流式运行工作流（用于实时监控Agent执行）

    Args:
        user_id: 用户ID
        message: 用户消息
        **kwargs: 其他参数

    Yields:
        每个Agent执行的中间状态
    """
    initial_state: AgentState = {
        "user_id": user_id,
        "message": message,
        "message_type": kwargs.get("message_type", "text"),
        "event_type": kwargs.get("event_type"),
        "conversation_id": None,
        "chat_history": [],
        "user_profile": None,
        "intent": None,
        "confidence": 0.0,
        "entities": {},
        "current_agent": None,
        "agent_chain": [],
        "next_agent": None,
        "content_outline": None,
        "content_draft": None,
        "content_variants": [],
        "chat_response": None,
        "faq_matches": [],
        "analytics_data": None,
        "insights": [],
        "schedule_time": None,
        "scheduled_tasks": [],
        "response_message": None,
        "metadata": {},
        "error": None,
        "retry_count": 0,
        "messages": []
    }

    config = kwargs.get("config", {"configurable": {"thread_id": user_id}})

    async for event in workflow_app.astream(initial_state, config):
        yield event
