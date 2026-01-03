import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import re

def send_discord_notification(webhook_url, version, url):
    """Discordにリッチな埋め込みメッセージを送信する"""
    payload = {
        "username": "NVIDIA Driver Bot",
        "avatar_url": "https://www.nvidia.com/favicon.ico",
        "embeds": [{
            "title": "🚀 新しいNVIDIAドライバが公開されました！",
            "description": f"最新バージョン **{version}** の生存を確認しました。\n直リンクをリポジトリに保存しました。",
            "color": 7419530,
            "fields": [
                {"name": "バージョン", "value": f"`{version}`", "inline": True},
                {"name": "配信種別", "value": "Game Ready (DCH)", "inline": True},
                {"name": "ダウンロードリンク", "value": f"[ここをクリックしてダウンロード]({url})"}
            ],
            "footer": {"text": "NVIDIA 自動監視システム"}
        }]
    }
    try:
        res = requests.post(webhook_url, json=payload)
        res.raise_for_status()
        print("Discord notification sent successfully!")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def update_driver_history():
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        all_versions = re.findall(r'(\d{3}\.\d{2})', response.text)
        
        if not all_versions:
            raise ValueError("Driver version not found.")

        # 500番台以上の最新を取得
        modern_versions = [v for v in all_versions if float(v) >= 500.0]
        latest_version = max(modern_versions, key=float) if modern_versions else max(all_versions, key=float)

        print(f"Target Version: {latest_version}")

        # サーバー探索
        domains = ["jp.download.nvidia.com", "us.download.nvidia.com"]
        file_name = f"{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        download_url = None

        for domain in domains:
            test_url = f"https://{domain}/Windows/{latest_version}/{file_name}"
            try:
                if session.head(test_url, timeout=10).status_code == 200:
                    download_url = test_url
                    break
            except: continue

        if not download_url:
            print("Link is 404. Skipping.")
            return

        # --- 履歴チェック ---
        existing = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing = f.read()

        # バージョンだけでなく、そのURLも含まれているかチェック
        if download_url not in existing:
            # 1. 履歴保存 (追記)
            with open(history_file, "a") as f:
                f.write(f"{latest_version}: {download_url}\n")
            
            # 2. Discord通知
            if webhook_url:
                send_discord_notification(webhook_url, latest_version, download_url)

            # 3. GitHub Actions用出力
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as o:
                    o.write("updated=true\n")
            print(f"SUCCESS: {latest_version} added to history.")
        else:
            print(f"ALREADY EXISTS: {latest_version} with this URL is already in history.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
