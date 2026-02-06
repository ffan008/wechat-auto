#!/usr/bin/env python3
"""
自动创建GitHub仓库并推送代码
"""
import subprocess
import sys
import requests
import json
import getpass

def create_github_repo(token, repo_name, description):
    """使用GitHub API创建仓库"""
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "has_wiki": True,
        "has_issues": True
    }

    print(f"📦 正在创建GitHub仓库: {repo_name}")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        repo_data = response.json()
        clone_url = repo_data["clone_url"]
        print(f"✅ 仓库创建成功!")
        print(f"📍 仓库地址: {repo_data['html_url']}")
        return clone_url
    elif response.status_code == 401:
        print("❌ 认证失败: Token无效或已过期")
        return None
    else:
        print(f"❌ 创建失败: {response.status_code}")
        print(response.json())
        return None

def push_to_github(clone_url):
    """推送代码到GitHub"""
    # 使用token的URL（避免输入密码）
    # 从clone_url中提取用户名
    if "https://" in clone_url:
        # 转换为使用token的URL
        parts = clone_url.split("https://")
        token_url = f"https://oauth2:TOKEN@{parts[1]}"
    else:
        token_url = clone_url

    try:
        # 添加remote
        print("\n🔗 配置remote...")
        subprocess.run(
            ["git", "remote", "add", "origin", clone_url],
            check=True,
            capture_output=True
        )

        # 推送代码
        print("🚀 正在推送代码到GitHub...")
        result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ 代码推送成功!")
            return True
        else:
            print("❌ 推送失败:")
            print(result.stderr)
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    print("=" * 60)
    print("  GitHub 仓库自动创建和推送工具")
    print("=" * 60)
    print()

    # 获取GitHub Token
    print("请提供GitHub Personal Access Token:")
    print("1. 访问: https://github.com/settings/tokens")
    print("2. 点击 'Generate new token (classic)'")
    print("3. 选择权限: repo (全选)")
    print("4. 生成并复制token")
    print()

    token = getpass.getpass("请输入Token (输入后隐藏): ").strip()

    if not token:
        print("❌ Token不能为空")
        sys.exit(1)

    # 仓库信息
    repo_name = input("\n仓库名称 (默认: wechat-auto): ").strip() or "wechat-auto"
    description = "WeChat Official Account Auto Operation System with AI Agents"

    # 创建仓库
    clone_url = create_github_repo(token, repo_name, description)

    if not clone_url:
        sys.exit(1)

    # 推送代码
    success = push_to_github(clone_url)

    if success:
        print("\n" + "=" * 60)
        print("🎉 完成! 您的代码已成功推送到GitHub!")
        print("=" * 60)
    else:
        print("\n⚠️  仓库已创建，但推送失败。请手动执行:")
        print(f"   git remote add origin {clone_url}")
        print(f"   git push -u origin main")

if __name__ == "__main__":
    main()
