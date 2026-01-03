import requests
import os
import re

def send_discord_notification(webhook_url, version, url):
    """Discordにリッチな埋め込みメッセージを送信する"""
    if not webhook_url:
        print("Webhook URL not found. Skipping notification.")
        return
    payload = {
        "username": "NVIDIA Driver Bot",
        "avatar_url": "https://www.nvidia.com/favicon.ico",
        "embeds": [{
            "title": "🚀 新しいNVIDIAドライバが公開されました！",
            "description": f"最新バージョン **{version}** の生存を確認しました。\n直リンクをリポジトリに保存しました。",
            "color": 7419530,
            "fields": [
                {"name": "バージョン", "value": f"`{version}`", "inline": True},
                {"name": "配信種別", "value": "Game Ready (DCH)", "inline": True},
                {"name": "ダウンロードリンク", "value": f"[ここをクリックしてダウンロード]({url})"}
            ],
            "footer": {"text": "NVIDIA 自動監視システム"}
        }]
    }
    try:
        res = requests.post(webhook_url, json=payload)
        res.raise_for_status()
        print("Discord notification sent successfully!")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def update_driver_history():
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(api_url, headers=headers, timeout=20)
        versions = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        # 500未満を排除
        modern_versions = [v for v in versions if float(v) >= 500.0]
        if not modern_versions:
            print("No modern versions found. Stopping.")
            return
            
        latest_version = max(modern_versions, key=float)
        print(f"Target Version: {latest_version}")

        # URL生成と生存確認
        domains = ["jp.download.nvidia.com", "us.download.nvidia.com"]
        download_url = None
        for dom in domains:
            url = f"https://{dom}/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
            try:
                if requests.head(url, timeout=10).status_code == 200:
                    download_url = url
                    break
            except:
                continue
        
        if not download_url:
            print(f"File {latest_version} is 404. Skipping.")
            return

        # 履歴チェック
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing_content = f.read()

        # URLが履歴になければ実行
        if download_url not in existing_content:
            with open(history_file, "a") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"SUCCESS: {latest_version} recorded.")
            
            # 通知実行
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"Skip: {latest_version} already in history.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
