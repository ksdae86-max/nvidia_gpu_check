@echo off
REM 最小限のテストスクリプト - 問題箇所特定用

echo [Test 1] スクリプト起動確認
echo ===================================
pause

echo [Test 2] ディレクトリ移動テスト
cd /d "%~dp0"
echo カレントディレクトリ: %cd%
pause

echo [Test 3] 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [結果] 管理者権限がありません
) else (
    echo [結果] 管理者権限: OK
)
pause

echo [Test 4] Dドライブ存在確認
if exist "D:\" (
    echo [結果] Dドライブ: 存在します
) else (
    echo [結果] Dドライブ: 存在しません
)
pause

echo [Test 5] Cドライブテスト
if exist "C:\" (
    echo [結果] Cドライブ: 存在します
) else (
    echo [結果] Cドライブ: 存在しません
)
pause

echo [Test 6] ディレクトリ作成テスト
mkdir "C:\TestNvidiaUpdate"
if exist "C:\TestNvidiaUpdate" (
    echo [結果] C:\TestNvidiaUpdate 作成成功
    rmdir "C:\TestNvidiaUpdate"
) else (
    echo [結果] C:\TestNvidiaUpdate 作成失敗
)
pause

echo テスト完了
