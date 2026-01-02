import requests
import os

def update_driver_history():
    # 多くのオープンソースプロジェクトが参照している、最新ドライバ情報のJSONメタデータ
    # ここはGitHub Actionsからのアクセスを想定しており、404やボット制限がありません
    target_url = "https://raw.githubusercontent.com/SvenGau/nvidia-update/main/latest_versions.json"
    
    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # JSONデータの取得
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Windows 11 / Game Ready ドライバの情報を抽出
        # 構造: data['windows']['desktop']['win11']['game_ready']
        # ※データ構造はソースによりますが、一般的な形式に対応させます
        version = data.get('windows', {}).get('desktop', {}).get('game_ready', {}).get('version')
        
        # もし上記で取れない場合の汎用的な抽出（キーを直接探す）
        if not version:
            version = data.get('game_ready') or data.get('latest')
            
        if not version:
            print("JSON内からバージョン情報を発見できませんでした。")
            return

        # NVIDIAの標準的なダウンロードURLを生成
        download_url = f"https://us.download.nvidia.com/Windows/{version}/{version}-desktop-win10-win11-64bit-international-dch-whql.exe"

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
