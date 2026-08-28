# TradeMind Worker Deployment Script
# Windows -> Xavier (ARM64) via SCP
# Usage: .\deploy-to-xavier.ps1

$ErrorActionPreference = "Stop"

# Configuration
$XavierIP = "192.168.1.111"
$XavierUser = "dji"
$XavierPassword = "<TRADEMIND_XAVIER_PASSWORD>"
$RemotePath = "/opt/trademind/services"
$ServiceName = "indicator-worker"

Write-Host "=== TradeMind Worker Deployment ===" -ForegroundColor Cyan
Write-Host "Target: Xavier ($XavierIP)" -ForegroundColor Yellow
Write-Host "Service: $ServiceName" -ForegroundColor Yellow
Write-Host ""

# Step 1: Create deployment package locally
Write-Host "[1/5] Creating deployment package..." -ForegroundColor Green

$PackageDir = "d:\AGXXAIVER-4-WINDOWS-1-STOCK\deploy-pkg"
New-Item -ItemType Directory -Force -Path "$PackageDir\$ServiceName\src" | Out-Null

# Copy source files
Copy-Item -Path "d:\AGXXAIVER-4-WINDOWS-1-STOCK\$ServiceName\src\*.py" -Destination "$PackageDir\$ServiceName\src\" -Force
Copy-Item -Path "d:\AGXXAIVER-4-WINDOWS-1-STOCK\$ServiceName\Dockerfile" -Destination "$PackageDir\$ServiceName\" -Force
Copy-Item -Path "d:\AGXXAIVER-4-WINDOWS-1-STOCK\$ServiceName\requirements.txt" -Destination "$PackageDir\$ServiceName\" -Force
Copy-Item -Path "d:\AGXXAIVER-4-WINDOWS-1-STOCK\$ServiceName\docker-compose.yml" -Destination "$PackageDir\$ServiceName\" -Force

Write-Host "Files packaged to: $PackageDir" -ForegroundColor Gray

# Step 2: Transfer to Xavier via SCP
Write-Host ""
Write-Host "[2/5] Transferring to Xavier..." -ForegroundColor Green

$SecurePassword = ConvertTo-SecureString $XavierPassword -AsPlainText -Force
$Credential = New-Object System.Management.Automation.PSCredential ($XavierUser, $SecurePassword)

# Create remote directory via SSH
$Session = New-SSHSession -ComputerName $XavierIP -Credential $Credential -Force -ErrorAction SilentlyContinue
if (-not $Session) {
    Write-Host "SSH connection failed, trying password auth..." -ForegroundColor Yellow
}

# Use plink/putty for SCP
Write-Host "Creating remote directory..."
$createDirCmd = "mkdir -p $RemotePath/$ServiceName/src"
plink -batch -ssh -l $XavierUser -pw $XavierPassword $XavierIP $createDirCmd 2>$null

# Copy files with pscp
Write-Host "Copying files..."
pscp -r -scp -pw $XavierPassword "$PackageDir\$ServiceName\*" "$XavierUser@${XavierIP}:$RemotePath/$ServiceName/" 2>&1 | ForEach-Object {
    if ($_ -match "100%" -or $_ -match "complete") {
        Write-Host "." -NoNewline -ForegroundColor Green
    }
}
Write-Host ""

# Step 3: Verify transfer
Write-Host ""
Write-Host "[3/5] Verifying transfer..." -ForegroundColor Green
plink -batch -ssh -l $XavierUser -pw $XavierPassword $XavierIP "ls -la $RemotePath/$ServiceName/" 2>$null

# Step 4: Build on Xavier
Write-Host ""
Write-Host "[4/5] Building Docker image on Xavier..." -ForegroundColor Green
$buildCmd = @"
cd $RemotePath/$ServiceName
docker build -t trademind/$ServiceName`:1.0.0 . 2>&1
"@

plink -batch -ssh -l $XavierUser -pw $XavierPassword $XavierIP $buildCmd

# Step 5: Deploy
Write-Host ""
Write-Host "[5/5] Deploying service..." -ForegroundColor Green
$deployCmd = @"
cd $RemotePath/$ServiceName
docker-compose up -d 2>&1
docker-compose ps 2>&1
"@

plink -batch -ssh -l $XavierUser -pw $XavierPassword $XavierIP $deployCmd

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Health check: http://${XavierIP}:8000/health" -ForegroundColor Green
Write-Host "API endpoint: http://${XavierIP}:8000/calculate" -ForegroundColor Green
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "  ssh $XavierUser@$XavierIP 'cd $RemotePath/$ServiceName && docker-compose logs -f'" -ForegroundColor Gray
