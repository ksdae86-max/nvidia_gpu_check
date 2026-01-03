import os
import requests
import subprocess
import time
import winreg
import logging
import hashlib
from windows_toasts import WindowsToaster, ToastText1, ToastActivatedEventArgs

# --- 設定 ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ksdae86-max/nvidia_gpu_check/main/driver_history.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "updater.log")
VERSION_LOG = os.path.join(BASE_DIR, "installed_version.txt")
TEMP_EXE = os.path.join(os.environ["TEMP"], "nvidia_update_temp.exe")

# 1. ログの強化（ファイルとコンソールの両方に出力）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileStatus(LOG_FILE), logging.StreamHandler()]
)

class NVIDIAUpdater:
    def __init__(self):
        self.target_version = ""
        self.download_url = ""

    # 2. レジストリパスの動的検証（将来の変更に対応）
    def get_actual_installed_version(self):
        paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}_Display.Driver",
            r"SOFTWARE\NVIDIA Corporation\Global\NVTweak\DisplayVersion" # 予備パス
        ]
        for path in paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    ver, _ = winreg.QueryValueEx(key, "DisplayVersion")
                    return ver.strip()
            except: continue
        return "0.0"

    # 3. インストール成功の事後検証
    def verify_and_finalize(self):
        time.sleep(10) # OSがレジストリを更新するまで待機
        final_ver = self.get_actual_installed_version()
        if final_ver == self.target_version:
            logging.info(f"Verify Success: {final_ver}")
            with open(VERSION_LOG, "w") as f: f.write(self.target_version)
            return True
        return False

    def on_toast_activated(self, args: ToastActivatedEventArgs):
        if args.arguments == "install":
            # 4. インストール前のファイル存在確認
            if not os.path.exists(TEMP_EXE):
                logging.error("Installer missing before execution.")
                return

            logging.info(f"Starting silent installation: {self.target_version}")
            try:
                # 5. プロセス実行の最適化（バックグラウンドで待機）
                flags = ["-s", "-n", "-f", "-noreboot"]
                process = subprocess.Popen([TEMP_EXE] + flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # 6. ユーザーへのフィードバック（通知を更新できればベストだが今回はログと標準出力）
                print("[!] インストールを実行中... 数分かかる場合があります。")
                process.wait()

                if self.verify_and_finalize():
                    print("[*] インストール成功。")
                    if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                else:
                    logging.warning("Installation finished but version mismatch. Check log.")

            except Exception as e:
                logging.error(f"Execution Error: {e}")

    def check(self):
        # 7. ネットワークリトライロジック
        actual_ver = self.get_actual_installed_version()
        print(f"[*] 現在のシステムバージョン: {actual_ver}")

        for attempt in range(3):
            try:
                res = requests.get(GITHUB_RAW_URL, timeout=10)
                res.raise_for_status()
                self.target_version, self.download_url = res.text.strip().split(": ")
                break
            except Exception as e:
                if attempt == 2: raise
                time.sleep(5)

        # 8. バージョン比較の数値化（文字列比較によるミス防止）
        if float(self.target_version) > float(actual_ver):
            logging.info(f"New Version: {self.target_version}")
            
            # 9. ダウンロード進捗の可視化
            print(f"[*] ダウンロード中...")
            with requests.get(self.download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(TEMP_EXE, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 簡易プログレス表示
                        print(f"\rProgress: {downloaded/total_size:.1%}", end="")
            print("\n[*] ダウンロード完了。")
            self.show_notification()
        else:
            print("[-] アップデートは不要です。")

    def show_notification(self):
        # 10. 通知の視覚的強調
        toaster = WindowsToaster('NVIDIA Driver Manager')
        toast = ToastText1()
        toast.body = f"🚀 最新ドライバ {self.target_version} が利用可能です。\n(インストール中に画面が暗転します)"
        toast.add_action('今すぐインストール', 'install')
        toast.add_action('あとで', 'later')
        toast.on_activated = self.on_toast_activated
        toaster.show_toast(toast)
        time.sleep(45)

if __name__ == "__main__":
    # 多重起動防止のロック（より安全な方式）
    lock_path = os.path.join(os.environ["TEMP"], "nv_upd_v2.lock")
    if os.path.exists(lock_path):
        # 1時間以上経過したロックは無効とみなす
        if time.time() - os.path.getmtime(lock_path) < 3600:
            print("Already running.")
            exit()

    with open(lock_path, "w") as f: f.write(str(os.getpid()))
    try:
        updater
