import requests
import os

def update_driver_history():
    # 2026年現在、最も安定している検索APIエンドポイント
    # psid: 127 (RTX 40), pfid: 956 (4060), osid: 135 (Win 11), lang: 7 (JP)
    api_url = "https://gfwsl.geforce.com/services_nvd/lookup/v1/type/3/id/135/is_beta/0/is_whql/1/language/7/gpubid/956/direct/1"
    
    # 別の候補（上記が404の場合に備えて）
    alternate_url = "https://www.nvidia.com/Download/processDriver.aspx?psid=127&pfid=956&osid=135&lid=1&dtid=1&whql=1&lang=jp"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        # まずプライマリAPIを試行
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 404:
            print("API v1が404のため、公式サイト経由の取得を試みます...")
            # 公式サイトの検索結果から直接URLを取得
            response = requests.get(alternate_url, headers=headers, allow_redirects=True, timeout=15)
            download_url = response.url
            # URLからバージョンを抽出
            import re
            version_match = re.search(r'/(\d+\.\d+)/', download_url)
            version = version_match.group(1) if version_match else "Unknown"
        else:
            response.raise_for_status()
            data = response.json()
            version = data.get('version')
            download_url = data.get('downloadUrl')

        if not version or version == "Unknown":
            print("ドライバ情報を特定できませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 履歴管理
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: {version} を保存しました。")
        else:
            print(f"更新なし: {version} は記録済みです。")

    except Exception as e:
        print(f"致命的なエラー: {e}")

if __name__ == "__main__":
    update_driver_history()
