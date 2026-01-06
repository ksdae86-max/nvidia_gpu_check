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
    from windows_toasts import InteractableWindowsToaster, Toast, ToastActivatedEventArgs, ToastButton
except ImportError:
    print("Required library missing: python -m pip install windows_toasts==1.3.1")
    sys.exit(1)

# ==========================================
# 1. 実行環境とパスの定義
# ==========================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# 設定
GITHUB_URL = "https://raw.githubusercontent.com/ksdae86-max/nvidia_gpu_check/main/driver_history.txt"
LOG_FILE = os.path.join(BASE_DIR, "updater.log")
VERSION_LOG = os.path.join(BASE_DIR, "installed_version.txt")
TEMP_EXE = os.path.join(BASE_DIR, "nvidia_update_temp.exe")

# ログ設定
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
                logging.error("権限不足：管理者権限が必要です。")
                self.is_installing = False
                return

            logging.info(f"承認されました。インストール開始: Ver {self.target_version}")
            try:
                # 実行ファイルの存在確認
                if not os.path.exists(TEMP_EXE):
                    logging.error("インストーラーが見つかりません。再ダウンロードしてください。")
                    return

                process = subprocess.Popen([TEMP_EXE, "-s", "-n", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait()

                logging.info("反映待ち(30秒)...")
                time.sleep(30) 

                actual = self.get_actual_installed_version()
                if actual == self.target_version:
                    logging.info(f"成功：バージョン {actual} に更新されました。")
                    with open(VERSION_LOG, "w", encoding='utf-8') as f: f.write(self.target_version)
                    if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                else:
                    logging.warning(f"更新不一致。手動確認が必要（現在: {actual}）")
            except Exception as e:
                logging.error(f"インストールエラー: {e}")
            finally:
                self.is_installing = False

    def check(self):
        if os.path.exists(TEMP_EXE):
            try: os.remove(TEMP_EXE)
            except: pass

        actual_ver = self.get_actual_installed_version()
        logging.info(f"チェック開始（現在: {actual_ver}）")

        try:
            res = requests.get(GITHUB_URL, timeout=15)
            res.raise_for_status()
            content = res.text.strip().split(": ")
            if len(content) < 2: return
            self.target_version = content[0]
            self.download_url = content[1]
        except Exception as e:
            logging.error(f"GitHub取得失敗: {e}")
            return

        try:
            if float(self.target_version) > float(actual_ver):
                logging.info(f"新バージョン検知: {self.target_version}. ダウンロード開始...")
                with requests.get(self.download_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(TEMP_EXE, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
                
                logging.info("ダウンロード完了。通知を表示します。")
                self.show_notification()
            else:
                logging.info("最新の状態です。")
        except Exception as e:
            logging.error(f"実行エラー: {e}")

    def show_notification(self):
        # アプリIDをユニークなものに変更してキャッシュを回避
        toaster = InteractableWindowsToaster('NVIDIA.Driver.Updater')
        
        new_toast = Toast()
        new_toast.text_fields = [
            f"🚀 NVIDIA ドライバ {self.target_version} の準備完了",
            "今すぐインストールを実行しますか？"
        ]
        
        # ボタンの追加（スロットへ追加）
        new_toast.actions.append(ToastButton('今すぐインストール', 'install'))
        new_toast.actions.append(ToastButton('あとで', 'later'))
        
        new_toast.on_activated = self.on_toast_activated
        
        # 通知を表示
        toaster.show_toast(new_toast)

        logging.info("通知を表示しました。ユーザーの応答を待機中...")
        # 120秒ループ
        for i in range(120):
            if self.is_installing:
                while self.is_installing: time.sleep(1)
                break
            time.sleep(1)

if __name__ == "__main__":
    lock_path = os.path.join(os.environ["TEMP"], "nv_updater_final_v2.lock")
    if os.path.exists(lock_path):
        if time.time() - os.path.getmtime(lock_path) < 3600: sys.exit()
    with open(lock_path, "w") as f: f.write(str(os.getpid()))
    
    try:
        updater = NVIDIAUpdater()
        updater.check()
    finally:
        if os.path.exists(lock_path): os.remove(lock_path)
