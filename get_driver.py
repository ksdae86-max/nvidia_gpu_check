import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "✅ 最新ドライバを検知しました",
            "description": f"バージョン: **{version}**\n[ダウンロードはこちら]({url})",
            "color": 5025616 # NVIDIA Greenに近い色
        }]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def update_driver_history():
    # 最新GeForce RTX 40/30シリーズ向けのAPI URL
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        # バージョン番号（例：591.59）を抽出
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        if not versions:
            print("No versions found in API response.")
            return

        # 重複を排除して数値の高い順にソート
        unique_versions = sorted(list(set(versions)), key=lambda x: float(x), reverse=True)
        
        # 400番台は古いので、500番台以上があればそれを優先する
        modern_versions = [v for v in unique_versions if float(v) >= 500.0]
        latest_version = modern_versions[0] if modern_versions else unique_versions[0]
        
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        print(f"DEBUG: Found latest version: {latest_version}")

        # ファイル書き込み判定
        should_write = True
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            with open(history_file, "r", encoding="utf-8") as f:
                if latest_version in f.read():
                    should_write = False

        if should_write:
            with open(history_file, "w", encoding="utf-8") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"SUCCESS: Recorded {latest_version}")
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"SKIP: {latest_version} already recorded.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
