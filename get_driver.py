import requests
import os
import re

def update_driver_history():
    # 検索結果を表示するページ（人間がブラウザで見るのと同じURL）
    search_url = "https://www.nvidia.com/Download/processDriver.aspx?psid=127&pfid=956&osid=135&lid=1&dtid=1&whql=1&lang=1"
    
    history_file = "driver_history.txt"
    # ブラウザであることを強調するための詳細なヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # セッションを使用してクッキーを保持しながらアクセス
        session = requests.Session()
        response = session.get(search_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        html_text = response.text

        # 1. バージョン番号の抽出 (例: 566.36)
        # HTML内の "Version: 566.36" またはそれに類する文字列を探す
        version_match = re.search(r'Version:\s*(\d{3}\.\d{2})', html_text, re.IGNORECASE)
        if not version_match:
            # URLの中にバージョンが含まれているパターンも探す
            version_match = re.search(r'(\d{3}\.\d{2})', html_text)

        # 2. ダウンロードIDまたは直接リンクの抽出
        # driverDetails.aspx?driverid=XXXXX という文字列を探す
        driver_id_match = re.search(r'driverid=(\d+)', html_text)
        
        if version_match and driver_id_match:
            version = version_match.group(1)
            driver_id = driver_id_match.group(1)
            # 詳細ページへのリンクを構成
            download_url = f"https://www.nvidia.com/Download/driverDetails.aspx/jpn/en/{driver_id}"
        else:
            # 最終手段：もし何も見つからなければ、HTMLの一部をログに出してデバッグ
            print("解析失敗：HTML内に情報が見つかりませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 履歴の保存
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
        print(f"エラー: {e}")

if __name__ == "__main__":
    update_driver_history()
