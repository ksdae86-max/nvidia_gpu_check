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
            "color": 7419530, # NVIDIA Greenっぽい色
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
    # ターゲット: RTX 40シリーズ(汎用), Win11, Game Ready(whql=1), DCH
    # pfid=933 に広げることで、4060単体指定(956)より新しいデータが降りてきやすくなります
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,*/*;q=0.8",
        "Referer": "https://www.nvidia.com/Download/index.aspx"
    }

    try:
        print("Connecting to NVIDIA Release API (Focusing on Latest Game Ready)...")
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        content = response.text
        
       # すべてのバージョン（XXX.XX）を抽出
        all_versions = re.findall(r'(\d{3}\.\d{2})', content)

        if not all_versions:
            print(f"DEBUG: Content Snippet: {content[:500]}")
            raise ValueError("Driver version pattern not found.")

        # --- 修正ポイント：500番台以上の現行ドライバのみにフィルタリング ---
        # 400番台（472.12など）を完全に無視します
        modern_versions = [v for v in all_versions if float(v) >= 500.0]

        if not modern_versions:
            # もし500番台が見つからない場合は、仕方なく全体から最大値を取る（保険）
            latest_version = max(all_versions, key=float)
        else:
            # 500番台の中で最大のものを採用
            latest_version = max(modern_versions, key=float)

        print(f"Latest Modern Game Ready Version Found: {latest_version}")

        # --- ここから書き換え ---
        # 1. 日本(JP)サーバーを優先し、2. 米国(US)サーバーを予備とする
        domains = ["jp.download.nvidia.com", "us.download.nvidia.com"]
        file_name = f"{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        
        download_url = None
        for domain in domains:
            test_url = f"https://{domain}/Windows/{latest_version}/{file_name}"
            print(f"Checking URL on {domain}: {test_url}")
            try:
                check_res = session.head(test_url, headers=headers, allow_redirects=True, timeout=10)
                if check_res.status_code == 200:
                    download_url = test_url
                    print(f"VALID: Match Found on {domain}!")
                    break
            except Exception as e:
                print(f"Server {domain} check failed: {e}")

        if not download_url:
            print(f"Link is 404 on all servers. Waiting for NVIDIA to upload the file...")
            return # 関数を抜ける（保存・通知処理をスキップ）
        
        if check_res.status_code == 200:
            # 履歴チェック
            existing = ""
            if os.path.exists(history_file):
                with open(history_file, "r") as f: existing = f.read()

            if latest_version not in existing:
                # 1. 履歴保存
                with open(history_file, "a") as f:
                    f.write(f"{latest_version}: {download_url}\n")
                
                # 2. Discord通知
                if webhook_url:
                    send_discord_notification(webhook_url, latest_version, download_url)
                
                # 3. GitHub出力
                if "GITHUB_OUTPUT" in os.environ:
                    with open(os.environ["GITHUB_OUTPUT"], "a") as o:
                        o.write(f"updated=true\n")
                print(f"SUCCESS: {latest_version} recorded and notified.")
            else:
                print(f"NO CHANGE: {latest_version} already exists.")
        else:
            print(f"Link is 404. Waiting for NVIDIA to upload the file...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
