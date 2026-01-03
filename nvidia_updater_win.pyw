import os
import requests
import subprocess
import time
import winreg
import logging
import ctypes
import sys
from windows_toasts import WindowsToaster, ToastText1, ToastActivatedEventArgs

# --- 設定 ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ksdae86-max/nvidia_gpu_check/main/driver_history.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "updater.log")
VERSION_LOG = os.path.join(BASE_DIR, "installed_version.txt")
TEMP_EXE = os.path.join(os.environ["TEMP"], "nvidia_update_temp.exe")

# 1. ロギングの堅牢化 (FileHandlerの typo 修正とエンコーディング指定)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

class NVIDIAUpdater:
    def __init__(self):
        self.target_version = ""
        self.download_url = ""

    # 2. 権限チェック (管理者権限がないとインストールに失敗するため)
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def get_actual_installed_version(self):
        # 3. レジストリ取得のフォールバック強化
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}_Display.Driver"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NVIDIA Corporation\Global\NVTweak"),
        ]
        for hkey, path in paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    ver, _ = winreg.QueryValueEx(key, "DisplayVersion")
                    return ver.strip()
            except Exception:
                continue
        
        if os.path.exists(VERSION_LOG):
            with open(VERSION_LOG, "r") as f: return f.read().strip()
        return "0.0"

    def on_toast_activated(self, args: ToastActivatedEventArgs):
        if args.arguments == "install":
            if not self.is_admin():
                logging.error("管理者権限がありません。スクリプトを管理者として実行してください。")
                return
            
            if not os.path.exists(TEMP_EXE):
                logging.error("インストーラーが見つかりません。")
                return

            logging.info(f"インストール開始: {self.target_version}")
            try:
                # 4. プロセス実行の最適化
                # -s: Silent, -n: No Reboot, -f: Force
                process = subprocess.Popen([TEMP_EXE, "-s", "-n", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("[!] インストール中... 数分かかります。画面の暗転にご注意ください。")
                process.wait()

                # 5. インストール後の成否判定とクリーンアップ
                time.sleep(15) # レジストリ反映待ち
                if self.get_actual_installed_version() == self.target_version:
                    logging.info("インストール成功。")
                    with open(VERSION_LOG, "w") as f: f.write(self.target_version)
                    if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                else:
                    logging.warning("インストール完了後にバージョン不一致を検知しました。")
            except Exception as e:
                logging.error(f"インストールエラー: {e}")

    def check(self):
        # 6. 古い一時ファイルの削除を確実に
        if os.path.exists(TEMP_EXE):
            try: os.remove(TEMP_EXE)
            except PermissionError: 
                logging.error("前回のインストーラーがまだ使用中です。")
                return

        actual_ver = self.get_actual_installed_version()
        print(f"[*] 現在のバージョン: {actual_ver}")

        # 7. ネットワークエラーのリトライ強化
        for attempt in range(3):
            try:
                res = requests.get(GITHUB_RAW_URL, timeout=10)
                res.raise_for_status()
                parts = res.text.strip().split(": ")
                self.target_version, self.download_url = parts[0], parts[1]
                break
            except Exception as e:
                if attempt == 2: raise
                logging.warning(f"再試行中... ({attempt+1}/3)")
                time.sleep(5)

        # 8. バージョン比較を確実に (float変換の安全策)
        try:
            is_new = float(self.target_version) > float(actual_ver)
        except ValueError:
            is_new = self.target_version != actual_ver

        if is_new:
            logging.info(f"新バージョン検知: {self.target_version}")
            
            # 9. ダウンロードの進捗表示とストリーミング保存
            print(f"[*] ダウンロード中...")
            with requests.get(self.download_url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                done = 0
                with open(TEMP_EXE, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                        done += len(chunk)
                        if total > 0:
                            print(f"\rProgress: {done/total:.1%}", end="")
            print("\n[*] ダウンロード完了。")
            self.show_notification()
        else:
            print("[-] 最新の状態です。")

    def show_notification(self):
        # 10. 通知のタイムアウトとボタンの即応性
        toaster = WindowsToaster('NVIDIA Driver Manager')
        toast = ToastText1()
        toast.body = f"🚀 最新ドライバ {self.target_version} の準備完了。\n今すぐインストールしますか？"
        toast.add_action('今すぐインストール', 'install')
        toast.add_action('あとで', 'later')
        toast.on_activated = self.on_toast_activated
        toaster.show_toast(toast)
        
        # 通知が表示されている間、スクリプトを維持（ボタン反応のため）
        # time.sleep中もバックグラウンドでイベントを処理できるようにします
        count = 0
        while count < 60: # 60秒間待機
            time.sleep(1)
            count += 1

if __name__ == "__main__":
    # 多重起動防止 (LockFile)
    lock_path = os.path.join(os.environ["TEMP"], "nv_updater.lock")
    if os.path.exists(lock_path):
        if time.time() - os.path.getmtime(lock_path) < 3600:
            print("既に実行中です。")
            sys.exit()

    with open(lock_path, "w") as f: f.write(str(os.getpid()))
    
    try:
        updater = NVIDIAUpdater()
        updater.check()
    finally:
        if os.path.exists(lock_path): os.remove(lock_path)
