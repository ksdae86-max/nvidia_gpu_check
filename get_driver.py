import os
import requests

def update_github_variable(formatted_value):
    """GitHubのRepository VariableをAPI経由で更新する"""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    var_name = "LATEST_GPU_VERSION"

    if not token or not repo:
        print("⚠️ GITHUB_TOKEN または REPOSITORY が設定されていないため変数を更新できません。")
        return

    url = f"https://api.github.com/repos/{repo}/actions/variables/{var_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    # PC側の split(": ") に対応する形式で保存
    data = {"name": var_name, "value": str(formatted_value)}

    res = requests.patch(url, json=data, headers=headers)
    if res.status_code == 204:
        print(f"✅ GitHub Actionsの基準変数を更新しました: {formatted_value}")
    else:
        print(f"❌ 変数更新失敗: {res.status_code} - {res.text}")

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "💎 最新ドライバを検知！",
            "description": f"バージョン: **{version}**\n[直リンク]({url})",
            "color": 5025616
        }]
    }
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        print(f"Discord Notification Sent: {res.status_code}")
    except Exception as e:
        print(f"Notification Error: {e}")

def check_url_exists(url):
    try:
        res = requests.head(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return res.status_code == 200
    except:
        return False

def update_driver_history():
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    # 変数から取得 (PC側の split 仕様に合わせた形式を想定)
    raw_var = os.getenv("LATEST_GPU_VERSION", "593.00")
    try:
        current_version = float(raw_var.split(": ")[0])
    except:
        current_version = 593.00

    print(f"Checking for updates. Starting from: {current_version}")

    found_version = None
    found_url = None

    start_major = int(current_version) + 2

    for major in range(start_major, int(current_version) - 1, -1):
        for minor in range(99, -1, -1):
            v = f"{major}.{minor:02d}"
            v_float = float(v)

            if v_float <= current_version:
                break

            test_url = f"https://jp.download.nvidia.com/Windows/{v}/{v}-desktop-win10-win11-64bit-international-dch-whql.exe"

            if check_url_exists(test_url):
                found_version = v
                found_url = test_url
                break
        if found_version: break

    if found_version and float(found_version) > current_version:
        print(f"NEW DRIVER FOUND: {found_version}")

        # 1. Discordに通知
        send_discord_notification(webhook_url, found_version, found_url)

        # 2. PC側(updater.py)が期待するフォーマット作成
        formatted_value = f"{found_version}: {found_url}"
        
        # 3. GitHub変数を更新
        update_github_variable(formatted_value)

        # 4. 【追加】リポジトリ上のファイル(driver_history.txt)も更新
        with open("driver_history.txt", "w", encoding="utf-8") as f:
            f.write(formatted_value)
    else:
        print(f"No new driver found higher than {current_version}")

if __name__ == "__main__":
    update_driver_history()
