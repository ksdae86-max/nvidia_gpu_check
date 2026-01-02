import requests
import os
import xml.etree.ElementTree as ET

def update_driver_history():
    # NVIDIAが公式に提供している全ドライバのXMLリスト（非常に安定しています）
    # 3=GeForce, 135=Win11 64bit, 1=Game Ready, 1041=Japanese
    api_url = "https://gfwsl.geforce.com/services_nvd/lookup/v1/type/3/id/135/is_beta/0/is_whql/1/language/1041/direct/1"
    
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # JSON形式でデータが返ってくる
        data = response.json()
        
        # 最新のバージョンとURLを抽出
        version = data.get('version')
        download_url = data.get('downloadUrl')

        if not version or not download_url:
            print("APIの応答にドライバ情報が含まれていませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 履歴の読み込み
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        # 重複チェックと追記
        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"成功: バージョン {version} を取得・保存しました。")
        else:
            print(f"更新なし: すでに最新バージョン ({version}) を記録済みです。")

    except Exception as e:
        print(f"通信エラーまたは解析エラー: {e}")

if __name__ == "__main__":
    update_driver_history()
