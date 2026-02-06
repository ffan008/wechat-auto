"""
FastAPI应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from api.routes import wechat
from src.database.session import db_manager

load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="WeChat Auto Operation System",
    description="基于AI Agent的微信公众号自动运营系统",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("🚀 WeChat Auto Operation System 启动中...")

    # 初始化数据库
    try:
        db_manager.initialize()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")

    print("✅ 系统启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("🛑 系统关闭中...")
    # 清理资源
    print("✅ 系统已关闭")


@app.get("/")
async def root():
    """根路径"""
    return JSONResponse(content={
        "message": "WeChat Auto Operation System API",
        "version": "1.0.0",
        "status": "running"
    })


@app.get("/health")
async def health():
    """健康检查"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "api"
    })


# 注册路由
app.include_router(wechat.router)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=True
    )
