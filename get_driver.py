import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import re
import xml.etree.ElementTree as ET

def update_driver_history():
    # NVIDIA公式 API
    api_url = "https://www.nvidia.com/Download/API/lookupValueSearch.aspx?typeID=3&psid=127&pfid=956&osid=135&lid=1&isDCH=1&dtcid=1"
    history_file = "driver_history.txt"
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # ブラウザであることをより強く主張するヘッダー（Sec-CH-UAなど）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/xml,application/xhtml+xml,text/html;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.nvidia.com/Download/index.aspx?lang=en-us",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"Connecting to NVIDIA API...")
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        
        content = response.text
        versions = []

        # 1. XMLとして解析を試みる
        if "<?xml" in content or "<Lookup" in content:
            try:
                # 名前空間などを無視して、とにかく 'Value' 属性を持つタグをすべて抽出
                root = ET.fromstring(response.content)
                for element in root.iter():
                    val = element.get('Value')
                    if val and re.match(r'^\d+\.\d+$', val): # 566.36 のような形式のみ
                        versions.append(val)
            except Exception as e:
                print(f"XML parse failed, trying Regex: {e}")

        # 2. XML解析が失敗、または空の場合、正規表現で強引に抜き出す (最終手段)
        if not versions:
            # Value="566.36" または "Value": "566.36" の形式を探す
            versions = re.findall(r'Value=["\'](\d+\.\d+)["\']', content)

        if not versions:
            print(f"Error: No version pattern found. Content start: {content[:200]}")
            return

        # 最新を抽出
        latest_version = sorted(list(set(versions)), key=lambda x: [int(i) for i in x.split('.')], reverse=True)[0]
        print(f"Detected: {latest_version}")

        # URL生成と保存処理
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        new_entry = f"{latest_version}: {download_url}"

        history = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = f.read()

        if latest_version not in history:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"SUCCESS: Version {latest_version} added.")
        else:
            print(f"NO CHANGE: {latest_version} exists.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_driver_history()
