import os
import requests

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{"title": "💎 最新ドライバを検知！", "description": f"バージョン: **{version}**\n[ダウンロード]({url})", "color": 5025616}]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def check_url_exists(url):
    try:
        res = requests.head(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
        return res.status_code == 200
    except:
        return False

def update_driver_history():
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    # 現在の記録を読み取る（スキャンの開始地点を決めるため）
    current_version = 591.59
    if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
        with open(history_file, "r") as f:
            try:
                current_version = float(f.read().split(":")[0])
            except:
                pass

    # 現在のメジャーバージョン（591など）の前後をスキャン
    # 例：591.59なら、592.10 から 591.00 まで下向きに探す
    base_major = int(current_version)
    found_version = None
    found_url = None

    print(f"Scanning for updates starting from {base_major + 1}...")

    # メジャーバージョンを+1まで許容してスキャン
    for major in [base_major + 1, base_major]:
        for minor in range(99, -1, -1):
            v = f"{major}.{minor:02d}"
            test_url = f"https://jp.download.nvidia.com/Windows/{v}/{v}-desktop-win10-win11-64bit-international-dch-whql.exe"
            
            # 既に知っているバージョンより下は探さない
            if float(v) <= current_version and major == base_major:
                # 既知の最新版（591.59）が見つかったら終了
                found_version = f"{current_version:.2f}"
                found_url = f"https://jp.download.nvidia.com/Windows/{found_version}/{found_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
                break

            if check_url_exists(test_url):
                found_version = v
                found_url = test_url
                break
        if found_version: break

    # ファイル更新と通知
    if found_version and (float(found_version) > current_version):
        with open(history_file, "w", encoding="utf-8") as f:
            f.write(f"{found_version}: {found_url}\n")
        print(f"NEW DRIVER FOUND: {found_version}")
        send_discord_notification(webhook_url, found_version, found_url)
    else:
        print(f"No new driver. Current: {current_version}")

if __name__ == "__main__":
    update_driver_history()
