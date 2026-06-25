@echo off
REM 最小限のテストスクリプト - ブロック属性対応版

title GPU Driver Update - Debug Test

echo [Test 1] スクリプト起動確認
echo ===================================
timeout /t 2 /nobreak

cls
echo [Test 2] ディレクトリ移動テスト
cd /d "%~dp0"
echo カレントディレクトリ: %cd%
timeout /t 2 /nobreak

cls
echo [Test 3] 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [結果] 管理者権限がありません
) else (
    echo [結果] 管理者権限: OK
)
timeout /t 2 /nobreak

cls
echo [Test 4] Cドライブテスト
if exist "C:\" (
    echo [結果] Cドライブ: 存在します
) else (
    echo [結果] Cドライブ: 存在しません
)
timeout /t 2 /nobreak

cls
echo [Test 5] ディレクトリ作成テスト
mkdir "C:\TestNvidiaUpdate_001"
if exist "C:\TestNvidiaUpdate_001" (
    echo [結果] C:\TestNvidiaUpdate_001 作成成功
    rmdir "C:\TestNvidiaUpdate_001"
) else (
    echo [結果] C:\TestNvidiaUpdate_001 作成失敗
)
timeout /t 2 /nobreak

cls
echo.
echo テスト完了 - このウィンドウを閉じます
timeout /t 3 /nobreak
