import requests
import os

def update_driver_history():
    api_url = "https://gfwsl.geforce.com/services_nvd/lookup/v1/type/3/id/135/is_beta/0/is_whql/1/language/1041/gpubid/956/direct/1"
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        version = data.get('version')
        url = data.get('downloadUrl')
        new_entry = f"{version}: {url}"

        # 既存の履歴を確認
        existing_content = ""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                existing_content = f.read()

        # 新しいバージョンなら追記
        if version not in existing_content:
            with open(history_file, "a") as f:
                f.write(new_entry + "\n")
            print(f"新しいバージョンが見つかりました: {version}")
        else:
            print(f"バージョン {version} は既に記録済みです。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    update_driver_history()
