"""
微信API客户端
"""
import time
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from src.cache.redis_client import cache_manager

load_dotenv()


class WeChatAPIClient:
    """微信API客户端"""

    def __init__(self):
        self.app_id = os.getenv("WECHAT_APP_ID")
        self.app_secret = os.getenv("WECHAT_APP_SECRET")
        self.api_base = "https://api.weixin.qq.com/cgi-bin"

        # AccessToken相关
        self.access_token = None
        self.token_expires_at = None
        self.redis_cache = cache_manager

    def get_access_token(self) -> str:
        """
        获取AccessToken（双Token机制）
        优先从缓存获取，缓存失效则重新获取
        """
        # 先从Redis缓存获取
        cached_token = self.redis_cache.get_wechat_access_token()
        if cached_token:
            return cached_token

        # 缓存不存在，调用API获取
        url = f"{self.api_base}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                # 设置过期时间（实际7200秒，缓存7000秒，提前200秒刷新）
                self.token_expires_at = datetime.now() + timedelta(seconds=7000)

                # 缓存Token
                self.redis_cache.set_wechat_access_token(self.access_token)

                return self.access_token
            else:
                raise Exception(f"获取AccessToken失败: {data}")

        except Exception as e:
            print(f"获取AccessToken错误: {e}")
            raise

    def refresh_access_token(self) -> str:
        """强制刷新AccessToken"""
        # 清除缓存
        self.redis_cache.redis.delete("wechat:access_token")
        return self.get_access_token()

    def _make_request(self, endpoint: str, method: str = "GET",
                      params: Optional[Dict] = None,
                      data: Optional[Dict] = None,
                      files: Optional[Dict] = None,
                      retry: int = 3) -> Dict[str, Any]:
        """
        发起API请求（带重试机制）

        Args:
            endpoint: API端点
            method: HTTP方法
            params: URL参数
            data: POST数据
            files: 上传文件
            retry: 重试次数

        Returns:
            API响应数据
        """
        url = f"{self.api_base}/{endpoint}"

        # 添加AccessToken
        if params is None:
            params = {}
        params["access_token"] = self.get_access_token()

        for attempt in range(retry):
            try:
                if method == "GET":
                    response = requests.get(url, params=params, timeout=10)
                elif method == "POST":
                    if files:
                        response = requests.post(url, params=params, files=files, timeout=30)
                    else:
                        response = requests.post(url, params=params, json=data, timeout=10)

                response.raise_for_status()
                result = response.json()

                # Token过期，刷新后重试
                if result.get("errcode") == 40001:
                    self.refresh_access_token()
                    params["access_token"] = self.get_access_token()
                    continue

                return result

            except requests.exceptions.RequestException as e:
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                raise Exception(f"API请求失败: {e}")

        return {}

    # ========== 消息发送相关 ==========

    def send_text_message(self, openid: str, text: str) -> Dict[str, Any]:
        """
        发送文本消息

        Args:
            openid: 用户OpenID
            text: 文本内容

        Returns:
            发送结果
        """
        endpoint = "message/custom/send"
        data = {
            "touser": openid,
            "msgtype": "text",
            "text": {"content": text}
        }
        return self._make_request(endpoint, method="POST", data=data)

    def send_image_message(self, openid: str, media_id: str) -> Dict[str, Any]:
        """
        发送图片消息

        Args:
            openid: 用户OpenID
            media_id: 媒体ID

        Returns:
            发送结果
        """
        endpoint = "message/custom/send"
        data = {
            "touser": openid,
            "msgtype": "image",
            "image": {"media_id": media_id}
        }
        return self._make_request(endpoint, method="POST", data=data)

    def send_news_message(self, openid: str, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        发送图文消息

        Args:
            openid: 用户OpenID
            articles: 图文文章列表 [{"title": "", "description": "", "url": "", "picurl": ""}]

        Returns:
            发送结果
        """
        endpoint = "message/custom/send"
        data = {
            "touser": openid,
            "msgtype": "news",
            "news": {"articles": articles}
        }
        return self._make_request(endpoint, method="POST", data=data)

    # ========== 素材管理相关 ==========

    def upload_media(self, media_type: str, file_path: str) -> Dict[str, Any]:
        """
        上传临时素材

        Args:
            media_type: 媒体类型（image, voice, video, thumb）
            file_path: 文件路径

        Returns:
            上传结果，包含media_id
        """
        endpoint = f"media/upload?type={media_type}"

        with open(file_path, "rb") as f:
            files = {"media": f}
            return self._make_request(endpoint, method="POST", files=files)

    def upload_article(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        上传图文素材

        Args:
            articles: 图文文章列表

        Returns:
            上传结果，包含media_id
        """
        endpoint = "media/uploadnews"
        data = {"articles": articles}
        return self._make_request(endpoint, method="POST", data=data)

    def get_media_url(self, media_id: str) -> str:
        """
        获取临时素材URL

        Args:
            media_id: 媒体ID

        Returns:
            素材URL
        """
        return f"{self.api_base}/media/get?access_token={self.get_access_token()}&media_id={media_id}"

    # ========== 用户管理相关 ==========

    def get_user_info(self, openid: str) -> Optional[Dict[str, Any]]:
        """
        获取用户基本信息

        Args:
            openid: 用户OpenID

        Returns:
            用户信息
        """
        endpoint = "user/info"
        params = {"openid": openid, "lang": "zh_CN"}
        return self._make_request(endpoint, method="GET", params=params)

    def get_followers_list(self, next_openid: Optional[str] = None) -> Dict[str, Any]:
        """
        获取关注用户列表

        Args:
            next_openid: 下一个用户的OpenID（分页）

        Returns:
            用户列表
        """
        endpoint = "user/get"
        params = {}
        if next_openid:
            params["next_openid"] = next_openid
        return self._make_request(endpoint, method="GET", params=params)

    def batch_get_user_info(self, openids: List[str]) -> Dict[str, Any]:
        """
        批量获取用户信息

        Args:
            openids: OpenID列表

        Returns:
            用户信息列表
        """
        endpoint = "user/info/batchget"
        data = {
            "user_list": [{"openid": openid} for openid in openids]
        }
        return self._make_request(endpoint, method="POST", data=data)

    # ========== 菜单管理相关 ==========

    def create_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建自定义菜单

        Args:
            menu_data: 菜单数据

        Returns:
            创建结果
        """
        endpoint = "menu/create"
        return self._make_request(endpoint, method="POST", data=menu_data)

    def get_menu(self) -> Dict[str, Any]:
        """
        获取自定义菜单

        Returns:
            菜单数据
        """
        endpoint = "menu/get"
        return self._make_request(endpoint, method="GET")

    def delete_menu(self) -> Dict[str, Any]:
        """
        删除自定义菜单

        Returns:
            删除结果
        """
        endpoint = "menu/delete"
        return self._make_request(endpoint, method="GET")

    # ========== 数据统计相关 ==========

    def get_user_summary(self, begin_date: str, end_date: str) -> Dict[str, Any]:
        """
        获取用户增减数据

        Args:
            begin_date: 开始日期（格式：YYYY-MM-DD）
            end_date: 结束日期

        Returns:
            用户增减数据
        """
        endpoint = "datacube/getusersummary"
        data = {
            "begin_date": begin_date,
            "end_date": end_date
        }
        return self._make_request(endpoint, method="POST", data=data)

    def get_article_total(self, begin_date: str, end_date: str) -> Dict[str, Any]:
        """
        获取图文群发总数据

        Args:
            begin_date: 开始日期
            end_date: 结束日期

        Returns:
            图文数据
        """
        endpoint = "datacube/getarticletotal"
        data = {
            "begin_date": begin_date,
            "end_date": end_date
        }
        return self._make_request(endpoint, method="POST", data=data)

    def get_user_read(self, begin_date: str, end_date: str) -> Dict[str, Any]:
        """
        获取图文统计数据

        Args:
            begin_date: 开始日期
            end_date: 结束日期

        Returns:
            阅读统计数据
        """
        endpoint = "datacube/getuserread"
        data = {
            "begin_date": begin_date,
            "end_date": end_date
        }
        return self._make_request(endpoint, method="POST", data=data)

    # ========== 草稿箱相关 ==========

    def add_draft(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        新建草稿

        Args:
            articles: 图文文章列表

        Returns:
            草稿media_id
        """
        endpoint = "draft/add"
        data = {"articles": articles}
        return self._make_request(endpoint, method="POST", data=data)

    # ========== 自动回复规则相关 ==========

    def add_auto_reply_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加自动回复规则

        Args:
            rule_data: 规则数据

        Returns:
            添加结果
        """
        endpoint = "img/auto-reply_rule"
        return self._make_request(endpoint, method="POST", data=rule_data)


# 全局微信API客户端实例
wechat_api_client = WeChatAPIClient()
