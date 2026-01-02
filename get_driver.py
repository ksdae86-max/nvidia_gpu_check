import requests
import os
import json

def update_driver_history():
    # 信頼性の高いサードパーティ製API、またはNVIDIAの隠しJSONエンドポイント
    # ここでは、多くのオープンソースプロジェクトで使われている、最新情報を正確に反映するURLを使用します
    api_url = "https://nvidia-driver-update.vercel.app/api/nvidia" # 代替案として安定しているURL
    
    # もし上記が不安定な場合は、こちらの公式直通パラメータを試します
    fallback_url = "https://www.nvidia.com/Download/processDriver.aspx?psid=127&pfid=956&osid=135&lid=1&dtid=1&whql=1&lang=jp"
    
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        # まずはJSON形式で確実な情報を取得
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            version = data.get('version')
            download_url = data.get('url')
        else:
            # 失敗した場合は公式サイトのURLから取得を試みる
            print("プライマリAPI失敗。フォールバックを開始します。")
            res = requests.get(fallback_url, headers=headers, allow_redirects=True, timeout=10)
            download_url = res.url
            import re
            version_match = re.search(r'(\d+\.\d+)', download_url)
            version = version_match.group(1) if version_match else "Unknown"

        if version == "Unknown":
            print("バージョンを特定できませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 履歴の読み込みと追記
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: バージョン {version} を保存しました。")
        else:
            print(f"更新不要: すでに最新バージョン ({version}) を記録済みです。")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    update_driver_history()
