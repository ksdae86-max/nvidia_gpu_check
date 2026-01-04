import os
import requests
import subprocess
import time
import winreg
import logging
import ctypes
import sys

# ライブラリの読み込み
try:
    from windows_toasts import WindowsToaster, Toast, ToastActivatedEventArgs
except ImportError as e:
    # ライブラリがない場合、ログに書き残す
    print(f"Required library missing: {e}")
    sys.exit(1)

# ==========================================
# 1. 実行環境の強制固定（タスクスケジューラ対策）
# ==========================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

LOG_FILE = os.path.join(BASE_DIR, "updater.log")
VERSION_LOG = os.path.join(BASE_DIR, "installed_version.txt")
TEMP_EXE = os.path.join(os.environ["TEMP"], "nvidia_update_temp.exe")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
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
            try:
                with open(VERSION_LOG, "r", encoding='utf-8') as f: return f.read().strip()
            except: pass
        return "0.0"

    def on_toast_activated(self, args: ToastActivatedEventArgs):
        # ボタンのID（arguments）で判定
        if args.arguments == "install":
            self.is_installing = True
            if not self.is_admin():
                logging.error("権限不足：管理者として実行されていません。")
                return

            logging.info(f"インストール承認：Version {self.target_version}")
            try:
                process = subprocess.Popen([TEMP_EXE, "-s", "-n", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait()

                time.sleep(20)
                actual = self.get_actual_installed_version()
                if actual == self.target_version:
                    logging.info(f"インストール成功完了：{actual}")
                    with open(VERSION_LOG, "w", encoding='utf-8') as f: f.write(self.target_version)
                    if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                else:
                    logging.warning(f"インストール後のバージョン不一致（現在: {actual}）")
            except Exception as e:
                logging.error(f"インストールプロセスエラー: {e}")
            finally:
                self.is_installing = False

    def check(self):
        if os.path.exists(TEMP_EXE):
            try: os.remove(TEMP_EXE)
            except: pass

        actual_ver = self.get_actual_installed_version()
        logging.info(f"チェック開始（現バージョン: {actual_ver}）")

        try:
            res = requests.get(GITHUB_RAW_URL, timeout=15)
            res.raise_for_status()
            self.target_version, self.download_url = res.text.strip().split(": ")
        except Exception as e:
            logging.error(f"GitHub取得失敗: {e}")
            return

        try:
            if float(self.target_version) > float(actual_ver):
                logging.info(f"新バージョン検知: {self.target_version}")
                
                logging.info(f"ダウンロード開始: {self.download_url}")
                with requests.get(self.download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(TEMP_EXE, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                
                logging.info("ダウンロード完了。通知を送信します。")
                self.show_notification()
            else:
                logging.info("アップデートの必要はありません。")
        except Exception as e:
            logging.error(f"エラー: {e}")

    def show_notification(self):
        # 最新の windows-toasts (v0.6.0+) に対応した書き方
        toaster = WindowsToaster('NVIDIA Driver Manager')
        new_toast = Toast()
        new_toast.text_fields = [
            f"🚀 NVIDIA ドライバ {self.target_version} の準備完了。",
            "今すぐインストールしますか？（画面暗転注意）"
        ]
        
        # ボタンの追加
        new_toast.add_action('今すぐインストール', 'install')
        new_toast.add_action('あとで', 'later')
        
        # コールバック設定
        new_toast.on_activated = self.on_toast_activated
        
        toaster.show_toast(new_toast)

        logging.info("通知応答待機中（120秒）...")
        for _ in range(120):
            if self.is_installing:
                while self.is_installing: time.sleep(1)
                break
            time.sleep(1)

if __name__ == "__main__":
    lock_path = os.path.join(os.environ["TEMP"], "nv_updater_smart_final.lock")
    if os.path.exists(lock_path):
        if time.time() - os.path.getmtime(lock_path) < 3600:
            sys.exit()

    with open(lock_path, "w") as f: f.write(str(os.getpid()))
    
    try:
        updater = NVIDIAUpdater()
        updater.check()
    finally:
        if os.path.exists(lock_path): os.remove(lock_path)
