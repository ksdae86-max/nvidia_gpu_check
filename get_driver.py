import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "✅ 最新ドライバを強制検知しました",
            "description": f"バージョン: **{version}**\n[ダウンロードはこちら]({url})",
            "color": 5025616
        }]
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except:
        pass

def update_driver_history():
    # APIではなく、実際の検索結果ページを直接シミュレート
    # RTX 4090 / Windows 11 の検索結果
    scrape_url = "https://www.nvidia.co.jp/Download/processFind.aspx?psid=120&pfid=1033&osid=135&lid=1&whql=1&isDCH=1"
    
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nvidia.co.jp/Download/index.aspx?lang=jp"
    }
    
    try:
        # 日本語サイト経由でリクエスト
        res = requests.get(scrape_url, headers=headers, timeout=30)
        
        # HTML内に埋もれている全バージョン番号(XXX.XX)をスキャン
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        # それでもダメならグローバルサイトを試す
        if not versions:
            print("JP Site failed. Trying Global Site...")
            global_url = "https://www.nvidia.com/Download/processFind.aspx?psid=120&pfid=1033&osid=135&lid=1&whql=1&isDCH=1"
            res = requests.get(global_url, headers=headers, timeout=30)
            versions = re.findall(r'(\d{3}\.\d{2})', res.text)

        if not versions:
            print("CRITICAL: NVIDIA returned NO data in HTML.")
            # デバッグ用に取得できた文字数を出力
            print(f"Response length: {len(res.text)}")
            return

        # 数値として最大のものを取得
        float_versions = [float(v) for v in versions]
        latest_val = max(float_versions)
        latest_version = f"{latest_val:.2f}"
        
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        print(f"SUCCESS: Found {latest_version}")

        # 書き込み
        with open(history_file, "w", encoding="utf-8") as f:
            f.write(f"{latest_version}: {download_url}\n")
        
        send_discord_notification(webhook_url, latest_version, download_url)

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
