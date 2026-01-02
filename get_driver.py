import requests
import os
import re

def update_driver_history():
    # Microsoft wingetリポジトリ内の最新のインストーラー情報を探すためのURL
    # 検索を介さず、公式が公開している最新のバージョンリスト（別ルート）を使用します
    target_url = "https://raw.githubusercontent.com/microsoft/winget-pkgs/master/manifests/n/Nvidia/GeForceDriver/GameReady/566.36/Nvidia.GeForceDriver.GameReady.installer.yaml"
    
    # バージョン番号が不明なため、親ディレクトリの「最新」を特定するためのリストページ
    # ここは、GitHubのWeb UIを介さず、インデックスを直接参照できる別の公式エンドポイントを利用します
    index_url = "https://api.github.com/repos/microsoft/winget-pkgs/contents/manifests/n/Nvidia/GeForceDriver/GameReady"

    history_file = "driver_history.txt"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # 1. バージョン一覧を取得（大文字小文字の揺らぎを回避するため複数候補を試行）
        paths = [
            "manifests/n/Nvidia/GeForceDriver/GameReady",
            "manifests/n/nvidia/GeForceDriver/GameReady"
        ]
        
        items = []
        for path in paths:
            api_url = f"https://api.github.com/repos/microsoft/winget-pkgs/contents/{path}"
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code == 200:
                items = res.json()
                break
        
        if not items:
            # 最終手段：NVIDIAの別の公式メタデータサーバーを直接叩く
            # ここはボット制限が非常に緩い「公式XML」です
            print("winget API失敗。公式メタデータに切り替えます。")
            res = requests.get("https://gfwsl.geforce.com/services_nvd/lookup/v1/type/3/id/135/is_beta/0/is_whql/1/language/1041/gpubid/956/direct/1", timeout=15)
            data = res.json()
            version = data.get('version')
            download_url = data.get('downloadUrl')
        else:
            # wingetから取得できた場合
            versions = [i['name'] for i in items if re.match(r'^\d{3}\.\d{2}$', i['name'])]
            version = sorted(versions, reverse=True)[0]
            download_url = f"https://us.download.nvidia.com/Windows/{version}/{version}-desktop-win10-win11-64bit-international-dch-whql.exe"

        if not version:
            print("バージョンを特定できませんでした。")
            return

        new_entry = f"{version}: {download_url}"

        # 2. 履歴の保存
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
        print(f"致命的なエラー: {e}")

if __name__ == "__main__":
    update_driver_history()
