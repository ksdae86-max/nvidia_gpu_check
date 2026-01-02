import requests
import os
import re

def update_driver_history():
    # 公式サイトの検索エンジンが直接使用する、最も原始的で安定したクエリURL
    # psid=127(RTX40), pfid=956(4060), osid=135(Win11), dtid=1(Game Ready), lang=1(English/US - 最も安定)
    # ※言語を1(US)にしても、中身は国際版(International)なので日本でも使えます。
    api_url = "https://www.nvidia.com/Download/processDriver.aspx?psid=127&pfid=956&osid=135&lid=1&dtid=1&whql=1&lang=1"
    
    history_file = "driver_history.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nvidia.com/Download/index.aspx"
    }

    try:
        # リダイレクトを許可して、最終的なダウンロード先のURLを直接取得する
        # NVIDIAのこのURLは、アクセスすると即座に「詳細ページ」へ飛ばされます
        response = requests.get(api_url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        final_url = response.url
        print(f"到達URL: {final_url}")

        # URLからバージョン（例: 566.36）を抽出する
        # パターン: /566.36/ または 566.36-desktop...
        version_match = re.search(r'(\d{3}\.\d{2})', final_url)
        
        if version_match:
            version = version_match.group(1)
            # 実際のダウンロードURLを構成（リダイレクト先URLをそのまま利用）
            download_url = final_url
            
            # もし詳細ページに飛ばされただけなら、さらにURLを整形（もし必要なら）
            if "driverDetails.aspx" in download_url:
                # 詳細ページから実際の.exeリンクを推測または抽出が必要だが、
                # 多くの場合はこのURL自体がバージョン特定に役立つ
                pass
        else:
            print("URLからバージョンを特定できませんでした。")
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
