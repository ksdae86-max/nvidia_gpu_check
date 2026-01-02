import requests
import os
import re

def update_driver_history():
    # NVIDIAのダウンロードサーバーのルートに近いインデックスページ
    # ここはボット制限が緩く、かつ全てのドライバがリストされています
    target_url = "https://jp.download.nvidia.com/Windows/"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # 1. サーバーのファイルリストを取得
        response = requests.get(target_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        # 2. ページ内の「5xx.xx」という形式のフォルダ名をすべて探す
        # HTML内の <a href="566.36/"> のような記述を抽出します
        versions = re.findall(r'(\d{3}\.\d{2})', response.text)
        
        if not versions:
            print("サーバーからバージョンリストを取得できませんでした。")
            return

        # 3. 数値として最大のものが最新版
        # 文字列のリストなので、重複を消してソート
        latest_version = sorted(list(set(versions)), reverse=True)[0]
        
        # 4. 公式のURL規則に従ってダウンロードリンクを生成
        download_url = f"https://us.download.nvidia.com/Windows/{latest_version}/{latest_version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        new_entry = f"{latest_version}: {download_url}"

        # 5. 履歴の保存
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if latest_version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: 最新バージョン {latest_version} を記録しました。")
        else:
            print(f"更新不要: すでに最新 ({latest_version}) です。")

    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")

if __name__ == "__main__":
    update_driver_history()
