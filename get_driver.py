import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import re
import xml.etree.ElementTree as ET

def update_driver_history():
    # 本物の最新ドライバ情報を返す検索結果用API
    # psid=127 (RTX 40 Series), pfid=956 (RTX 4060), osid=135 (Win11), dtcid=1 (Game Ready)
    api_url = "https://www.nvidia.com/Download/processFind.aspx?psid=127&pfid=956&osid=135&lid=1&whql=1&isDCH=1&dtcid=1"
    history_file = "driver_history.txt"
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=2, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.nvidia.com/Download/index.aspx"
    }

    try:
        print("Connecting to NVIDIA Release API...")
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        
        latest_version = None
        
        # 1. XMLとしてパース
        try:
            root = ET.fromstring(response.content)
            # 全階層から ReleaseVersion タグを探す
            for el in root.iter():
                if el.tag.endswith('ReleaseVersion'):
                    v = el.text.strip() if el.text else ""
                    if re.match(r'^\d+\.\d+$', v):
                        latest_version = v
                        break
        except Exception as e:
            print(f"XML Parsing failed, falling back to Regex: {e}")

        # 2. 正規表現によるバックアップ抽出
        if not latest_version:
            match = re.search(r'<ReleaseVersion>(\d+\.\d+)</ReleaseVersion>', response.text)
            if match:
                latest_version = match.group(1)

        if not latest_version:
            print(f"Error: Version not found. Content start: {response.text[:200]}")
            return

        print(f"Detected Version: {latest_version}")

        # URL生成 (国際版DCHドライバ形式)
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        new_entry = f"{latest_version}: {download_url}"

        # 履歴の読み込み（重複防止）
        existing_versions = set()
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        existing_versions.add(line.split(":")[0].strip())

        # 3. 更新・保存処理
        if latest_version not in existing_versions:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"SUCCESS: Version {latest_version} added to history.")
            
            # GitHub Actions用出力
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as env_file:
                    env_file.write(f"updated=true\nversion={latest_version}\n")
        else:
            print(f"NO CHANGE: Version {latest_version} is already recorded.")
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as env_file:
                    env_file.write(f"updated=false\n")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    update_driver_history()
