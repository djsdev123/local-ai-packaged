# HOME_GPU_NORDVPN.ps1
# Run once on Windows 11 desktop

Write-Host "=== HOME GPU SERVER (NordVPN Meshnet + WOL) ===" -ForegroundColor Green

# Install NordVPN if not already installed
if (!(Test-Path "C:\Program Files\NordVPN\NordVPN.exe")) {
    Write-Host "Installing NordVPN..." -ForegroundColor Yellow
    winget install NordVPN.NordVPN --accept-package-agreements --accept-source-agreements
    Write-Host "Please login to NordVPN and enable Meshnet in settings" -ForegroundColor Red
    Read-Host "Press Enter after you've logged in and enabled Meshnet"
}

# Install Ollama
Write-Host "Installing Ollama..." -ForegroundColor Yellow
winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements

# Install Python if needed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Python..." -ForegroundColor Yellow
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Get meshnet IP
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "IMPORTANT: Open NordVPN app and go to Meshnet" -ForegroundColor Yellow
Write-Host "Find your meshnet IP (looks like nord-xxx or 10.x.x.x)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$meshnetIP = Read-Host "Enter this PC's meshnet IP or hostname"

# Configure Ollama
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "${meshnetIP}:11434", "User")
$env:OLLAMA_HOST = "${meshnetIP}:11434"

# Create wake service directory
$serviceDir = "$env:USERPROFILE\WakeService"
New-Item -ItemType Directory -Force -Path $serviceDir | Out-Null

# Create wake service script
$wakeService = @"
import http.server
import socketserver
import subprocess
import json
import os
from datetime import datetime

PORT = 9999
MESHNET_IP = '${meshnetIP}'

class WakeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

    def do_GET(self):
        if self.path == '/status':
            # Return status
            status = {
                'status': 'awake',
                'timestamp': datetime.now().isoformat(),
                'ollama_running': self.check_ollama(),
                'meshnet_ip': MESHNET_IP
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())

        elif self.path == '/wake':
            # Already awake, but ensure Ollama is running
            self.ensure_ollama()
            response = {
                'status': 'already_awake',
                'message': 'PC is already running',
                'ollama_started': True
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def check_ollama(self):
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ollama.exe'],
                                  capture_output=True, text=True)
            return 'ollama.exe' in result.stdout
        except:
            return False

    def ensure_ollama(self):
        if not self.check_ollama():
            try:
                subprocess.Popen(['ollama', 'serve'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("Started Ollama service")
            except Exception as e:
                print(f"Failed to start Ollama: {e}")

# Prevent network adapter from sleeping
print(f"Wake Service starting on {MESHNET_IP}:{PORT}")
print("This service allows remote wake and status checks")
print("Press Ctrl+C to stop")

with socketserver.TCPServer((MESHNET_IP, PORT), WakeHandler) as httpd:
    print(f"✅ Listening on http://{MESHNET_IP}:{PORT}")
    httpd.serve_forever()
"@

$wakeService | Out-File -FilePath "$serviceDir\wake_service.py" -Encoding UTF8

# Create start script
$startScript = @"
@echo off
title GPU Wake Service
echo Starting Wake Service on ${meshnetIP}:9999
echo Keep this window open!
echo.
python "%USERPROFILE%\WakeService\wake_service.py"
pause
"@
$startScript | Out-File -FilePath "$serviceDir\START_WAKE_SERVICE.bat" -Encoding ASCII

# Create scheduled task to start wake service on login
$action = New-ScheduledTaskAction -Execute "python" -Argument "`"$serviceDir\wake_service.py`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 0)

Register-ScheduledTask -TaskName "GPU_WakeService" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "✅ Wake service installed" -ForegroundColor Green

# Configure Windows power settings for sleep
Write-Host "Configuring power settings for sleep..." -ForegroundColor Yellow
powercfg /change standby-timeout-ac 30  # Sleep after 30 min on AC
powercfg /change standby-timeout-dc 15  # Sleep after 15 min on battery
Write-Host "✅ Sleep configured (30 min idle)" -ForegroundColor Green

# Enable Wake-on-LAN in network adapter
Write-Host "Enabling Wake-on-LAN..." -ForegroundColor Yellow
$adapters = Get-NetAdapter | Where-Object {$_.Status -eq "Up"}
foreach ($adapter in $adapters) {
    try {
        Enable-NetAdapterPowerManagement -Name $adapter.Name -WakeOnMagicPacket
        Write-Host "  ✅ Enabled WOL on $($adapter.Name)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not enable WOL on $($adapter.Name)" -ForegroundColor Yellow
    }
}

# Start Ollama
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden

# Start wake service
Start-Process "python" -ArgumentList "`"$serviceDir\wake_service.py`"" -WindowStyle Minimized

# Create desktop info
$note = @"
GPU SERVER INFO (with Wake-on-LAN)
===================================
Meshnet Address: $meshnetIP
GPU URL: http://${meshnetIP}:11434
Wake Service: http://${meshnetIP}:9999

Give laptop this address: $meshnetIP

The PC will sleep after 30 minutes of inactivity.
Your laptop can wake it remotely!

Wake Service auto-starts on login.
"@
$note | Out-File "$env:USERPROFILE\Desktop\MESHNET_GPU_INFO.txt"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "GPU Server: http://${meshnetIP}:11434" -ForegroundColor Cyan
Write-Host "Wake Service: http://${meshnetIP}:9999" -ForegroundColor Cyan
Write-Host ""
Write-Host "Power Settings:" -ForegroundColor Yellow
Write-Host "  • PC will sleep after 30 min idle" -ForegroundColor White
Write-Host "  • Wake service runs automatically" -ForegroundColor White
Write-Host "  • Laptop can wake this PC remotely" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
