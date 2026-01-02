import requests
import os
import re

def update_driver_history():
    # パスを小文字(nvidia)に修正し、最新バージョンが格納されている最深部を狙います
    # ※ wingetリポジトリの構造：n > Nvidia > GeForceDriver > GameReady
    api_url = "https://api.github.com/repos/microsoft/winget-pkgs/contents/manifests/n/Nvidia/GeForceDriver/GameReady"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # 1. GitHub APIでフォルダ一覧を取得
        response = requests.get(api_url, headers=headers, timeout=15)
        
        # もし404なら「nvidia」を小文字にしてリトライ
        if response.status_code == 404:
            api_url = api_url.replace("Nvidia", "nvidia")
            response = requests.get(api_url, headers=headers, timeout=15)

        response.raise_for_status()
        items = response.json()
        
        # 2. フォルダ名からバージョン番号（XXX.XX）を抽出
        versions = []
        for item in items:
            name = item['name']
            # 512.34 や 566.36 などの形式にマッチ
            if re.match(r'^\d{3}\.\d{2}$', name):
                versions.append(name)
        
        if not versions:
            print("バージョンフォルダが見つかりませんでした。")
            return

        # 3. 最新（最大の数字）を取得
        latest_version = sorted(versions, reverse=True)[0]
        
        # 4. 公式URLを構成
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
            print(f"更新なし: {latest_version} は記録済みです。")

    except Exception as e:
        print(f"致命的なエラー: {e}")

if __name__ == "__main__":
    update_driver_history()
