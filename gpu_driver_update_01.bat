@echo off
setlocal enabledelayedexpansion

:: 【超重要】管理者実行時のカレントディレクトリをバッチの場所に変更
cd /d "%~dp0"

:: 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [エラー] このスクリプトは管理者権限で実行してください。
    pause
    exit /b 1
)

:: ドライブ存在確認
if not exist "D:\" (
    echo [警告] Dドライブが見つかりません。Cドライブを使用します。
    set "DOWNLOAD_DIR=C:\NvidiaUpdate"
) else (
    set "DOWNLOAD_DIR=D:\NvidiaUpdate"
)

if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

echo [NVIDIA] 最新のドライバー情報をチェックしています...

:: Gemini CLIへプロンプトを送信
timeout /t 3 >nul
echo https://www.nvidia.com/ja-jp/geforce/drivers/ にアクセスし、Game Ready Driver（ゲーム用ドライバー）のみを対象に、グラフィックボード RTX 4060 向けの最新版のダウンロードURLを抽出してください。URLのみを返してください。 | gemini > "%DOWNLOAD_DIR%\gemini_output.txt" 2>&1
timeout /t 2 >nul

:: URLを読み込み、クレンジング
set "URL="
if exist "%DOWNLOAD_DIR%\gemini_output.txt" (
    for /f "usebackq delims=" %%A in ("%DOWNLOAD_DIR%\gemini_output.txt") do (
        if not "%%A"=="" (
            set "URL=%%A"
        )
    )
    
    if defined URL (
        :: バッククォート・スペース・タブ除去
        set "URL=!URL:`=!"
        set "URL=!URL: =!"
        set "URL=!URL:	=!"
    )
)

:: URLバリデーション
if not "!URL!"=="" if "!URL:~0,8!"=="https://" (
    cls
    echo ===================================================
    echo       ★ GPUドライバー更新中... (自動処理中) ★
    echo ===================================================
    echo [情報] ドライバーURL: !URL!
    echo.

    :: curlでダウンロード
    curl -f -L --max-time 600 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "!URL!" -o "%DOWNLOAD_DIR%\driver.exe"
    
    if !errorlevel! equ 0 if exist "%DOWNLOAD_DIR%\driver.exe" (
        for %%I in ("%DOWNLOAD_DIR%\driver.exe") do set "FILE_SIZE=%%~zI"
        
        if !FILE_SIZE! gtr 100000000 (
            echo [情報] ダウンロード完了 (!FILE_SIZE! bytes)。インストール中...
            
            :: サイレントインストール実行
            start /wait "" "%DOWNLOAD_DIR%\driver.exe" -s -noreboot
            set "INSTALL_RESULT=!errorlevel!"
            
            :: インストール結果確認（複数の成功コード対応）
            if !INSTALL_RESULT! equ 0 (
                echo [%date% %time%] アップデート成功 >> "%DOWNLOAD_DIR%\update_log.txt"
                del "%DOWNLOAD_DIR%\driver.exe"
                cls
                echo ===================================================
                echo       ◆ GPUドライバーの更新が完了しました ◆
                echo ===================================================
                timeout /t 5 >nul
            ) else (
                echo [%date% %time%] インストール失敗 (コード: !INSTALL_RESULT!) >> "%DOWNLOAD_DIR%\update_log.txt"
                echo [エラー] インストールに失敗しました (コード: !INSTALL_RESULT!)
                pause
            )
        ) else (
            echo [%date% %time%] ダウンロード失敗 (サイズ異常: !FILE_SIZE! bytes) >> "%DOWNLOAD_DIR%\update_log.txt"
            echo [エラー] ファイルサイズが異常です。(取得: !FILE_SIZE! bytes, 期待: 100MB以上)
            del "%DOWNLOAD_DIR%\driver.exe"
            pause
        )
    ) else (
        echo [%date% %time%] ダウンロード失敗 (curl: !errorlevel!) >> "%DOWNLOAD_DIR%\update_log.txt"
        echo [エラー] ダウンロードに失敗しました。
        pause
    )
    
    if exist "%DOWNLOAD_DIR%\gemini_output.txt" del "%DOWNLOAD_DIR%\gemini_output.txt"
) else (
    echo [%date% %time%] URL取得失敗 (値: !URL!) >> "%DOWNLOAD_DIR%\update_log.txt"
    echo [エラー] 有効なドライバーURLを取得できませんでした。
    pause
)

endlocal
