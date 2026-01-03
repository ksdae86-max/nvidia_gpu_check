import os
import re
import requests
from playwright.sync_api import sync_playwright

def send_discord_notification(webhook_url, version, url):
    if not webhook_url: return
    payload = {
        "username": "NVIDIA Driver Bot",
        "embeds": [{"title": "✅ 最新ドライバをブラウザで検知！", "description": f"バージョン: **{version}**\n[ダウンロード]({url})", "color": 5025616}]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def update_driver_history():
    history_file = "driver_history.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    # RTX 4090 / Win11 の検索結果ページ
    target_url = "https://www.nvidia.co.jp/Download/processFind.aspx?psid=120&pfid=1033&osid=135&lid=1&whql=1&isDCH=1"

    with sync_playwright() as p:
        # ブラウザを起動（人間らしく見せるための設定）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            print(f"Navigating to NVIDIA...")
            page.goto(target_url, wait_until="networkidle")
            
            # ページ全体のテキストを取得
            content = page.content()
            versions = re.findall(r'(\d{3}\.\d{2})', content)
            
            if not versions:
                print("No versions found even with browser. Content snippet:")
                print(content[:500])
                return

            latest_val = max([float(v) for v in versions])
            latest_version = f"{latest_val:.2f}"
            
            download_url = f"https://jp.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
            
            print(f"SUCCESS: Found {latest_version}")

            with open(history_file, "w", encoding="utf-8") as f:
                f.write(f"{latest_version}: {download_url}\n")
            
            send_discord_notification(webhook_url, latest_version, download_url)

        except Exception as e:
            print(f"Browser error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    update_driver_history()
