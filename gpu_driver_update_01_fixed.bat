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

echo [情報] ダウンロードディレクトリ: %DOWNLOAD_DIR%

if not exist "%DOWNLOAD_DIR%" (
    mkdir "%DOWNLOAD_DIR%"
    echo [情報] ディレクトリを作成しました。
) else (
    echo [情報] ディレクトリは既に存在します。
)

echo [NVIDIA] 最新のドライバー情報をチェックしています...
echo.

:: ===== ここで問題修正 =====
:: Gemini CLIを実際に呼び出す必要があります
:: 以下は一例です（実際のGemini CLIコマンドに置き換えてください）

:: 【注意】以下のコマンドは例です。実際のGemini CLIパスに変更してください
:: set "GEMINI_CMD=gemini"  または  set "GEMINI_CMD=C:\path\to\gemini"

:: ダミー URL 取得（テスト用）
:: 実際には、以下のようにGemini CLIから取得する必要があります：
:: %GEMINI_CMD% "プロンプト内容" > "%DOWNLOAD_DIR%\gemini_output.txt"

echo [警告] Gemini CLIの呼び出しが未設定です。
echo [情報] 手動でドライバーURLを入力してください。
echo.

set "URL="
if exist "%DOWNLOAD_DIR%\gemini_output.txt" (
    for /f "usebackq delims=" %%A in ("%DOWNLOAD_DIR%\gemini_output.txt") do (
        if not "%%A"=="" (
            set "URL=%%A"
        )
    )
)

:: URLが取得できない場合は手動入力
if "!URL!"=="" (
    echo ドライバーURLを入力してください:
    set /p URL=URL: 
)

:: URLクリーニング
if defined URL (
    set "URL=!URL:`=!"
    set "URL=!URL: =!"
    set "URL=!URL:	=!"
)

echo [デバッグ] 取得したURL: !URL!
echo.

:: URLバリデーション
if not "!URL!"=="" if "!URL:~0,8!"=="https://" (
    cls
    echo ===================================================
    echo       ★ GPUドライバー更新中... (自動処理中) ★
    echo ===================================================
    echo [情報] ドライバーURL: !URL!
    echo.

    :: curlでダウンロード
    echo [情報] ドライバーをダウンロードしています...
    curl -f -L --max-time 600 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "!URL!" -o "%DOWNLOAD_DIR%\driver.exe"
    
    if !errorlevel! equ 0 if exist "%DOWNLOAD_DIR%\driver.exe" (
        for %%I in ("%DOWNLOAD_DIR%\driver.exe") do set "FILE_SIZE=%%~zI"
        
        echo [情報] ダウンロード完了 (!FILE_SIZE! bytes)
        
        if !FILE_SIZE! gtr 100000000 (
            echo [情報] ファイルサイズ確認OK。インストール中...
            
            :: サイレントインストール実行
            start /wait "" "%DOWNLOAD_DIR%\driver.exe" -s -noreboot
            set "INSTALL_RESULT=!errorlevel!"
            
            :: インストール結果確認
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
        echo [エラー] ダウンロードに失敗しました。(エラーコード: !errorlevel!)
        pause
    )
    
    if exist "%DOWNLOAD_DIR%\gemini_output.txt" del "%DOWNLOAD_DIR%\gemini_output.txt"
) else (
    echo [%date% %time%] URL取得失敗 (値: !URL!) >> "%DOWNLOAD_DIR%\update_log.txt"
    echo [エラー] 有効なドライバーURLを取得できませんでした。
    echo [情報] 取得したURL: !URL!
    pause
)

endlocal
