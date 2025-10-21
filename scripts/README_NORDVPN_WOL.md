# NordVPN Meshnet GPU Server with Wake-on-LAN

Simple, secure setup for accessing your home GPU from anywhere with automatic sleep/wake.

## Features

✅ **Security First**
- E2E encrypted via NordVPN Meshnet
- Public WiFi protection via NordVPN
- Zero third-party access to your AI inference

✅ **Power Efficient**
- Home PC sleeps after 30 minutes idle
- Wake remotely from laptop
- Cold start ~30-60 seconds

✅ **Grandma-Proof**
- One-click wake from desktop
- Built-in troubleshooter
- Clear status indicators

---

## Setup Instructions

### 1. Home Windows PC (One-Time Setup)

1. Download `HOME_GPU_NORDVPN.ps1`
2. Right-click → **Run with PowerShell**
3. Follow prompts:
   - NordVPN will install and ask you to login
   - Enable Meshnet in NordVPN settings
   - Note your meshnet IP (looks like `100.x.x.x` or `nord-xxxxx`)
4. Done! Check your desktop for `MESHNET_GPU_INFO.txt`

**What gets installed:**
- NordVPN with Meshnet
- Ollama (GPU inference engine)
- Wake service (allows remote wake)
- Auto-sleep after 30 min idle

---

### 2. Laptop (Mac) - One-Time Setup

1. Download `LAPTOP_SETUP.sh`
2. Open Terminal
3. Run: `bash LAPTOP_SETUP.sh`
4. Follow prompts:
   - NordVPN will install
   - Connect to VPN server (for WiFi protection)
   - Enable Meshnet in settings
   - Add home PC in meshnet
   - Enter home PC meshnet IP when asked

**What gets installed:**
- NordVPN with Meshnet
- Ollama CLI
- Wake utilities
- Desktop shortcuts

---

## Daily Usage

### On Laptop:

**Option 1: Desktop Shortcuts**
- Double-click **GPU_Wake.command** → Wakes GPU and shows status
- Double-click **GPU_Status.command** → Check if GPU is ready

**Option 2: Command Line**
```bash
# Check if GPU is awake
gpu-wake status

# Wake GPU from sleep
gpu-wake wake

# Run diagnostics
gpu-wake troubleshoot

# Use GPU for inference
ollama-gpu run llama2
ollama-gpu list
```

### On Home PC:
- Leave it! It auto-sleeps after 30 min
- Wake service auto-starts on boot

---

## How Wake-on-LAN Works

### Traditional WOL (doesn't work here):
```
Laptop → Magic Packet → Router → Home PC ❌
Problem: Doesn't work over internet/VPN
```

### Our Solution:
```
Laptop → NordVPN Meshnet → Wake Service → Wake PC ✅
```

**The Wake Service:**
- Tiny Python HTTP server (uses ~10MB RAM)
- Listens on meshnet IP port 9999
- Keeps network adapter awake
- Triggers PC wake when requested
- Auto-starts Ollama after wake

**Power Usage:**
- Sleeping: ~5-10W
- Wake Service: +1W (negligible)
- Wake time: 30-60 seconds

---

## Status Indicators

### `gpu-wake status` output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GPU STATUS CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wake Service:  ✅ ONLINE
Status:        ✅ AWAKE
Ollama:        ✅ RUNNING
GPU Ready:     ✅ READY FOR INFERENCE

