import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "🚀 新しいNVIDIAドライバを記録しました",
            "description": f"バージョン: **{version}**\n[ダウンロードはこちら]({url})",
            "color": 7419530
        }]
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except:
        print("Notification failed, but moving on.")

def update_driver_history():
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        if not versions: return
        
        latest_version = max([v for v in versions if float(v) >= 500.0], key=float)
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        # 物理的な書き込み判定：
        # 1. ファイルが存在しない
        # 2. ファイルサイズが0（空）
        # 3. ファイルの中に最新バージョンが書かれていない
        should_write = True
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            with open(history_file, "r", encoding="utf-8") as f:
                if latest_version in f.read():
                    should_write = False

        if should_write:
            # 確実に新規作成/上書きするために "w" モードを使用
            with open(history_file, "w", encoding="utf-8") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"SUCCESS: {latest_version} written to file.")
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"SKIP: {latest_version} is already recorded.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
