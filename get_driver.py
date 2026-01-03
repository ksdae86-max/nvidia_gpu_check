import requests
import os
import re

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
        
        # URLの生成
        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        # 【修正ポイント】既存のチェックをあえて甘くし、
        # ファイルが空だったり、URLが含まれていなければ必ず書き込む
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing_content = f.read().strip()

        # ファイルが空、または今回のURLが入っていないなら書き込む
        if not existing_content or (download_url not in existing_content):
            with open(history_file, "w") as f: # "a"（追記）ではなく"w"（上書き）で確実に書く
                f.write(f"{latest_version}: {download_url}\n")
            print(f"FORCED WRITE: {latest_version} recorded.")
            
            # 通知用のダミー関数や実際の通知処理をここに
        else:
            print(f"Skip: {latest_version} already in file.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
