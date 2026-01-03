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
            "color": 5025616
        }]
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except:
        pass

def update_driver_history():
    # 特定のIDに頼らず、より広範な情報を返すAPIエンドポイントを使用
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=120&pfid=1033&osid=135&lid=1&whql=1&isDCH=1"
    # 予備のAPI (GeForce全体を対象にする)
    backup_url = "https://www.nvidia.com/Download/processFind.aspx?psid=120&pfid=1033&osid=57&lid=1&whql=1&isDCH=1"
    
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    try:
        # まずメインのURLを試す
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        all_numbers = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        # もし空なら予備のURLを試す
        if not all_numbers:
            print("Primary API failed, trying backup...")
            res = requests.get(backup_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            all_numbers = re.findall(r'(\d{3}\.\d{2})', res.text)

        if not all_numbers:
            print("FATAL: Both APIs returned no data. Check NVIDIA site status.")
            return

        # 数値として最大のものを取得（591.59 > 472.12）
        float_versions = [float(v) for v in all_numbers]
        latest_val = max(float_versions)
        latest_version = f"{latest_val:.2f}"
        
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        print(f"DEBUG: All found versions: {sorted(list(set(float_versions)), reverse=True)[:5]}")
        print(f"DEBUG: Selected latest: {latest_version}")

        # 強制的に最新を書き込む
        with open(history_file, "w", encoding="utf-8") as f:
            f.write(f"{latest_version}: {download_url}\n")
        
        print(f"SUCCESS: Written {latest_version}")
        send_discord_notification(webhook_url, latest_version, download_url)

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