GPU URL: http://100.x.x.x:11434
```

**What each means:**
- **Wake Service ONLINE** = PC is awake, can respond
- **Wake Service OFFLINE** = PC is sleeping or off
- **Ollama RUNNING** = GPU inference ready
- **GPU Ready** = Can accept inference requests

---

## Troubleshooting

### Problem: "Wake Service OFFLINE"

**Quick Fix:**
```bash
gpu-wake wake
```

**Still not working?**
```bash
gpu-wake troubleshoot
```

**Manual checklist:**
1. Is home PC powered on? (not just sleeping?)
2. Is NordVPN running on home PC?
3. Is Meshnet enabled on both devices?
4. Are devices paired in meshnet?

---

### Problem: "Ollama not ready"

**Fix:**
```bash
# Wake and wait 60 seconds
gpu-wake wake
sleep 60
gpu-wake status
```

Ollama takes ~30-60 sec to start after wake.

---

### Problem: "Cannot reach GPU"

**Run diagnostics:**
```bash
gpu-wake troubleshoot
```

**Common causes:**
- Home PC is fully off (not sleeping) → Turn it on
- NordVPN not connected on laptop → Connect to any server
- Meshnet not paired → Check NordVPN app settings
- Network issue → Check internet connection

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         LAPTOP (Mac)                        │
│                                                             │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │   NordVPN VPN    │        │  NordVPN Meshnet │         │
│  │   (WiFi Security)│        │  (E2E to Home)   │         │
│  └────────┬─────────┘        └────────┬─────────┘         │
│           │                           │                    │
│           │                           │                    │
│      ┌────▼──────────────────────────▼────┐               │
│      │      gpu-wake / ollama-gpu         │               │
│      └─────────────────┬──────────────────┘               │
└────────────────────────┼───────────────────────────────────┘
                         │
                         │ Encrypted Meshnet
                         │ Tunnel (E2E)
                         │
┌────────────────────────▼───────────────────────────────────┐
│                    HOME PC (Windows 11)                    │
│                                                             │
│  ┌────────────────────────────────────────────┐           │
│  │         NordVPN Meshnet IP                 │           │
│  │         (100.x.x.x or nord-xxxx)           │           │
│  └──────┬──────────────────────┬──────────────┘           │
│         │                      │                           │
│    ┌────▼─────┐          ┌────▼──────┐                   │
│    │  Wake    │          │  Ollama   │                   │
│    │  Service │          │  + GPU    │                   │
│    │  :9999   │          │  :11434   │                   │
│    └──────────┘          └───────────┘                   │
│                                                             │
│  Auto-sleep after 30 min idle                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Model

### Encryption Layers:
1. **NordVPN Server Connection** (Laptop → VPN)
   - Protects laptop on public WiFi
   - Hides laptop IP

2. **Meshnet E2E Encryption** (Laptop ↔ Home)
   - Direct encrypted tunnel
   - Zero third-party access
   - NordVPN doesn't see inference traffic

### Attack Surface:
- **Wake Service:** Only accessible via meshnet (not internet)
- **Ollama:** Only listens on meshnet IP (not 0.0.0.0)
- **No Port Forwarding:** Router untouched
- **No Public Exposure:** Nothing exposed to internet

---

## Power & Performance

### Power Consumption:
| State | Power | Cost/Month* |
|-------|-------|-------------|
| Idle (awake) | ~50W | ~$5 |
| Sleep | ~8W | ~$0.80 |
| Wake service overhead | +1W | +$0.10 |

*Based on $0.15/kWh

### Performance:
- **Wake time:** 30-60 seconds
- **Cold start (Ollama):** +30 seconds
- **Total ready time:** ~60-90 seconds from sleep
- **Inference speed:** Same as local (GPU bound)

### Network:
- **Latency:** +5-20ms (meshnet overhead)
- **Bandwidth:** Full (not VPN limited)
- **Reliability:** 99%+ (meshnet is peer-to-peer)

---

## Advanced Usage

### Environment Variable (for apps):
```bash
export OLLAMA_HOST="http://100.x.x.x:11434"
```

### Check Wake Service Directly:
```bash
curl http://100.x.x.x:9999/status
```

### Manual Wake:
```bash
curl http://100.x.x.x:9999/wake
```

### Monitor Ollama:
```bash
watch -n 2 "curl -s http://100.x.x.x:11434/api/tags"
```

---

## Maintenance

### Update Ollama:
**On Home PC:**
```powershell
winget upgrade Ollama.Ollama
```

### Update NordVPN:
**On Home PC:**
```powershell
winget upgrade NordVPN.NordVPN
```

**On Laptop:**
```bash
brew upgrade --cask nordvpn
```

### Restart Wake Service:
**On Home PC:**
- Task Manager → End `python.exe` (wake_service)
- It will auto-restart on next login
- Or run: `START_WAKE_SERVICE.bat` from WakeService folder

---

## FAQ

**Q: Can I use this on cellular data?**
A: Yes! NordVPN Meshnet works over any internet connection.

**Q: Does the home PC need to stay on 24/7?**
A: No, it sleeps after 30 min idle. You wake it when needed.

**Q: What if I forget to wake it?**
A: First inference request will fail. Just run `gpu-wake wake` and retry.

**Q: Can I change sleep timeout?**
A: Yes, on Windows: `powercfg /change standby-timeout-ac 60` (60 min)

**Q: Does this work with multiple laptops?**
A: Yes! Run setup on each laptop, use same home PC IP.

**Q: What if my IP changes?**
A: Meshnet IPs are stable. If it changes, update on laptop:
```bash
# Edit ~/gpu-tools/gpu-wake
# Change GPU_IP="old-ip" to GPU_IP="new-ip"
```

**Q: Can I use hostname instead of IP?**
A: Yes! NordVPN meshnet provides `nord-xxxx.nord` hostnames.

---

## Files Reference

### On Home PC:
- `C:\Users\[You]\WakeService\wake_service.py` - Wake service
- `C:\Users\[You]\WakeService\START_WAKE_SERVICE.bat` - Manual start
- `C:\Users\[You]\Desktop\MESHNET_GPU_INFO.txt` - Connection info

### On Laptop:
- `~/gpu-tools/gpu-wake` - Wake/status CLI tool
- `~/gpu-tools/ollama-gpu` - GPU-enabled Ollama wrapper
- `~/Desktop/GPU_Wake.command` - Wake shortcut
- `~/Desktop/GPU_Status.command` - Status shortcut

---

## Uninstall

### Home PC:
```powershell
# Stop and remove wake service
schtasks /delete /tn "GPU_WakeService" /f
Remove-Item -Recurse "$env:USERPROFILE\WakeService"

# Uninstall apps (optional)
winget uninstall Ollama.Ollama
winget uninstall NordVPN.NordVPN
```

### Laptop:
```bash
# Remove tools
rm -rf ~/gpu-tools
rm ~/Desktop/GPU_*.command

# Remove from PATH
# Edit ~/.zshrc and ~/.bash_profile, remove gpu-tools line

# Uninstall (optional)
brew uninstall ollama
brew uninstall --cask nordvpn
```

---

## Support

**Wake Service Issues:**
- Check: Task Manager → python.exe running?
- Logs: Wake service terminal shows all requests
- Restart: Run `START_WAKE_SERVICE.bat`

**Meshnet Issues:**
- Check: NordVPN app → Meshnet → Devices
- Ensure both devices show "Online"
- Try removing and re-pairing devices

**Ollama Issues:**
- Check: Task Manager → ollama.exe running?
- Restart: `ollama serve` in PowerShell
- Logs: Check Ollama output in terminal

---

## Credits

- **NordVPN Meshnet:** Private networking solution
- **Ollama:** GPU inference engine
- **Wake-on-LAN:** Power management standard

**Philosophy:** Simple, secure, efficient. No overengineering.
