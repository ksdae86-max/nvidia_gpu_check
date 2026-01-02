import requests
import os

def update_driver_history():
    # 新しいAPIエンドポイント (RTX 4060, Win11, Game Ready)
    # psid=127 (RTX 40), pfid=956 (4060), osid=135 (Win11), dtid=1 (Game Ready)
    api_url = "https://www.nvidia.com/Download/processDriver.aspx?psid=127&pfid=956&osid=135&lid=1&dtid=1&whql=1&lang=jp"
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        # このAPIはリダイレクト先が実際のダウンロードURLになることが多い
        response = requests.get(api_url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        # 最終的なURLを取得
        download_url = response.url
        
        # URLからバージョン番号を抽出 (例: .../566.36-desktop-...)
        import re
        version_match = re.search(r'/(\d+\.\d+)-', download_url)
        version = version_match.group(1) if version_match else "Unknown"

        new_entry = f"{version}: {download_url}"

        # 既存の履歴を確認
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if version != "Unknown" and version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: バージョン {version} を追記しました。")
        else:
            print(f"更新なし (現在のバージョン: {version})")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    update_driver_history()
