import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "✅ 最新ドライバを特定しました",
            "description": f"バージョン: **{version}**\n[ダウンロードはこちら]({url})",
            "color": 5025616
        }]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def update_driver_history():
    # ターゲットを最新世代（RTX 40/30）に固定
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=120&pfid=1033&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        # 472.12 等の「文字列の罠」にハマらないよう、ページ内の全数字を抽出
        all_numbers = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        if not all_numbers:
            print("No versions found.")
            return

        # 文字列としてではなく、浮動小数点数（float）として最大値を決定
        # 472.12 < 591.59 を数学的に保証する
        latest_val = max([float(v) for v in all_numbers])
        latest_version = f"{latest_val:.2f}"
        
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        print(f"DEBUG: Found versions: {sorted(list(set(all_numbers)), reverse=True)}")
        print(f"DEBUG: Selected latest value: {latest_version}")

        # ファイル書き込み
        with open(history_file, "w", encoding="utf-8") as f:
            f.write(f"{latest_version}: {download_url}\n")
        
        print(f"SUCCESS: Written {latest_version}")
        send_discord_notification(webhook_url, latest_version, download_url)

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
