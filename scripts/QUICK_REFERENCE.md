# GPU Server - Quick Reference Card
**Print this and keep near your laptop**

---

## Daily Checklist

### Before Using GPU:
```
1. ☐ Turn on home PC (if completely off)
2. ☐ Connect NordVPN on laptop
3. ☐ Double-click "GPU_Wake" on desktop
4. ☐ Wait for ✅ green checkmarks
5. ☐ Start inference!
```

---

## Commands You'll Use

### Desktop Shortcuts (Mac):
- **GPU_Wake.command** → Wake GPU (double-click)
- **GPU_Status.command** → Check status (double-click)

### Terminal Commands:
```bash
# Check if ready
gpu-wake status

# Wake from sleep
gpu-wake wake

# Something broken?
gpu-wake troubleshoot

# Use GPU
ollama-gpu run llama2
ollama-gpu list
```

---

## Status Guide

### ✅ Everything Working:
```
Wake Service:  ✅ ONLINE
Status:        ✅ AWAKE
Ollama:        ✅ RUNNING
GPU Ready:     ✅ READY FOR INFERENCE
```
**Action:** You're good! Start inferencing.

---

### ⚠️ GPU Sleeping:
```
Wake Service:  ❌ OFFLINE (sleeping)
```
**Action:**
```bash
gpu-wake wake
# Wait 60 seconds
gpu-wake status
```

---

### ❌ GPU Unreachable:
```
Wake Service:  ❌ OFFLINE
Cannot reach GPU
```
**Action:**
1. Check home PC is powered on
2. Check NordVPN connected on laptop
3. Run: `gpu-wake troubleshoot`

---

## Troubleshooting Flowchart

```
GPU not working?
    │
    ├─ Is laptop connected to NordVPN?
    │   No → Connect to any VPN server
    │   Yes → Continue
    │
    ├─ Run: gpu-wake troubleshoot
    │   Look for ❌ red X's
    │
    ├─ Is home PC on?
    │   No → Turn it on, wait 2 min
    │   Yes → Continue
    │
    ├─ Is Wake Service online?
    │   No → Run: gpu-wake wake
    │   Yes → Continue
    │
    └─ Still broken?
        → Check meshnet in NordVPN app
        → Devices should show "Online"
```

---

## Common Scenarios

### Scenario: "First use of the day"
```bash
# PC was sleeping all night
gpu-wake wake
# Wait ~60 seconds
gpu-wake status
# Should show all ✅
```

---

### Scenario: "PC was fully shut down"
```bash
# 1. Turn on PC manually (walk to it)
# 2. Wait ~3 minutes for Windows to boot
# 3. Then:
gpu-wake status
# Should work now
```

---

### Scenario: "Ollama not ready"
```bash
# Common after wake
gpu-wake wake
sleep 60  # Wait for Ollama to start
gpu-wake status
```

---

### Scenario: "Changed location/WiFi"
```bash
# 1. Disconnect/reconnect NordVPN
# 2. Then:
gpu-wake status
```

---

## Emergency Contacts

### Home PC Info:
```
Meshnet IP: _________________ (check desktop file)
GPU URL:    http://[IP]:11434
Wake URL:   http://[IP]:9999
```

### If Nothing Works:
1. Restart home PC
2. Restart laptop
3. Reconnect NordVPN on both
4. Run setup scripts again

---

## Power Schedule

**Home PC Auto-Sleep:**
- After 30 minutes of no use
- Wake service keeps running
- Wake time: ~60 seconds

**Don't Worry About:**
- Leaving it on - it auto-sleeps
- Turning it off - wake won't work if fully off
- Power bill - sleep uses ~8W

---

## One-Liner Cheat Sheet

```bash
# Status check
gpu-wake status

# Wake up
gpu-wake wake && sleep 60 && gpu-wake status

# Full diagnostic
gpu-wake troubleshoot

# Use GPU immediately (if awake)
ollama-gpu run llama2 "Hello!"

# List available models
ollama-gpu list

# Pull new model
ollama-gpu pull mistral
```

---

## URLs to Bookmark

### Home PC Desktop File:
`MESHNET_GPU_INFO.txt` - Has all connection details

### Check GPU Manually:
`http://[meshnet-ip]:11434/api/tags`
- If loads → GPU working
- If timeout → GPU asleep/off

---

## Monthly Maintenance

```bash
# Update everything (run on first of month)

# On laptop:
brew upgrade --cask nordvpn
brew upgrade ollama

# On home PC:
winget upgrade --all
```

---

## Security Checklist

✅ **Always verify:**
- [ ] NordVPN connected on laptop (for WiFi security)
- [ ] Meshnet enabled (for E2E encryption)
- [ ] No port forwarding on router (should be none)
- [ ] Ollama only on meshnet IP (not 0.0.0.0)

---

## Pro Tips

💡 **Add alias to shell:**
```bash
# Add to ~/.zshrc or ~/.bash_profile
alias gpu='gpu-wake status'
alias wake='gpu-wake wake'
alias grun='ollama-gpu run'
```

💡 **Check before starting big job:**
```bash
gpu-wake status && ollama-gpu run llama2
```

💡 **Morning routine:**
```bash
# One command to wake and verify
gpu-wake wake && sleep 60 && ollama-gpu list
```

---

**Date Setup:** _______________
**Home PC Meshnet IP:** _______________
**Notes:**
_________________________________
_________________________________
_________________________________
