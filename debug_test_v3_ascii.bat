@echo off
title GPU Driver Update - Debug Test
echo Test 1 - Script Started
timeout /t 2
cls
echo Test 2 - Directory Test
cd /d "%~dp0"
echo Current Directory: %cd%
timeout /t 2
cls
echo Test 3 - Admin Check
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Result: No Admin Rights
) else (
    echo Result: Admin OK
)
timeout /t 2
cls
echo Test 4 - C Drive Check
if exist "C:\" (
    echo Result: C Drive Exists
) else (
    echo Result: C Drive Not Found
)
timeout /t 2
cls
echo Test 5 - Create Directory
mkdir "C:\TestNvidiaUpdate_001"
if exist "C:\TestNvidiaUpdate_001" (
    echo Result: Directory Created Successfully
    rmdir "C:\TestNvidiaUpdate_001"
) else (
    echo Result: Directory Creation Failed
)
timeout /t 2
cls
echo.
echo Test Complete
timeout /t 3
