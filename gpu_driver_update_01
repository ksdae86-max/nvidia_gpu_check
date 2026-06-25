@echo off
setlocal enabledelayedexpansion

:: 1. 保存先フォルダの作成（Dドライブに変更）
set "DOWNLOAD_DIR=D:\NvidiaUpdate"
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

:: 2. Gemini CLIからURLを取得（Game Ready Driverを選択するようロジックを厳格化）
echo [NVIDIA] 最新のドライバー情報をチェックしています...
for /f "delims=" %%i in ('gemini "https://www.nvidia.com/ja-jp/geforce/drivers/ にアクセスし、グラフィックボード（RTX 4060）向けの最新ドライバーを探してください。ドライバーには『Game Ready』と『Studio』の2種類がありますが、必ず『Game Ready Driver』を選択してください。その上で、対応する『us.download.nvidia.comから始まる.exeの直リンクURL』を1行だけで出力してください。解説やマークダウン（```）は絶対に含めないでください。"') do (
    set "URL=%%i"
)

:: 3. 取得したURLが有効な場合、画面をクリアして指定のメッセージを表示
if not "%URL%"=="" (
    cls
    echo ===================================================
    echo       ★ GPUドライバー更新中... (自動処理中) ★
    echo ===================================================
    echo ※ 画面が一瞬ついたり消えたりする場合がありますが、
    echo    そのまましばらくお待ちください...
    echo.

    :: 4. curlの進捗を非表示(--silent)にしてバックグラウンドダウンロード
    curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" "!URL!" -o "%DOWNLOAD_DIR%\driver.exe"
    
    :: 5. サイレントインストールを実行（完全同期処理）
    if exist "%DOWNLOAD_DIR%\driver.exe" (
        :: start /wait を使い、インストーラーが完全に終了するまでバッチを待機させる
        start /wait "" "%DOWNLOAD_DIR%\driver.exe" -s -noreboot
        
        echo [%date% %time%] アップデート成功 >> "%DOWNLOAD_DIR%\update_log.txt"
        del "%DOWNLOAD_DIR%\driver.exe"
        
        cls
        echo ===================================================
        echo       ◆ GPUドライバーの更新が完了しました ◆
        echo ===================================================
        timeout /t 5 >nul
    ) else (
        echo [%date% %time%] ダウンロード失敗 >> "%DOWNLOAD_DIR%\update_log.txt"
        echo [エラー] ファイルのダウンロードに失敗しました。
        pause
    )
) else (
    echo [%date% %time%] Gemini CLIからのURL取得失敗 >> "%DOWNLOAD_DIR%\update_log.txt"
    echo [エラー] 最新ドライバーのURLが取得できませんでした。
    pause
)

endlocal
