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
        pass

def update_driver_history():
    # NVIDIAの公式検索API
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        # バージョン番号（例：591.59）を探す
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        # リストが空だった場合のガード
        if not versions:
            print("API response did not contain any versions.")
            # ログにレスポンスの一部を出して原因調査しやすくする
            print(f"Response snippet: {res.text[:200]}")
            return
        
        # 数値として最大のものを取得
        latest_version = max(versions, key=lambda x: float(x))
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        # 常に最新を記録するように判定
        should_write = True
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            with open(history_file, "r", encoding="utf-8") as f:
                content = f.read()
                if latest_version in content:
                    should_write = False

        if should_write:
            with open(history_file, "w", encoding="utf-8") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"SUCCESS: {latest_version} written.")
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"SKIP: {latest_version} is already current.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
