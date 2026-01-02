import requests
import os
import re

def update_driver_history():
    # 公式サイトが内部的に「最新のドライバURL」を特定するために使うPOSTリクエストのエンドポイント
    # GETではなくPOSTを使うことで、サーバー側のガードを突破します
    target_url = "https://www.nvidia.co.jp/Download/processDriver.aspx"
    
    # RTX 4060, Windows 11用のパラメータ
    payload = {
        "psid": "127",
        "pfid": "956",
        "osid": "135",
        "lid": "18", # 日本語
        "dtid": "1", # Game Ready
        "whql": "1",
        "lang": "jp"
    }

    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Origin": "https://www.nvidia.co.jp",
        "Referer": "https://www.nvidia.co.jp/Download/index.aspx?lang=jp",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        # POSTメソッドでリクエストを送る
        # allow_redirects=True にすることで、最終的なダウンロードページまで追いかけます
        response = requests.post(target_url, data=payload, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        final_url = response.url
        print(f"到達URL: {final_url}")

        # URLからバージョン番号（例：566.36）を抽出
        version_match = re.search(r'(\d{3}\.\d{2})', final_url)
        
        if not version_match:
            # もしURLになければ、HTMLの中身から探す
            version_match = re.search(r'(\d{3}\.\d{2})', response.text)

        if version_match:
            version = version_match.group(1)
            # 公式ダウンロードサーバーの直リンクを組み立て
            download_url = f"https://us.download.nvidia.com/Windows/{version}/{version}-desktop-win10-win11-64bit-international-dch-whql.exe"
            
            new_entry = f"{version}: {download_url}"

            # 履歴管理
            existing_content = ""
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            if version not in existing_content:
                with open(history_file, "a", encoding="utf-8") as f:
                    f.write(new_entry + "\n")
                print(f"成功: {version} を記録しました。")
            else:
                print(f"更新不要: すでに最新 ({version}) です。")
        else:
            print("解析失敗: バージョン情報を特定できませんでした。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    update_driver_history()
