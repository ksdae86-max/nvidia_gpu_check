import requests
import os
import re

def update_driver_history():
    # 手法を変更：NVIDIAのダウンロードサーバーに直接存在する「最新バージョンのテキスト」を読みに行く
    # このファイルはGeForce Experienceが更新チェックに使う生データの一つです
    target_url = "https://gfwsl.geforce.com/services_nvd/lookup/v1/type/3/id/135/is_beta/0/is_whql/1/language/1041/gpubid/956/direct/1"
    
    # 予備の取得先（サードパーティ製ミラーサイトの最新情報ページ）
    backup_url = "https://www.techpowerup.com/download/nvidia-geforce-graphics-drivers/"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        # ステップ1: サードパーティサイトからスクレイピング（ここは比較的緩い）
        response = requests.get(backup_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        # HTMLからバージョン番号を抽出 (例: 566.36)
        html = response.text
        # "Version: 566.36" というパターンを探す
        match = re.search(r'Version\s*</span>\s*(\d{3}\.\d{2})', html)
        
        if match:
            version = match.group(1)
            # URLは公式の配布パターンに基づいて生成（これが一番確実）
            # NVIDIAの配布URLはバージョン番号さえわかれば固定ルールで構成可能です
            download_url = f"https://us.download.nvidia.com/Windows/{version}/{version}-desktop-win10-win11-64bit-international-dch-whql.exe"
        else:
            print("ミラーサイトからもバージョンを特定できませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 履歴の保存処理
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: {version} を保存しました。")
        else:
            print(f"更新なし: {version} は既に記録済みです。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    update_driver_history()
