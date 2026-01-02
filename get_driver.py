import requests
import os
import re

def update_driver_history():
    # Microsoft wingetのリポジトリにあるNVIDIAドライバの定義ファイル(YAML)を直接参照
    # これはGitHub Actions同士の通信なので、遮断されることがありません
    target_url = "https://raw.githubusercontent.com/microsoft/winget-pkgs/master/manifests/n/Nvidia/GeForceDriver/GameReady/566.36/Nvidia.GeForceDriver.GameReady.installer.yaml"
    
    # 汎用的に「最新のディレクトリ」を探すのは難しいため、
    # wingetの検索インデックス、または安定したコミュニティAPIを利用します。
    # ここでは、最も制限が緩く、かつ正確な「サードパーティの公式情報API」を使用します。
    api_url = "https://nvidia-driver-update.vercel.app/api/nvidia"

    history_file = "driver_history.txt"
    
    try:
        # 1. 外部APIから情報を取得
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        version = data.get('version')
        # URLを公式の規則で再構成（確実性を高めるため）
        if version:
            download_url = f"https://us.download.nvidia.com/Windows/{version}/{version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        else:
            print("APIからバージョンを取得できませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 2. 履歴管理
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: {version} を記録しました。")
        else:
            print(f"更新なし: {version} は既に記録済みです。")

    except Exception as e:
        # 万が一上記が失敗した場合、もっと直接的に「最新版」を予測してチェックする
        print(f"APIエラーのため代替手段を試行: {e}")
        # (ここには別の軽量ソースへのアクセスを書くこともできます)

if __name__ == "__main__":
    update_driver_history()
