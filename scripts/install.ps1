$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Configuration ---
$repo = "ezhil-003/qr-excel"
$binaryName = "qr-excel.exe"
$installDir = "$HOME\.qr-excel"
$assetsDir = "$installDir\assets"

# --- UI Helpers ---
function Show-Banner {
    Clear-Host
    Write-Host "`n"
    Write-Host "  ░██████   ░█████████                ░██████████ ░██    ░██   ░██████  ░██████████ ░██         " -ForegroundColor Cyan
    Write-Host " ░██   ░██  ░██     ░██               ░██          ░██  ░██   ░██   ░██ ░██         ░██         " -ForegroundColor Cyan
    Write-Host "░██     ░██ ░██     ░██               ░██           ░██░██   ░██        ░██         ░██         " -ForegroundColor Cyan
    Write-Host "░██     ░██ ░█████████     ░██████    ░█████████     ░███    ░██        ░█████████  ░██         " -ForegroundColor Cyan
    Write-Host "░██     ░██ ░██   ░██                 ░██           ░██░██   ░██        ░██         ░██         " -ForegroundColor Cyan
    Write-Host " ░██   ░██  ░██    ░██                ░██          ░██  ░██   ░██   ░██ ░██         ░██         " -ForegroundColor Cyan
    Write-Host "  ░██████   ░██     ░██               ░██████████ ░██    ░██   ░██████  ░██████████ ░██████████ " -ForegroundColor Cyan
    Write-Host "       ░██                                                                                      " -ForegroundColor Cyan
    Write-Host "        ░██                                                                                     " -ForegroundColor Cyan
    Write-Host " "
    Write-Host "  ==============================================================================================" -ForegroundColor DarkGray
    Write-Host "                                   Windows Installer   |   Auto-Setup                           " -ForegroundColor DarkGray
    Write-Host "  ==============================================================================================`n" -ForegroundColor DarkGray
}

function Write-Step ($msg) {
    Write-Host "  [>] " -NoNewline -ForegroundColor Blue
    Write-Host "$msg" -ForegroundColor Gray
}

function Write-Success ($msg) {
    Write-Host "  [+] " -NoNewline -ForegroundColor Green
    Write-Host "$msg" -ForegroundColor White
}

function Write-Warn ($msg) {
    Write-Host "  [!] " -NoNewline -ForegroundColor Yellow
    Write-Host "$msg" -ForegroundColor Yellow
}

function Write-Error ($msg) {
    Write-Host "  [x] " -NoNewline -ForegroundColor Red
    Write-Host "$msg" -ForegroundColor Red
}

function Invoke-FakeDelay {
    # Gives a slight pause to make the installation feel smoother
    Start-Sleep -Milliseconds 400
}

# --- Installation Steps ---
try {
    Show-Banner

    # 1. Directory Setup
    Write-Step "Initializing installation directories..."
    if (!(Test-Path $installDir)) {
        New-Item -ItemType Directory -Force -Path $installDir | Out-Null
        Write-Success "Created base directory: $installDir"
    } else {
        Write-Success "Found existing directory: $installDir"
    }

    if (!(Test-Path $assetsDir)) {
        New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null
    }
    Invoke-FakeDelay

    # 2. Fetch Latest Version
    Write-Step "Fetching latest release data from GitHub..."
    $latestRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases/latest"
    $version = $latestRelease.tag_name
    Write-Success "Discovered latest version: $version"
    Invoke-FakeDelay

    # 3. Download Binary
    $downloadUrl = "https://github.com/$repo/releases/download/$version/qr-excel-windows-amd64.exe"
    Write-Step "Downloading executable binary..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile "$installDir\$binaryName"
    Write-Success "Downloaded successfully to: $installDir\$binaryName"
    Invoke-FakeDelay

    # 4. Download Assets
    Write-Step "Fetching required assets (logo, templates)..."
    $logoUrl = "https://raw.githubusercontent.com/$repo/main/qr_excel/assets/upi_logo.png"
    $dbUrl = "https://raw.githubusercontent.com/$repo/main/qr_excel/assets/upi_qr_template.db"
    
    Invoke-WebRequest -Uri $logoUrl -OutFile "$assetsDir\upi_logo.png"
    Invoke-WebRequest -Uri $dbUrl -OutFile "$assetsDir\upi_qr_template.db"
    Write-Success "Assets fetched and placed in: $assetsDir"
    Invoke-FakeDelay

    # 5. Environment PATH Setup
    Write-Step "Checking system PATH configuration..."
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("Path", $userPath + ";$installDir", "User")
        $env:Path += ";$installDir"
        Write-Success "Added $installDir to User PATH"
    } else {
        Write-Success "Directory already exists in User PATH"
    }
    Invoke-FakeDelay

    # --- Completion ---
    Write-Host "`n  =======================================================" -ForegroundColor DarkGray
    Write-Host "  ✨  Installation Completed Successfully! ✨" -ForegroundColor Green
    Write-Host "  =======================================================`n" -ForegroundColor DarkGray

    Write-Host "  To get started, you may need to restart your terminal." -ForegroundColor Yellow
    Write-Host "  Then, simply run: " -NoNewline; Write-Host "qr-excel --help" -ForegroundColor Cyan
    Write-Host "`n"

} catch {
    Write-Error "An error occurred during installation:"
    Write-Host "      $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n  Installation aborted.`n" -ForegroundColor DarkGray
    Exit 1
}
