import requests
import os
import re

def update_driver_history():
    # Microsoft wingetリポジトリの特定のディレクトリにあるファイル/フォルダ一覧を取得するAPI
    # これならHTMLを解析する必要がなく、JSONでフォルダ名（バージョン）が返ってきます
    api_url = "https://api.github.com/repos/microsoft/winget-pkgs/contents/manifests/n/Nvidia/GeForceDriver/GameReady"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # 1. APIを叩いてフォルダ一覧を取得
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        items = response.json()
        
        # 2. フォルダ名の中から「数字.数字」の形式（例: 566.36）をすべて抽出
        versions = []
        for item in items:
            if item['type'] == 'dir':
                name = item['name']
                if re.match(r'^\d{3}\.\d{2}$', name):
                    versions.append(name)
        
        if not versions:
            print("バージョンフォルダが見つかりませんでした。")
            return

        # 3. 最大の数値（最新版）を特定
        latest_version = sorted(versions, reverse=True)[0]
        
        # 4. 公式URLを組み立て
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        new_entry = f"{latest_version}: {download_url}"

        # 5. 履歴保存
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if latest_version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: 最新バージョン {latest_version} を取得しました。")
        else:
            print(f"更新なし: すでに最新 ({latest_version}) を記録済みです。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    update_driver_history()
