import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "✅ 最新ドライバを検知！",
            "description": f"バージョン: **{version}**\n[ダウンロードはこちら]({url})",
            "color": 5025616
        }]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def update_driver_history():
    # 以前使っていた www.nvidia.com ではなく、アプリ専用の別ドメインを使用
    url = "https://gfwsl.geforce.com/services_v1/renderer.php?func=gfe_product_finder&psid=120&pfid=1033&osid=135&lid=1&whql=1&isDCH=1"
    
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    # GeForce Experience アプリ本体のふりをする
    headers = {
        "User-Agent": "NVIDIA GeForce Experience/3.27.0.120",
        "Accept": "*/*"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=30)
        
        # 1. 取得データをログに出して「中身が空でないか」を10回以上検証するためのデバッグ
        print(f"DEBUG: Response length: {len(res.text)}")
        
        # 2. バージョン番号（591.59など）をすべて抜き出す
        all_versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        if not all_versions:
            # 3. もしダメなら、以前失敗したウェブ用APIとは「別の」予備パラメータを試す
            print("GFE Domain failed. Trying backup parameters...")
            backup_url = url.replace("osid=135", "osid=57") # Win10版
            res = requests.get(backup_url, headers=headers, timeout=30)
            all_versions = re.findall(r'(\d{3}\.\d{2})', res.text)

        if not all_versions:
            print("CRITICAL: All methods failed to find version numbers.")
            return

        # 数値として最大のものを取得
        latest_val = max([float(v) for v in all_versions])
        latest_version = f"{latest_val:.2f}"
        
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        print(f"DEBUG: Scanned versions: {sorted(list(set(all_versions)), reverse=True)[:3]}")
        print(f"SUCCESS: {latest_version} found.")

        # ファイルに書き込む
        with open(history_file, "w", encoding="utf-8") as f:
            f.write(f"{latest_version}: {download_url}\n")
        
        send_discord_notification(webhook_url, latest_version, download_url)

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
