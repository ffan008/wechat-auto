"""
微信Webhook处理
"""
import xml.etree.ElementTree as ET
import hashlib
import time
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

from src.graph.workflow import run_workflow
from src.wechat.api_client import wechat_api_client
from src.database.crud import UserCRUD, ConversationCRUD
from src.database.session import db_manager

load_dotenv()

router = APIRouter(prefix="/wechat", tags=["wechat"])

# 微信配置
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN")
WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY")


def verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """
    验证微信签名

    Args:
        signature: 微信签名
        timestamp: 时间戳
        nonce: 随机数

    Returns:
        是否验证通过
    """
    # 将token、timestamp、nonce三个参数进行字典序排序
    params = sorted([WECHAT_TOKEN, timestamp, nonce])
    # 将三个参数字符串拼接成一个字符串进行sha1加密
    sha1 = hashlib.sha1()
    sha1.update("".join(params).encode())
    hashcode = sha1.hexdigest()

    # 将加密后的字符串与signature对比
    return hashcode == signature


def parse_xml_message(xml_data: str) -> Dict[str, Any]:
    """
    解析XML消息

    Args:
        xml_data: XML字符串

    Returns:
        消息字典
    """
    root = ET.fromstring(xml_data)

    msg = {}
    for child in root:
        msg[child.tag] = child.text

    return msg


def build_xml_response(to_user: str, from_user: str, content: str,
                       msg_type: str = "text") -> str:
    """
    构建XML响应

    Args:
        to_user: 接收方OpenID
        from_user: 发送方微信号
        content: 消息内容
        msg_type: 消息类型

    Returns:
        XML字符串
    """
    timestamp = int(time.time())

    if msg_type == "text":
        xml = f"""
<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[{msg_type}]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>
"""
    else:
        # 其他消息类型
        xml = f"""
<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[{msg_type}]]></MsgType>
</xml>
"""

    return xml.strip()


@router.get("/webhook")
async def wechat_webhook_verify(
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str
):
    """
    微信服务器验证（GET请求）

    当用户首次配置服务器时，微信会发送GET请求验证服务器有效性
    """
    if verify_signature(signature, timestamp, nonce):
        return PlainTextResponse(content=echostr)
    else:
        raise HTTPException(status_code=403, detail="签名验证失败")


@router.post("/webhook")
async def wechat_webhook_handler(request: Request):
    """
    微信消息处理（POST请求）

    处理用户发送的消息和事件推送
    """
    # 读取XML数据
    xml_data = await request.body()
    message = parse_xml_message(xml_data.decode())

    # 提取消息字段
    msg_type = message.get("MsgType", "")
    event_type = message.get("Event", "")

    to_user = message.get("ToUserName", "")
    from_user = message.get("FromUserName", "")

    print(f"[Webhook] 收到消息")
    print(f"[Webhook] MsgType: {msg_type}")
    print(f"[Webhook] Event: {event_type}")
    print(f"[Webhook] FromUser: {from_user}")

    # 处理事件消息
    if msg_type == "event":
        response = await handle_event_message(message, from_user)

    # 处理文本消息
    elif msg_type == "text":
        response = await handle_text_message(message, from_user)

    # 处理其他类型消息（图片、语音等）
    else:
        response = await handle_other_message(message, from_user)

    # 如果有回复，返回XML
    if response and response.get("reply"):
        return PlainTextResponse(
            content=build_xml_response(
                to_user=from_user,
                from_user=to_user,
                content=response["reply"],
                msg_type=response.get("msg_type", "text")
            )
        )

    # 无回复，返回成功
    return PlainTextResponse(content="success")


