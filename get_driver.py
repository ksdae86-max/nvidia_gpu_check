import requests
import os
import re

def update_driver_history():
    # 40シリーズ、Win11、Game Ready用のAPI
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(api_url, headers=headers, timeout=20)
        # バージョン番号をすべて抽出
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        # 【重要】500未満（472.12など）を徹底排除
        modern_versions = [v for v in versions if float(v) >= 500.0]
        if not modern_versions:
            print("No modern versions found. Stopping.")
            return
            
        latest_version = max(modern_versions, key=float)
        print(f"Latest Version Target: {latest_version}")

        # URL生成と生存確認
        domains = ["jp.download.nvidia.com", "us.download.nvidia.com"]
        download_url = None
        for dom in domains:
            url = f"https://{dom}/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
            if requests.head(url, timeout=10).status_code == 200:
                download_url = url
                break
        
        if not download_url:
            print("Download file not ready yet (404).")
            return

        # 履歴ファイルの読み込み
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing_content = f.read()

        # 【修正点】URLが未登録なら追記
        if download_url not in existing_content:
            with open(history_file, "a") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"SUCCESS: {latest_version} recorded.")
            
            # Discord通知（ここはお持ちの関数を呼び出すか、直書き）
            # send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"Skip: {latest_version} already in history.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
