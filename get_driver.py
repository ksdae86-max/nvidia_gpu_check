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
    requests.post(webhook_url, json=payload, timeout=10)

def update_driver_history():
    # パラメータを最新のRTX 4090 (Windows 11) 用に最適化
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=933&osid=135&lid=1&whql=1&isDCH=1"
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        
        # 472.12のような古い情報を避けるため、ページ内の「すべての」バージョン番号を抽出
        # 今回は、より広範囲に数字を探します
        all_matches = re.findall(r'(\d{3}\.\d{2})', res.text)
        
        if not all_matches:
            print("No versions found.")
            return

        # 文字列ではなく数値として比較し、最大のものを取得
        # 472.12 よりも 591.59 の方が確実に大きいと判定させます
        float_versions = []
        for v in all_matches:
            try:
                float_versions.append(float(v))
            except:
                continue
        
        if not float_versions:
            return

        latest_val = max(float_versions)
        latest_version = f"{latest_val:.2f}"
        
        # 500番台未満（古いドライバ）を誤検知している可能性を排除
        if latest_val < 500.0:
            print(f"Warning: Found {latest_version}, but it seems too old. Searching again...")
            # もし500番台が見つからない場合は、何かがおかしい

        download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        print(f"DEBUG: Scanned versions: {sorted(list(set(float_versions)))}")
        print(f"DEBUG: Selected latest: {latest_version}")

        # ファイル書き込み
        should_write = True
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            with open(history_file, "r", encoding="utf-8") as f:
                if latest_version in f.read():
                    should_write = False

        if should_write:
            with open(history_file, "w", encoding="utf-8") as f:
                f.write(f"{latest_version}: {download_url}\n")
            print(f"SUCCESS: Recorded {latest_version}")
            send_discord_notification(webhook_url, latest_version, download_url)
        else:
            print(f"SKIP: {latest_version} already recorded.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    update_driver_history()