async def handle_event_message(message: Dict, user_id: str) -> Optional[Dict[str, str]]:
    """
    处理事件消息

    Args:
        message: 消息字典
        user_id: 用户ID

    Returns:
        回复字典
    """
    event = message.get("Event", "")

    # 用户关注事件
    if event == "subscribe":
        # 创建或更新用户
        with db_manager.get_session() as db:
            user = UserCRUD.get_user_by_openid(db, user_id)
            if not user:
                user = UserCRUD.create_user(
                    db,
                    openid=user_id,
                    is_subscribed=True
                )
            else:
                UserCRUD.update_user(
                    db,
                    user.id,
                    is_subscribed=True,
                    subscribe_time=datetime.now()
                )

        # 返回欢迎消息
        return {
            "reply": """欢迎关注我们的公众号！🎉

我是AI助手，可以帮您：
• 回答问题和咨询
• 提供产品信息
• 生成内容（如果需要）
• 查看数据分析

随时给我发消息，我会尽快回复！""",
            "msg_type": "text"
        }

    # 用户取消关注
    elif event == "unsubscribe":
        with db_manager.get_session() as db:
            user = UserCRUD.get_user_by_openid(db, user_id)
            if user:
                UserCRUD.update_user(
                    db,
                    user.id,
                    is_subscribed=False,
                    unsubscribe_time=datetime.now()
                )
        return None  # 不需要回复

    # 菜单点击事件
    elif event == "CLICK":
        event_key = message.get("EventKey", "")
        return await handle_menu_click(event_key, user_id)

    return None


async def handle_text_message(message: Dict, user_id: str) -> Optional[Dict[str, str]]:
    """
    处理文本消息

    Args:
        message: 消息字典
        user_id: 用户ID

    Returns:
        回复字典
    """
    content = message.get("Content", "").strip()

    if not content:
        return None

    print(f"[Webhook] 用户消息: {content}")

    try:
        # 运行LangGraph工作流
        result = await run_workflow(
            user_id=user_id,
            message=content,
            message_type="text"
        )

        if result.get("success"):
            reply = result.get("response_message")
            print(f"[Webhook] AI回复: {reply}")

            return {
                "reply": reply,
                "msg_type": "text"
            }
        else:
            print(f"[Webhook] 工作流执行失败: {result.get('error')}")
            return {
                "reply": "抱歉，系统出现了一点问题，请稍后再试。",
                "msg_type": "text"
            }

    except Exception as e:
        print(f"[Webhook] 处理消息失败: {e}")
        import traceback
        traceback.print_exc()

        return {
            "reply": "抱歉，我暂时无法理解您的消息。您可以换个说法，或联系人工客服。",
            "msg_type": "text"
        }


async def handle_other_message(message: Dict, user_id: str) -> Optional[Dict[str, str]]:
    """
    处理其他类型消息

    Args:
        message: 消息字典
        user_id: 用户ID

    Returns:
        回复字典
    """
    msg_type = message.get("MsgType", "")

    # 图片消息
    if msg_type == "image":
        return {
            "reply": "收到您的图片！如需分析图片内容，请描述您的需求。",
            "msg_type": "text"
        }

    # 语音消息
    elif msg_type == "voice":
        return {
            "reply": "收到您的语音！我目前只支持文字对话，请用文字描述您的需求。",
            "msg_type": "text"
        }

    # 其他不支持的消息类型
    else:
        return {
            "reply": f"暂不支持 {msg_type} 类型的消息，请发送文字。",
            "msg_type": "text"
        }


async def handle_menu_click(event_key: str, user_id: str) -> Optional[Dict[str, str]]:
    """
    处理菜单点击

    Args:
        event_key: 菜单键值
        user_id: 用户ID

    Returns:
        回复字典
    """
    # 根据菜单键值返回不同内容
    menu_responses = {
        "LATEST_ARTICLE": "最新文章：《如何使用AI提升运营效率》\n\n点击查看全文：https://...",
        "PRODUCT_INFO": "我们的产品包括...\n\n如需了解更多，请回复具体问题。",
        "CUSTOMER_SERVICE": "正在为您转接人工客服，请稍候..."
    }

    reply = menu_responses.get(event_key, "感谢您的点击！")
    return {"reply": reply, "msg_type": "text"}


@router.post("/test")
async def test_wechat_connection():
    """
    测试微信API连接
    """
    try:
        # 尝试获取AccessToken
        token = wechat_api_client.get_access_token()

        return JSONResponse(content={
            "success": True,
            "message": "微信API连接正常",
            "access_token": token[:20] + "..." if token else None
        })

    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "wechat-webhook"
    })


from datetime import datetime
