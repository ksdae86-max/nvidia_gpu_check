import os
import requests

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{
            "title": "💎 最新ドライバを検知！",
            "description": f"バージョン: **{version}**\n[直リンク]({url})",
            "color": 5025616
        }]
    }
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        print(f"Discord Notification Sent: {res.status_code}")
    except Exception as e:
        print(f"Notification Error: {e}")

def check_url_exists(url):
    try:
        # タイムアウトを少し伸ばして安定性を確保
        res = requests.head(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return res.status_code == 200
    except:
        return False

def update_driver_history():
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    # デフォルトの開始地点
    current_version = 0.0
    if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
        with open(history_file, "r") as f:
            try:
                # 591.59: https://... の形式から数字だけ抽出
                line = f.readline()
                current_version = float(line.split(":")[0])
            except:
                current_version = 0.0

    print(f"Checking for updates. Current recorded version: {current_version}")

    found_version = None
    found_url = None

    # 現在のバージョンから +2 メジャーバージョン先までスキャン（例: 591 -> 593）
    start_major = int(current_version) + 2 if current_version > 0 else 593
    
    # 巨大なループになるのを防ぎつつ、効率的にスキャン
    for major in range(start_major, int(current_version) - 1, -1):
        # メジャーバージョンが変わる時は、.99から探し始める
        for minor in range(99, -1, -1):
            v = f"{major}.{minor:02d}"
            
            # すでに持っているバージョン以下ならスキャン終了
            if float(v) <= current_version:
                break
                
            test_url = f"https://jp.download.nvidia.com/Windows/{v}/{v}-desktop-win10-win11-64bit-international-dch-whql.exe"
            
            if check_url_exists(test_url):
                found_version = v
                found_url = test_url
                break
        if found_version: break

    if found_version and float(found_version) > current_version:
        with open(history_file, "w", encoding="utf-8") as f:
            f.write(f"{found_version}: {found_url}\n")
        print(f"NEW DRIVER: {found_version}")
        send_discord_notification(webhook_url, found_version, found_url)
    else:
        print(f"No new driver found higher than {current_version}")

if __name__ == "__main__":
    update_driver_history()
