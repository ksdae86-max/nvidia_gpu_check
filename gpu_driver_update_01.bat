@echo off
setlocal enabledelayedexpansion

:: 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [エラー] このスクリプトは管理者権限で実行してください。
    pause
    exit /b 1
)

:: 1. 保存先フォルダの作成（Dドライブに変更）
set "DOWNLOAD_DIR=D:\NvidiaUpdate"
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

:: 2. Gemini CLIからURLを取得（パイプを使用してインタラクティブシェルに対応）
echo [NVIDIA] 最新のドライバー情報をチェックしています...

:: Gemini CLIへプロンプトを送信（Game Ready Driverに限定、タイムアウト付き）
timeout /t 3 >nul
echo https://www.nvidia.com/ja-jp/geforce/drivers/ にアクセスし、Game Ready Driver（ゲーム用ドライバー）のみを対象に、グラフィックボード RTX 4060 向けの最新版のダウンロードURLを抽出してください。URLのみを返してください。 | gemini > "%DOWNLOAD_DIR%\gemini_output.txt" 2>&1
timeout /t 2 >nul

:: ファイルから取得したURLを読み込み、前後の不要な空白やバッククォートを除去
if exist "%DOWNLOAD_DIR%\gemini_output.txt" (
    set /p RAW_URL=<"%DOWNLOAD_DIR%\gemini_output.txt"
    if defined RAW_URL (
        :: 前後の空白を除去
        for /f "tokens=*" %%A in ("!RAW_URL!") do set "URL=%%A"
        :: バッククォートを除去
        set "URL=!URL:`=!"
        :: その他の空白文字（スペース、タブ）を除去
        set "URL=!URL: =!"
        set "URL=!URL:	=!"
    )
)

:: 3. 取得したURLが有効な場合、画面をクリアして指定のメッセージを表示
:: (httpから始まっているか簡易判定を追加)
if not "!URL!"=="" if "!URL:~0,4!"=="http" (
    cls
    echo ===================================================
    echo       ★ GPUドライバー更新中... (自動処理中) ★
    echo ===================================================
    echo [情報] ドライバーURL: !URL!
    echo.

    :: 4. curlでダウンロード（-f オプションでサーバーエラー時にファイル作成を抑止）
    curl -f -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" "!URL!" -o "%DOWNLOAD_DIR%\driver.exe"
    
    if !errorlevel! equ 0 if exist "%DOWNLOAD_DIR%\driver.exe" (
        for %%I in ("%DOWNLOAD_DIR%\driver.exe") do set "FILE_SIZE=%%~zI"
        
        :: ファイルサイズが100KB以上か確認（NVIDIAドライバーは通常100MB以上）
        if !FILE_SIZE! gtr 100000 (
            echo [情報] ダウンロード完了。インストール中...
            
            :: 5. サイレントインストールを実行（完全同期処理）
            start /wait "" "%DOWNLOAD_DIR%\driver.exe" -s -noreboot
            
            if !errorlevel! equ 0 (
                echo [%date% %time%] アップデート成功 >> "%DOWNLOAD_DIR%\update_log.txt"
                del "%DOWNLOAD_DIR%\driver.exe"
                
                cls
                echo ===================================================
                echo       ◆ GPUドライバーの更新が完了しました ◆
                echo ===================================================
                timeout /t 5 >nul
            ) else (
                echo [%date% %time%] インストール失敗 (エラーコード: !errorlevel!) >> "%DOWNLOAD_DIR%\update_log.txt"
                echo [エラー] インストールに失敗しました。
                pause
            )
        ) else (
            echo [%date% %time%] ダウンロード失敗 (ファイルサイズ異常: !FILE_SIZE! bytes) >> "%DOWNLOAD_DIR%\update_log.txt"
            echo [エラー] ダウンロードファイルのサイズが異常です。(サイズ: !FILE_SIZE! bytes)
            if exist "%DOWNLOAD_DIR%\driver.exe" del "%DOWNLOAD_DIR%\driver.exe"
            pause
        )
    ) else (
        echo [%date% %time%] ダウンロード失敗 (curl エラー: !errorlevel!) >> "%DOWNLOAD_DIR%\update_log.txt"
        echo [エラー] ダウンロードに失敗しました。URLが不正かネットワークに問題があります。
        pause
    )
    
    :: 一時ファイルを削除
    if exist "%DOWNLOAD_DIR%\gemini_output.txt" del "%DOWNLOAD_DIR%\gemini_output.txt"
) else (
    echo [%date% %time%] URL取得失敗 (取得値: !URL!) >> "%DOWNLOAD_DIR%\update_log.txt"
    echo [エラー] 最新ドライバーのURLが正常に取得できませんでした。
    pause
)

endlocal
