import os
import requests
import subprocess
import time
import winreg
import logging
from windows_toasts import WindowsToaster, ToastText1, ToastActivatedEventArgs

# --- 設定 ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ksdae86-max/nvidia_gpu_check/main/driver_history.txt"
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_LOG = os.path.join(LOG_DIR, "installed_version.txt")
TEMP_EXE = os.path.join(os.environ["TEMP"], "nvidia_update_temp.exe")

# ログ設定
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "updater.log"),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class NVIDIAUpdater:
    def __init__(self):
        self.target_version = ""
        self.download_url = ""

    def get_actual_installed_version(self):
        """Windowsレジストリから実際にインストールされているドライババージョンを取得"""
        try:
            path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}_Display.Driver"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                ver_str, _ = winreg.QueryValueEx(key, "DisplayVersion")
                return ver_str.strip()
        except:
            # レジストリから取れない場合は、前回の記録ファイルを確認
            if os.path.exists(VERSION_LOG):
                with open(VERSION_LOG, "r") as f: return f.read().strip()
            return "0.0"

    def on_toast_activated(self, args: ToastActivatedEventArgs):
        if args.arguments == "install":
            logging.info(f"User approved installation of version {self.target_version}")
            try:
                # NVIDIAサイレントインストール完全版フラグ
                # -s (Silent), -n (No Reboot), -f (Force), -noreboot (Extra safety)
                process = subprocess.Popen([TEMP_EXE, "-s", "-n", "-f", "-noreboot"])
                print("[!] インストール中... 完了までこの画面を閉じないでください。")
                process.wait()

                # 完了後の記録
                with open(VERSION_LOG, "w") as f: f.write(self.target_version)
                if os.path.exists(TEMP_EXE): os.remove(TEMP_EXE)
                
                logging.info("Installation completed successfully.")
                print("[*] 完了しました。")
            except Exception as e:
                logging.error(f"Installation failed: {e}")

    def check(self):
        # 1. 不完全な一時ファイルの掃除
        if os.path.exists(TEMP_EXE):
            try: os.remove(TEMP_EXE)
            except: pass

        actual_ver = self.get_actual_installed_version()
        logging.info(f"Check started. Actual Version: {actual_ver}")

        try:
            # 2. GitHubから最新情報を取得 (リトライ付き)
            res = requests.get(GITHUB_RAW_URL, timeout=15)
            res.raise_for_status()
            self.target_version, self.download_url = res.text.strip().split(": ")

            # 3. バージョン比較 (数値として比較)
            if float(self.target_version) > float(actual_ver):
                logging.info(f"New version found: {self.target_version}")
                
                # 4. ダウンロード (進捗をログに)
                print(f"[*] 新ドライバ {self.target_version} をダウンロード中...")
                with requests.get(self.download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(TEMP_EXE, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024): # 1MB単位
                            f.write(chunk)
                
                # 5. 通知
                self.show_notification()
            else:
                logging.info("No update required.")
        except Exception as e:
            logging.error(f"Check failed: {e}")

    def show_notification(self):
        toaster = WindowsToaster('NVIDIA Driver Manager')
        toast = ToastText1()
        toast.body = f"NVIDIA ドライバ {self.target_version} の準備完了。\n今すぐインストールしますか？"
        toast.add_action('今すぐインストール', 'install')
        toast.add_action('あとで', 'later')
        toast.on_activated = self.on_toast_activated
        toaster.show_toast(toast)
        # 通知の生存時間を確保
        time.sleep(60)

if __name__ == "__main__":
    # 多重起動の簡易チェック（TEMPにロックファイルを作成）
    lock_file = os.path.join(os.environ["TEMP"], "nv_updater.lock")
    if os.path.exists(lock_file) and (time.time() - os.path.getmtime(lock_file) < 600):
        print("別のインスタンスが実行中です。")
        exit()
    
    with open(lock_file, "w") as f: f.write("running")
    
    try:
        updater = NVIDIAUpdater()
        updater.check()
    finally:
        if os.path.exists(lock_file): os.remove(lock_file)
