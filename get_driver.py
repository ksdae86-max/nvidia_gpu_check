import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import json

def update_driver_history():
    # ターゲット: RTX 4060, Win11, Game Ready (DCH)
    # lid=1(English), lid=1041(Japanese) だが、データの更新が最も早いのは lid=1
    api_url = "https://www.nvidia.com/Download/API/lookupValueSearch.aspx?typeID=3&psid=127&pfid=956&osid=135&lid=1&isDCH=1&dtcid=1"
    history_file = "driver_history.txt"
    
    # セッションと指数バックオフによるリトライ設定
    session = requests.Session()
    retries = Retry(
        total=5, 
        backoff_factor=2, # 失敗するごとに待ち時間を増やす (2s, 4s, 8s...)
        status_forcelist=[403, 429, 500, 502, 503, 504]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.nvidia.com/Download/index.aspx",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        print(f"Connecting to NVIDIA API...")
        response = session.get(api_url, headers=headers, timeout=(10, 30))
        
        # 403 Forbidden対策: 
        # もしActionsのIPが一時的に弾かれた場合、ここで詳細なエラーを出して停止させる
        response.raise_for_status()
        
        # BOM(Byte Order Mark)対策とデコード
        response.encoding = response.apparent_encoding
        content = response.text.strip()
        
        if not content:
            print("Error: Empty response from API")
            return

        data = json.loads(content)

        if not isinstance(data, list) or len(data) == 0:
            print(f"Warning: Unexpected data format or empty list. Content: {content[:100]}")
            return

        # 最新バージョンを取得 (APIの[0]番目が通常最新)
        latest_version = data[0].get('Value')
        if not latest_version:
            print("Error: Could not find 'Value' key in API response.")
            return
            
        # URL組み立て (us.download が最も安定)
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        new_entry = f"{latest_version}: {download_url}"

        # 履歴ファイルの読み込み (存在しない場合は空)
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = f.read()
        else:
            history = ""

        # 重複チェック (バージョン番号が含まれているか)
        if latest_version not in history:
            # 追記モードで保存
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"SUCCESS: Found new version {latest_version}")
            # Actionsのステップ間で使えるように環境変数にセット（オプション）
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as out:
                    out.write(f"new_driver=true\nversion={latest_version}\n")
        else:
            print(f"NO CHANGE: Version {latest_version} already exists in history.")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - Action might be blocked by NVIDIA WAF.")
    except json.JSONDecodeError:
        print(f"JSON Parse Error: API returned non-JSON content. Snippet: {response.text[:100]}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    update_driver_history()
