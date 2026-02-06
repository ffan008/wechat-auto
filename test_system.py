"""
系统测试脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_workflow():
    """测试LangGraph工作流"""
    print("=" * 50)
    print("测试 LangGraph 工作流")
    print("=" * 50)

    from src.graph.workflow import run_workflow

    test_cases = [
        {
            "name": "问候测试",
            "user_id": "test_user_001",
            "message": "你好"
        },
        {
            "name": "咨询测试",
            "user_id": "test_user_002",
            "message": "怎么购买产品？"
        },
        {
            "name": "内容创作测试",
            "user_id": "test_user_003",
            "message": "帮我写一篇关于AI的文章"
        },
        {
            "name": "数据分析测试",
            "user_id": "test_user_004",
            "message": "查看本周数据"
        }
    ]

    for test in test_cases:
        print(f"\n📝 {test['name']}")
        print(f"用户: {test['user_id']}")
        print(f"消息: {test['message']}")

        try:
            result = await run_workflow(
                user_id=test['user_id'],
                message=test['message']
            )

            if result.get('success'):
                print(f"✅ 成功")
                print(f"意图: {result.get('intent')}")
                print(f"置信度: {result.get('confidence')}")
                print(f"Agent链: {' → '.join(result.get('agent_chain', []))}")
                print(f"回复: {result.get('response_message', '')[:200]}")
            else:
                print(f"❌ 失败: {result.get('error')}")

        except Exception as e:
            print(f"❌ 异常: {e}")
            import traceback
            traceback.print_exc()


def test_database():
    """测试数据库连接"""
    print("\n" + "=" * 50)
    print("测试数据库连接")
    print("=" * 50)

    try:
        from src.database.session import db_manager

        db_manager.initialize()

        # 创建表
        print("📊 创建数据库表...")
        db_manager.create_tables()
        print("✅ 数据库表创建成功")

        # 测试CRUD
        from src.database.crud import UserCRUD
        from src.database.models import User

        with db_manager.get_session() as db:
            # 创建测试用户
            user = UserCRUD.create_user(
                db,
                openid="test_openid_001",
                nickname="测试用户",
                is_subscribed=True
            )
            print(f"✅ 创建用户: {user.id}")

            # 查询用户
            found_user = UserCRUD.get_user_by_openid(db, "test_openid_001")
            print(f"✅ 查询用户: {found_user.nickname if found_user else 'Not found'}")

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_redis():
    """测试Redis连接"""
    print("\n" + "=" * 50)
    print("测试Redis连接")
    print("=" * 50)

    try:
        from src.cache.redis_client import redis_client, cache_manager

        # 测试连接
        redis_client.connect()
        print("✅ Redis连接成功")

        # 测试缓存
        test_key = "test_key"
        test_value = {"message": "Hello, Redis!"}

        cache_manager.redis.set(test_key, test_value, ttl=60)
        print(f"✅ 设置缓存: {test_key}")

        retrieved = cache_manager.redis.get(test_key)
        print(f"✅ 获取缓存: {retrieved}")

    except Exception as e:
        print(f"❌ Redis测试失败: {e}")


def test_wechat_api():
    """测试微信API（需要配置）"""
    print("\n" + "=" * 50)
    print("测试微信API")
    print("=" * 50)

    try:
        from src.wechat.api_client import wechat_api_client

        # 测试获取AccessToken
        token = wechat_api_client.get_access_token()
        if token:
            print(f"✅ AccessToken获取成功: {token[:20]}...")
        else:
            print("⚠️  AccessToken获取失败（可能是配置问题）")

    except Exception as e:
        print(f"⚠️  微信API测试跳过: {e}")


def test_agents():
    """测试各个Agent"""
    print("\n" + "=" * 50)
    print("测试Agent")
    print("=" * 50)

    # Coordinator Agent
    try:
        from src.agents.coordinator_agent import CoordinatorAgent

        agent = CoordinatorAgent()
        print(f"✅ Coordinator Agent加载成功")
        print(f"   描述: {agent.get_agent_description('coordinator')}")
    except Exception as e:
        print(f"❌ Coordinator Agent加载失败: {e}")

    # Chat Agent
    try:
        from src.agents.chat_agent import ChatAgent
        print(f"✅ Chat Agent加载成功")
    except Exception as e:
        print(f"❌ Chat Agent加载失败: {e}")

    # Content Agent
    try:
        from src.agents.content_agent import ContentAgent
        print(f"✅ Content Agent加载成功")
    except Exception as e:
        print(f"❌ Content Agent加载失败: {e}")

    # Analytics Agent
    try:
        from src.agents.analytics_agent import AnalyticsAgent
        print(f"✅ Analytics Agent加载成功")
    except Exception as e:
        print(f"❌ Analytics Agent加载失败: {e}")

    # Scheduler Agent
    try:
        from src.agents.scheduler_agent import SchedulerAgent
        print(f"✅ Scheduler Agent加载成功")
    except Exception as e:
        print(f"❌ Scheduler Agent加载失败: {e}")


async def main():
    """主测试函数"""
    print("\n╔═════════════════════════════════════════╗")
    print("║  WeChat Auto - 系统测试                  ║")
    print("╚═════════════════════════════════════════╝\n")

    # 测试数据库
    test_database()

    # 测试Redis
    test_redis()

    # 测试微信API
    test_wechat_api()

    # 测试Agent
    test_agents()

    # 测试工作流
    await test_workflow()

    print("\n" + "=" * 50)
    print("✅ 测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
