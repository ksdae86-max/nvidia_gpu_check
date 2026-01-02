import requests
import os

def update_driver_history():
    # NVIDIA公式API (RTX 4060, Win11用)
    api_url = "https://gfwsl.geforce.com/services_nvd/lookup/v1/type/3/id/135/is_beta/0/is_whql/1/language/1041/gpubid/956/direct/1"
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        version = data.get('version')
        url = data.get('downloadUrl')
        
        if not version or not url:
            print("APIから有効なデータが取得できませんでした。")
            return

        new_entry = f"{version}: {url}"

        # 既存の履歴を読み込む
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        # 新しいバージョンなら追記する
        if version not in existing_content:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(new_entry + "\n")
            print(f"書き込み完了: {version}")
        else:
            print(f"バージョン {version} は既に記録されています。")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    update_driver_history()
