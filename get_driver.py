import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url:
        return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "🚀 新しいNVIDIAドライバを記録しました",
            "description": f"バージョン: **{version}**\n[ダウンロードはこちら]({url})",
            "color": 7419530
        }]
    }
    requests.post(webhook_url, json=payload)

def update_driver_history():
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(api_url, headers=headers, timeout=20)
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        modern_versions = [v for v in versions if float(v) >= 500.0]

        if not modern_versions:
            return

        latest_version = max(modern_versions, key=float)
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing_content = f.read().strip()

        # ファイルが空、または今回のURLが入っていないなら書き込む
        if not existing_content or (download_url not in existing_content):
            with open(history_file, "w") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"FORCED WRITE: {latest_version} recorded.")
            
            # 通知も飛ばす
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"Skip: {latest_version} already in file.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
