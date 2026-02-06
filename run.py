"""
主入口文件
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    """主函数"""
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    print(f"""
    ╔═════════════════════════════════════════╗
    ║  WeChat Auto Operation System           ║
    ║  微信公众号自动运营系统                  ║
    ╚═════════════════════════════════════════╝

    🚀 启动中...
    📍 Host: {host}
    📍 Port: {port}
    🔧 Debug: {debug}
    """)

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=debug
    )


if __name__ == "__main__":
    main()
