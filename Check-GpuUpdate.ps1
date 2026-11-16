# ==========================================
# 設定情報
# ==========================================
$packageId = "Nvidia.DisplayDriver.NvidiaControlPanel"
$regPath   = "HKCU:\Software\GpuUpdateNotifier"
$defaultSnoozeDays = 7  # スヌーズの標準日数

# レジストリキーの自動生成
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}

# ==========================================
# 1. Wingetで最新バージョンの検出
# ==========================================
# 非表示実行時の横幅切り詰め（…によるパッケージID省略）を防止
try {
    $Host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(250, 3000)
} catch {}

$upgradeInfo = winget upgrade --id $packageId --source winget --accept-source-agreements --accept-package-agreements | Out-String

# パッケージIDが含まれていない場合は即終了
if ($upgradeInfo -notmatch [regex]::Escape($packageId)) {
    Exit
}

# 検出結果行から最新バージョン番号を取得
$latestVersion = ""
$matchingLine = ($upgradeInfo -split "`r?\n") | Where-Object { $_ -match [regex]::Escape($packageId) } | Select-Object -First 1

if ($matchingLine) {
    # パッケージIDの直後にある2つのバージョン文字列（現在Ver / 利用可能Ver）から後者を抽出
    if ($matchingLine -match "$([regex]::Escape($packageId))\s+(\S+)\s+(\S+)") {
        $latestVersion = $matches[2].Trim()
    }
}

# 数値ガード: バージョン情報が取得できていない場合は誤動作を防ぐため安全終了
if ([string]::IsNullOrWhiteSpace($latestVersion)) {
    Exit
}

# ==========================================
# 2. フラグ（レジストリ）チェック
# ==========================================
$savedState = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue

# 【拒否フラグの判定】対象バージョンが拒否登録されているか
if ($savedState -and $savedState.IgnoredVersion -eq $latestVersion) {
    Exit
}

# 【スヌーズフラグの判定】スヌーズ期限内か
if ($savedState -and $savedState.SnoozeUntil) {
    [DateTime]$snoozeDate = [DateTime]::MinValue
    if ([DateTime]::TryParse($savedState.SnoozeUntil, [ref]$snoozeDate)) {
        if ((Get-Date) -lt $snoozeDate) {
            Exit
        }
    }
}

# ==========================================
# 3. ユーザー選択ダイアログの表示
# ==========================================
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$msgText = "GPUドライバーの新しいバージョン ($latestVersion) が利用可能です。`n`n実行する操作を選択してください。"
$title   = "GPUドライバー更新通知"

$form = New-Object System.Windows.Forms.Form
$form.Text = $title
$form.Size = New-Object System.Drawing.Size(420, 230)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true

$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(20, 20)
$label.Size = New-Object System.Drawing.Size(360, 45)
$label.Text = $msgText
$form.Controls.Add($label)

# ボタン配置
$btnUpdate = New-Object System.Windows.Forms.Button
$btnUpdate.Location = New-Object System.Drawing.Point(20, 80)
$btnUpdate.Size = New-Object System.Drawing.Size(170, 35)
$btnUpdate.Text = "今すぐ更新"
$btnUpdate.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.Controls.Add($btnUpdate)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Location = New-Object System.Drawing.Point(210, 80)
$btnCancel.Size = New-Object System.Drawing.Size(170, 35)
$btnCancel.Text = "キャンセル (次回も通知)"
$btnCancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($btnCancel)

$btnSnooze = New-Object System.Windows.Forms.Button
$btnSnooze.Location = New-Object System.Drawing.Point(20, 125)
$btnSnooze.Size = New-Object System.Drawing.Size(170, 35)
$btnSnooze.Text = "スヌーズ (7日間)"
$btnSnooze.DialogResult = [System.Windows.Forms.DialogResult]::Retry
$form.Controls.Add($btnSnooze)

$btnIgnore = New-Object System.Windows.Forms.Button
$btnIgnore.Location = New-Object System.Drawing.Point(210, 125)
$btnIgnore.Size = New-Object System.Drawing.Size(170, 35)
$btnIgnore.Text = "このVerをスキップ"
$btnIgnore.DialogResult = [System.Windows.Forms.DialogResult]::Ignore
$form.Controls.Add($btnIgnore)

# ダイアログ表示とフォーム破棄
$result = $form.ShowDialog()
$form.Dispose()

# ==========================================
# 4. ユーザーの選択に応じた処理
# ==========================================
switch ($result) {
    "OK" {
        # 進捗画面表示 ➔ Winget更新 ➔ 一時キャッシュ削除 ➔ 最前面で結果ダイアログ表示
        $cmdText = "Write-Host 'GPUドライバーの更新処理を開始します。そのままお待ちください...' -ForegroundColor Cyan; " +
                   "winget upgrade --id '$packageId' --scope machine --source winget --accept-source-agreements --accept-package-agreements; " +
                   "`$exitCode = `$LASTEXITCODE; " +
                   "Remove-Item -Path `"`$env:TEMP\WinGet\*`" -Recurse -Force -ErrorAction SilentlyContinue; " +
                   "Add-Type -AssemblyName System.Windows.Forms; " +
                   "if (`$exitCode -eq 0) { " +
                   "  [System.Windows.Forms.MessageBox]::Show('GPUドライバーの更新が正常に完了しました。', '更新完了', 'OK', 'Information', 'Button1', 'DefaultDesktopOnly'); " +
                   "} else { " +
                   "  [System.Windows.Forms.MessageBox]::Show('更新が中断されたか、エラーが発生しました。(Code: ' + `$exitCode + ')', '更新エラー', 'OK', 'Warning', 'Button1', 'DefaultDesktopOnly'); " +
                   "}"

        try {
            Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"$cmdText`"" -Verb RunAs

            # 昇格が承認された場合のみ、既存のスヌーズ・拒否フラグを初期化
            Remove-ItemProperty -Path $regPath -Name "SnoozeUntil" -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $regPath -Name "IgnoredVersion" -ErrorAction SilentlyContinue
        } catch {
            # UAC（管理者権限昇格）がキャンセルされた場合はフラグを残したまま静かに終了
        }
    }
    "Retry" {
        # 【スヌーズ】7日後の日時をISO8601形式でレジストリに登録
        $snoozeUntil = (Get-Date).AddDays($defaultSnoozeDays).ToString("o")
        Set-ItemProperty -Path $regPath -Name "SnoozeUntil" -Value $snoozeUntil -Type String
    }
    "Ignore" {
        # 【拒否】対象バージョン番号を保存
        Set-ItemProperty -Path $regPath -Name "IgnoredVersion" -Value $latestVersion -Type String
    }
    "Cancel" {
        # 【キャンセル】フラグ操作をせず即時終了（次回ログイン時に再確認）
    }
}
