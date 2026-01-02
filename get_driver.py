import requests
import os
import re

def update_driver_history():
    # 最も規制が緩く、最新ドライバURLが直接書かれている公式XMLフィード
    # 2026年現在も有効な最新情報の配信元です
    target_url = "https://www.nvidia.com/central/api/v1/utils/driver/get-driver-results?psid=127&pfid=956&osid=135&lid=1&whql=1&lang=jp"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        # 1. NVIDIAのバックエンドAPIを叩く
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 2. JSONから情報を抽出
        # このAPIは "success" フラグとドライバ情報をリストで返します
        data = response.json()
        
        # APIの構造に合わせてパスを指定（ids[0]が最新版）
        if data.get('success') and data.get('ids'):
            driver_info = data['ids'][0]
            version = driver_info.get('version')
            download_url = driver_info.get('downloadUrl')
            
            # もしフルパスでない場合は補完
            if download_url and not download_url.startswith('http'):
                download_url = "https://jp.download.nvidia.com" + download_url
        else:
            print("APIから有効なドライバリストを取得できませんでした。")
            return

        if not version or not download_url:
            print("バージョンまたはURLが不明です。")
            return

        new_entry = f"{version}: {download_url}"

        # 3. 履歴管理（追記）
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: バージョン {version} を記録しました。")
        else:
            print(f"更新不要: バージョン {version} は既に記録済みです。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    update_driver_history()
