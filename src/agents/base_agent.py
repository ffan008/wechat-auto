"""
Agent基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import anthropic
import os
from dotenv import load_dotenv

from src.graph.state import AgentState

load_dotenv()


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str):
        self.name = name
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"  # 默认使用Claude 3.5 Sonnet

    @abstractmethod
    async def invoke(self, state: AgentState) -> AgentState:
        """
        Agent的执行逻辑

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        pass

    def call_claude(self, prompt: str, max_tokens: int = 1024,
                    system_prompt: Optional[str] = None) -> str:
        """
        调用Claude API

        Args:
            prompt: 用户提示
            max_tokens: 最大token数
            system_prompt: 系统提示

        Returns:
            Claude响应
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            if system_prompt:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages
                )

            return response.content[0].text

        except Exception as e:
            print(f"{self.name} Claude API调用失败: {e}")
            raise

    def call_claude_with_history(self, messages: list, max_tokens: int = 1024,
                                  system_prompt: Optional[str] = None) -> str:
        """
        使用对话历史调用Claude

        Args:
            messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
            max_tokens: 最大token数
            system_prompt: 系统提示

        Returns:
            Claude响应
        """
        try:
            if system_prompt:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages
                )

            return response.content[0].text

        except Exception as e:
            print(f"{self.name} Claude API调用失败: {e}")
            raise

    def update_state(self, state: AgentState, **kwargs) -> AgentState:
        """
        更新状态

        Args:
            state: 当前状态
            **kwargs: 要更新的字段

        Returns:
            更新后的状态
        """
        for key, value in kwargs.items():
            if key in state.__annotations__:
                state[key] = value
        return state

    def log_invocation(self, state: AgentState):
        """记录Agent调用日志"""
        print(f"[{self.name}] Agent invoked")
        print(f"[{self.name}] User: {state.get('user_id')}")
        print(f"[{self.name}] Message: {state.get('message', '')[:100]}")
