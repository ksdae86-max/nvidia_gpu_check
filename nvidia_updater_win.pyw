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
    print(f"Required library missing: {e}")
    sys.exit(1)

# ==========================================
# 1. 実行環境の強制固定と定数定義
# ==========================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# --- 設定（パブリックリポジトリのRaw URL） ---
# トークン（?token=...）を除去した、純粋なRaw URLにしてください
GITHUB_URL = "https://raw.githubusercontent.com/ksdae86-max/nvidia_gpu_check/main/driver_history.txt"
LOG_FILE = os.path.join(BASE_DIR, "updater.log")
VERSION_LOG = os.path.join(BASE_DIR, "installed_version.txt")
TEMP_EXE = os.path.join(os.environ["TEMP"], "nvidia_update_temp.exe")

# --- ログ設定 ---
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
        if args.arguments == "install":
            self.is_installing = True
            if not self.is_admin():
                logging.error("権限不足：管理者権限がありません。")
                return

            logging.info(f"インストール開始承認：Version {self.target_version}")
            try:
                # インストーラー実行 (-s: Silent, -n: No Reboot, -f: Force)
                process = subprocess.Popen([TEMP_EXE, "-s", "-n", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait()

                time.sleep(20)
                actual = self.get_actual_installed_version()
                if actual == self.target_version:
                    logging.info(f"成功：バージョン {actual} に更新されました。")
                    with open(VERSION_LOG, "w", encoding='utf-8') as f: f.write(self.target_version)
                    if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                else:
                    logging.warning(f"更新完了後の不一致（現在: {actual}）")
            except Exception as e:
                logging.error(f"インストールエラー: {e}")
            finally:
                self.is_installing = False

    def check(self):
        if os.path.exists(TEMP_EXE):
            try: os.remove(TEMP_EXE)
            except: pass

        actual_ver = self.get_actual_installed_version()
        logging.info(f"チェック開始（現バージョン: {actual_ver}）")

        try:
            res = requests.get(GITHUB_URL, timeout=15)
            res.raise_for_status()
            
            # 解析: 「バージョン: URL」の形式を想定
            content = res.text.strip().split(": ")
            if len(content) < 2:
                logging.error(f"解析失敗。ファイル内容を確認してください。")
                return
            self.target_version = content[0]
            self.download_url = content[1]
        except Exception as e:
            logging.error(f"GitHub取得失敗 (URLを確認): {e}")
            return

        try:
            # 数値比較
            if float(self.target_version) > float(actual_ver):
                logging.info(f"新バージョン検知: {self.target_version}")
                logging.info(f"ダウンロード開始...")
                
                with requests.get(self.download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(TEMP_EXE, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                
                logging.info("ダウンロード完了。通知を送信します。")
                self.show_notification()
            else:
                logging.info("ドライバは最新です。")
        except Exception as e:
            logging.error(f"処理エラー: {e}")

    def show_notification(self):
        toaster = WindowsToaster('NVIDIA Driver Manager')
        new_toast = Toast()
        new_toast.text_fields = [
            f"🚀 NVIDIA ドライバ {self.target_version} が利用可能です。",
            "今すぐインストールしますか？（画面暗転注意）"
        ]
        new_toast.add_action('今すぐインストール', 'install')
        new_toast.add_action('あとで', 'later')
        new_toast.on_activated = self.on_toast_activated
        
        toaster.show_toast(new_toast)

        logging.info("応答待機中（120秒）...")
        for _ in range(120):
            if self.is_installing:
                while self.is_installing: time.sleep(1)
                break
            time.sleep(1)

if __name__ == "__main__":
    # 多重起動防止
    lock_path = os.path.join(os.environ["TEMP"], "nv_updater_final.lock")
    if os.path.exists(lock_path):
        if time.time() - os.path.getmtime(lock_path) < 3600:
            sys.exit()

    with open(lock_path, "w") as f: f.write(str(os.getpid()))
    
    try:
        updater = NVIDIAUpdater()
        updater.check()
    finally:
        if os.path.exists(lock_path): os.remove(lock_path)
