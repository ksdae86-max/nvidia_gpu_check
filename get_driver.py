import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Bot",
        "embeds": [{"title": "🚀 Driver Updated", "description": f"Ver: **{version}**\n[Download]({url})", "color": 7419530}]
    }
    requests.post(webhook_url, json=payload)

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

        # 抜け漏れ防止：ファイルが存在しない、または中身が空なら強制書き込み
        should_write = True
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            with open(history_file, "r", encoding="utf-8") as f:
                content = f.read()
                if latest_version in content:
                    should_write = False

        if should_write:
            # "w"モードで確実に最新の状態を書き込む
            with open(history_file, "w", encoding="utf-8") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"DONE: Written {latest_version}")
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"SKIP: {latest_version} already exists")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
