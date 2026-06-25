@echo off
setlocal enabledelayedexpansion

:: 1. 保存先フォルダの作成（Dドライブに変更）
set "DOWNLOAD_DIR=D:\NvidiaUpdate"
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

:: 2. Gemini CLIからURLを取得（パイプを使用してインタラクティブシェルに対応）
echo [NVIDIA] 最新のドライバー情報をチェックしています...

:: Gemini CLIへプロンプトを送信（Game Ready Driverに限定）
echo https://www.nvidia.com/ja-jp/geforce/drivers/ にアクセスし、Game Ready Driver（ゲーム用ドライバー）のみを対象に、グラフィックボード RTX 4060 向けの最新版のダウンロードURLを抽出してください。URLのみを返してください。余計な解説やバッククォートなどの装飾は一切不要です。 | gemini > "%DOWNLOAD_DIR%\gemini_output.txt"

:: ファイルから取得したURLを読み込み、前後の不要な空白やバッククォートを除去
if exist "%DOWNLOAD_DIR%\gemini_output.txt" (
    set /p RAW_URL=<"%DOWNLOAD_DIR%\gemini_output.txt"
    if defined RAW_URL (
        :: 前後の空白を除去
        for /f "tokens=*" %%A in ("!RAW_URL!") do set "URL=%%A"
        :: バッククォートを除去
        set "URL=!URL:`=!"
    )
)

:: 3. 取得したURLが有効な場合、画面をクリアして指定のメッセージを表示
:: (httpから始まっているか簡易判定を追加)
if not "!URL!"=="" if "!URL:~0,4!"=="http" (
    cls
    echo ===================================================
    echo       ★ GPUドライバー更新中... (自動処理中) ★
    echo ===================================================
    echo ※ 画面が一瞬ついたり消えたりする場合がありますが、
    echo    そのまましばらくお待ちください...
    echo.

    :: 4. curlでダウンロード（-f オプションでサーバーエラー時にファイル作成を抑止）
    curl -f -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" "!URL!" -o "%DOWNLOAD_DIR%\driver.exe"

    :: 5. サイレントインストールを実行（完全同期処理 & エラーレベルとファイルサイズで判定）
    if exist "%DOWNLOAD_DIR%\driver.exe" (
        for %%I in ("%DOWNLOAD_DIR%\driver.exe") do set "FILE_SIZE=%%~zI"
        
        if !FILE_SIZE! gtr 0 (
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
            goto :DOWNLOAD_ERROR
        )
    ) else (
        :DOWNLOAD_ERROR
        echo [%date% %time%] ダウンロード失敗 (ファイル不在または0KB) >> "%DOWNLOAD_DIR%\update_log.txt"
        echo [エラー] ファイルのダウンロードに失敗しました。URLが不正かネットワークに問題があります。
        if exist "%DOWNLOAD_DIR%\driver.exe" del "%DOWNLOAD_DIR%\driver.exe"
        pause
    )

    :: 一時ファイルを削除
    del "%DOWNLOAD_DIR%\gemini_output.txt"
) else (
    echo [%date% %time%] Gemini CLIからのURL取得失敗 (取得値: !URL!) >> "%DOWNLOAD_DIR%\update_log.txt"
    echo [エラー] 最新ドライバーのURLが正常に取得できませんでした。
    pause
)

endlocal
