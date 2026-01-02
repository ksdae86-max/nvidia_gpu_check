import requests
import os
import re

def update_driver_history():
    # Microsoft公式のwingetリポジトリで、NVIDIAドライバの最新バージョンを管理しているディレクトリページ
    # GitHubのAPIやRawページは、Actionsから100%アクセス可能です
    search_url = "https://github.com/microsoft/winget-pkgs/tree/master/manifests/n/Nvidia/GeForceDriver/GameReady"
    
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # 1. wingetのリポジトリページを取得
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 2. HTMLからバージョン番号（5xx.xx形式）をすべて抽出
        versions = re.findall(r'(\d{3}\.\d{2})', response.text)
        
        if not versions:
            print("wingetリポジトリからバージョンを抽出できませんでした。")
            return

        # 3. 最も大きい数字（最新版）を特定
        latest_version = sorted(list(set(versions)), reverse=True)[0]
        
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
        print(f"致命的なエラー: {e}")

if __name__ == "__main__":
    update_driver_history()
