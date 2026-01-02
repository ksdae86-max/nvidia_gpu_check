import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import xml.etree.ElementTree as ET

def update_driver_history():
    # ターゲット: RTX 4060, Win11, Game Ready (DCH)
    api_url = "https://www.nvidia.com/Download/API/lookupValueSearch.aspx?typeID=3&psid=127&pfid=956&osid=135&lid=1&isDCH=1&dtcid=1"
    history_file = "driver_history.txt"
    
    # 1. ネットワークセッションの構築
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=2, status_forcelist=[403, 429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # ブラウザを装うヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.nvidia.com/Download/index.aspx"
    }

    try:
        print(f"Connecting to NVIDIA API...")
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        
        # 2. XMLのパース
        # XMLから <LookupValue Value="XXX.XX" /> の Value 属性をすべて抽出
        try:
            root = ET.fromstring(response.content)
            # 全階層から LookupValue タグを探す
            version_elements = root.findall(".//LookupValue")
            versions = [el.get('Value') for el in version_elements if el.get('Value')]
        except ET.ParseError as pe:
            print(f"XML Parse Error: {pe}. Raw Content: {response.text[:200]}")
            return

        if not versions:
            print("No versions found in XML response.")
            return

        # 3. バージョンの正規化とソート (最新を確実に取得)
        # 文字列のまま比較すると狂うことがあるため、数値リストとしてソート
        latest_version = sorted(versions, key=lambda x: [int(i) for i in x.split('.')], reverse=True)[0]
        print(f"Latest Detected Version: {latest_version}")

        # 4. URL生成
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        new_entry = f"{latest_version}: {download_url}"

        # 5. 履歴の管理（完全一致チェック）
        existing_versions = set()
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    # 行の先頭にあるバージョン番号（566.36など）を抽出
                    if ":" in line:
                        existing_versions.add(line.split(":")[0].strip())

        # 6. 更新判定と保存
        if latest_version not in existing_versions:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"SUCCESS: New version {latest_version} added to history.")
            
            # GitHub Actions用：後のステップで判定できるように出力
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as env_file:
                    env_file.write(f"updated=true\nversion={latest_version}\n")
        else:
            print(f"NO CHANGE: Version {latest_version} is already in history.")
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as env_file:
                    env_file.write(f"updated=false\n")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    update_driver_history()
