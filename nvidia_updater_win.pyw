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

# 1. ログの堅牢化：エンコーディングをutf-8に固定し、Windows特有の文字化けを防止
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

class NVIDIAUpdater:
    def __init__(self):
        self.target_version = ""
        self.download_url = ""
        self.is_installing = False

    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def get_actual_installed_version(self):
        # 2. レジストリ取得のフォールバック強化
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
            with open(VERSION_LOG, "r", encoding='utf-8') as f: return f.read().strip()
        return "0.0"

    def on_toast_activated(self, args: ToastActivatedEventArgs):
        """通知ボタンが押された時のコールバック"""
        if args.arguments == "install":
            self.is_installing = True
            if not self.is_admin():
                logging.error("管理者権限が必要です。タスクスケジューラの『最上位の特権』を確認してください。")
                return

            logging.info(f"承認：インストールを開始します ({self.target_version})")
            try:
                # 3. サイレントフラグの最適化
                # -s: Silent, -n: No Reboot, -f: Force
                process = subprocess.Popen([TEMP_EXE, "-s", "-n", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait()

                # 4. インストール後の検証（15秒待機してレジストリ反映を確認）
                time.sleep(15)
                if self.get_actual_installed_version() == self.target_version:
                    logging.info("インストール成功を確認しました。")
                    with open(VERSION_LOG, "w", encoding='utf-8') as f: f.write(self.target_version)
                    if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                else:
                    logging.warning("インストール完了後にバージョンが一致しませんでした。")
            except Exception as e:
                logging.error(f"インストールエラー: {e}")
            finally:
                self.is_installing = False

    def check(self):
        # 5. 前回の残骸を確実にクリーニング
        if os.path.exists(TEMP_EXE):
            try: os.remove(TEMP_EXE)
            except PermissionError:
                logging.error("前回のインストーラーがまだ実行中かロックされています。")
                return

        actual_ver = self.get_actual_installed_version()
        logging.info(f"起動：現在のシステムバージョン {actual_ver}")

        # 6. 通信リトライ（最大3回）
        for attempt in range(3):
            try:
                res = requests.get(GITHUB_RAW_URL, timeout=10)
                res.raise_for_status()
                self.target_version, self.download_url = res.text.strip().split(": ")
                break
            except Exception as e:
                if attempt == 2: raise
                time.sleep(5)

        # 7. バージョン比較の精度向上
        if float(self.target_version) > float(actual_ver):
            logging.info(f"新バージョン検知: {self.target_version}")
            
            # 8. ストリーミングダウンロードで巨大ファイルに対応
            print(f"[*] ドライバをダウンロード中...")
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
            logging.info("システムは最新です。")

    def show_notification(self):
        # 9. トースト通知の視認性向上
        toaster = WindowsToaster('NVIDIA Driver Manager')
        toast = ToastText1()
        toast.body = f"🚀 最新ドライバ {self.target_version} の準備完了。\n今すぐインストールしますか？（画面が暗転します）"
        toast.add_action('今すぐインストール', 'install')
        toast.add_action('あとで', 'later')
        toast.on_activated = self.on_toast_activated
        toaster.show_toast(toast)

        # 10. 通知の応答待機ループ（ボタンが押されるまで死なない）
        logging.info("ユーザーの応答を待機中...")
        wait_seconds = 120 # 最大120秒待機
        for _ in range(wait_seconds):
            if self.is_installing:
                while self.is_installing: time.sleep(1) # インストール中は待機継続
                break
            time.sleep(1)

if __name__ == "__main__":
    # 多重起動防止（1時間以内の二重起動をブロック）
    lock_path = os.path.join(os.environ["TEMP"], "nv_updater_smart.lock")
    if os.path.exists(lock_path):
        if time.time() - os.path.getmtime(lock_path) < 3600:
            sys.exit()

    with open(lock_path, "w") as f: f.write(str(os.getpid()))
    
    try:
        updater = NVIDIAUpdater()
        updater.check()
    finally:
        if os.path.exists(lock_path): os.remove(lock_path)
