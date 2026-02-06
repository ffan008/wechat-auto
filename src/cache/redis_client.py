"""
Redis客户端
"""
import redis
import json
import os
from typing import Any, Optional, Dict, List
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    """Redis客户端封装"""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self._connected = False

    def connect(self):
        """连接Redis"""
        if self._connected:
            return

        self.client = redis.from_url(
            self.redis_url,
            decode_responses=True,
            max_connections=50
        )
        self._connected = True

    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self._connected = False

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置键值"""
        if not self._connected:
            self.connect()

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if not self._connected:
            self.connect()

        try:
            value = self.client.get(key)
            if value is None:
                return None

            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """删除键"""
        if not self._connected:
            self.connect()

        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected:
            self.connect()

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if not self._connected:
            self.connect()

        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增"""
        if not self._connected:
            self.connect()

        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            print(f"Redis incr error: {e}")
            return None

    def hset(self, name: str, key: str, value: Any) -> bool:
        """哈希表设置"""
        if not self._connected:
            self.connect()

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.hset(name, key, value) >= 0
        except Exception as e:
            print(f"Redis hset error: {e}")
            return False

    def hget(self, name: str, key: str) -> Optional[Any]:
        """哈希表获取"""
        if not self._connected:
            self.connect()

        try:
            value = self.client.hget(name, key)
            if value is None:
                return None

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis hget error: {e}")
            return None

    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取整个哈希表"""
        if not self._connected:
            self.connect()

        try:
            data = self.client.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        except Exception as e:
            print(f"Redis hgetall error: {e}")
            return {}

    def lpush(self, name: str, *values: Any) -> int:
        """列表左侧推入"""
        if not self._connected:
            self.connect()

        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                serialized_values.append(value)
            return self.client.lpush(name, *serialized_values)
        except Exception as e:
            print(f"Redis lpush error: {e}")
            return 0

    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """列表范围获取"""
        if not self._connected:
            self.connect()

        try:
            values = self.client.lrange(name, start, end)
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except json.JSONDecodeError:
                    result.append(value)
            return result
        except Exception as e:
            print(f"Redis lrange error: {e}")
            return []

    def ltrim(self, name: str, start: int, end: int) -> bool:
        """列表裁剪"""
        if not self._connected:
            self.connect()

        try:
            self.client.ltrim(name, start, end)
            return True
        except Exception as e:
            print(f"Redis ltrim error: {e}")
            return False

    def flushdb(self) -> bool:
        """清空当前数据库"""
        if not self._connected:
            self.connect()

        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Redis flushdb error: {e}")
            return False


# 全局Redis客户端实例
redis_client = RedisClient()


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    # 对话缓存
    def get_conversation_history(self, user_id: int) -> List[Dict[str, Any]]:
        """获取对话历史"""
        key = f"conversation:{user_id}"
        return self.redis.lrange(key, 0, -1)

    def add_conversation_message(self, user_id: int, role: str, content: str,
                                 ttl: int = 7 * 24 * 3600) -> bool:
        """添加对话消息"""
        key = f"conversation:{user_id}"
        message = {"role": role, "content": content, "timestamp": str(datetime.now())}

        # 添加到列表头部
        self.redis.lpush(key, message)

        # 限制历史记录数量（保留最近20条）
        self.redis.ltrim(key, 0, 19)

        # 设置过期时间
        self.redis.expire(key, ttl)
        return True

    # 用户画像缓存
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        key = f"user_profile:{user_id}"
        return self.redis.hgetall(key)

    def set_user_profile(self, user_id: int, profile: Dict[str, Any],
                         ttl: int = 24 * 3600) -> bool:
        """设置用户画像"""
        key = f"user_profile:{user_id}"
        for field, value in profile.items():
            self.redis.hset(key, field, value)
        self.redis.expire(key, ttl)
        return True

    # 内容指标缓存
    def get_content_metrics(self, content_id: int) -> Optional[Dict[str, Any]]:
        """获取内容指标"""
        key = f"content_metrics:{content_id}"
        return self.redis.hgetall(key)

    def update_content_metrics(self, content_id: int, metrics: Dict[str, Any],
                               ttl: int = 3600) -> bool:
        """更新内容指标"""
        key = f"content_metrics:{content_id}"
        for field, value in metrics.items():
            self.redis.hset(key, field, value)
        self.redis.expire(key, ttl)
        return True

    # 分析概览缓存
    def get_analytics_overview(self) -> Optional[Dict[str, Any]]:
        """获取分析概览"""
        key = "analytics:overview"
        return self.redis.get(key)

    def set_analytics_overview(self, data: Dict[str, Any],
                               ttl: int = 6 * 3600) -> bool:
        """设置分析概览"""
        key = "analytics:overview"
        return self.redis.set(key, data, ttl)

    # 微信AccessToken缓存
    def get_wechat_access_token(self) -> Optional[str]:
        """获取微信AccessToken"""
        key = "wechat:access_token"
        return self.redis.get(key)

    def set_wechat_access_token(self, token: str, ttl: int = 7000) -> bool:
        """设置微信AccessToken（有效期约2小时，设置7200-200秒）"""
        key = "wechat:access_token"
        return self.redis.set(key, token, ttl)

    # 速率限制
    def check_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """检查速率限制"""
        redis_key = f"rate_limit:{key}"
        current = self.redis.get(redis_key)

        if current is None:
            self.redis.set(redis_key, 1, window)
            return True

        if current >= limit:
            return False

        self.redis.incr(redis_key)
        return True

    # 热点话题缓存
    def get_trending_topics(self) -> List[Dict[str, Any]]:
        """获取热点话题"""
        key = "trending:topics"
        return self.redis.get(key) or []

    def set_trending_topics(self, topics: List[Dict[str, Any]],
                            ttl: int = 1800) -> bool:
        """设置热点话题"""
        key = "trending:topics"
        return self.redis.set(key, topics, ttl)


# 全局缓存管理器实例
from datetime import datetime
cache_manager = CacheManager(redis_client)
