import os
import requests

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{"title": "💎 最新ドライバを直撃検知！", "description": f"バージョン: **{version}**\n[直リンク]({url})", "color": 5025616}]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def check_url_exists(url):
    try:
        # HEADリクエストでファイルの存在だけを高速確認
        res = requests.head(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return res.status_code == 200
    except:
        return False

def update_driver_history():
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    # 591.xx を中心に、周辺の数字を総当たりで確認
    # バージョンが上がった時にも対応できるよう、現在の最新付近をスキャン
    base_major = 591
    start_minor = 70  # 現在の591.59より上からスタート
    end_minor = 50    # 下に向かってスキャン
    
    print(f"Scanning for live download links...")
    
    found_version = None
    found_url = None

    # 最新から順に下に向かって、URLが実在するかチェック
    # (例: 591.65, 591.64, ... 591.59)
    for minor in range(start_minor, end_minor - 1, -1):
        v = f"{base_major}.{minor:02d}"
        test_url = f"https://jp.download.nvidia.com/Windows/{v}/{v}-desktop-win10-win11-64bit-international-dch-whql.exe"
        
        print(f"Checking {v}...", end="\r")
        if check_url_exists(test_url):
            found_version = v
            found_url = test_url
            break

    if not found_version:
        # 万が一見つからない場合は、今の確定版 591.59 をセット
        found_version = "591.59"
        found_url = f"https://jp.download.nvidia.com/Windows/591.59/591.59-desktop-win10-win11-64bit-international-dch-whql.exe"

    print(f"\nTarget found: {found_version}")

    with open(history_file, "w", encoding="utf-8") as f:
        f.write(f"{found_version}: {found_url}\n")
    
    send_discord_notification(webhook_url, found_version, found_url)

if __name__ == "__main__":
    update_driver_history()
