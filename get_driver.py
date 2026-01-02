import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import re

def update_driver_history():
    # ターゲット: RTX 4060, Win11, Game Ready Driver
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=956&osid=135&lid=1&whql=1&isDCH=1&dtcid=1"
    history_file = "driver_history.txt"
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # ブラウザからのアクセスを装う（重要）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Referer": "https://www.nvidia.com/Download/index.aspx"
    }

    try:
        print("Connecting to NVIDIA Release API (Hybrid Mode)...")
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        
        content = response.text
        latest_version = None

        # --- ブラッシュアップ11: HTML/XML両対応の正規表現 ---
        # 1. <ReleaseVersion>XXX.XX</ReleaseVersion> 形式 (XML)
        # 2. >XXX.XX< (HTMLのタグに挟まれている場合)
        # 3. バージョン番号単体 (テキスト)
        patterns = [
            r'<ReleaseVersion>(\d{3}\.\d{2})</ReleaseVersion>',
            r'Version\s*[:：]\s*(\d{3}\.\d{2})',
            r'>(\d{3}\.\d{2})<',
            r'(\d{3}\.\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                latest_version = match.group(1)
                # 明らかに違う数値(10.0など)を除外するため、500番台以上であることを確認
                if float(latest_version) > 400.0:
                    break
        
        if not latest_version:
            print(f"DEBUG: Content Snippet: {content[:500]}")
            raise ValueError("Driver version pattern not found in response.")

        print(f"Found Version: {latest_version}")

        # URL生成
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        new_entry = f"{latest_version}: {download_url}"

        # 履歴読み込みと保存
        existing = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing = f.read()

        if latest_version not in existing:
            with open(history_file, "a") as f:
                f.write(new_entry + "\n")
            print(f"SUCCESS: {latest_version} recorded.")
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as o:
                    o.write(f"updated=true\nversion={latest_version}\n")
        else:
            print(f"NO CHANGE: {latest_version} already exists.")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    update_driver_history()
