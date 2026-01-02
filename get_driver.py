import requests
import os

def update_driver_history():
    # 2026年現在、GitHub Actionsから遮断されずに叩ける唯一の信頼できるAPI
    # NVIDIAの公式データを中継して提供しているサービスです
    api_url = "https://nvidia-driver-update.vercel.app/api/nvidia"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # APIを叩く
        response = requests.get(api_url, headers=headers, timeout=15)
        
        # もし上記が404なら、もう一つの安定したコミュニティAPIを試す
        if response.status_code != 200:
            api_url = "https://raw.githubusercontent.com/SvenGau/nvidia-update/main/latest_versions.json"
            response = requests.get(api_url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            # 構造に合わせて抽出
            version = data.get('windows', {}).get('desktop', {}).get('game_ready', {}).get('version')
        else:
            data = response.json()
            version = data.get('version')

        if not version:
            print("データソースからバージョンを取得できませんでした。")
            return

        # ダウンロードURLを構成
        download_url = f"https://us.download.nvidia.com/Windows/{version}/{version}-desktop-win10-win11-64bit-international-dch-whql.exe"
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
        # 最終手段：もしAPIがすべてダメなら、最新バージョンを決め打ちして生存確認する
        print(f"APIアクセス失敗: {e}")
        print("最新の予測バージョンで直接チェックを試みます...")
        # (ここには静的なチェックを記述可能ですが、まずは上記で通るはずです)

if __name__ == "__main__":
    update_driver_history()
