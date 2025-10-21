# Open WebUI - Your ChatGPT-Like Interface for GPU

## What Is This?

Open WebUI gives you a **beautiful, ChatGPT-like interface** to your home GPU. No CLI needed!

```
┌────────────────────────────────────┐
│  Open WebUI (on your Mac)         │
│                                    │
│  ┌──────────────────────────────┐ │
│  │ Chat with your AI models     │ │
│  │ Just like ChatGPT!           │ │
│  │                              │ │
│  │ Models auto-appear from GPU  │ │
│  │ Beautiful web interface      │ │
│  │ Chat history saved           │ │
│  └──────────────────────────────┘ │
│                                    │
│  http://localhost:3000             │
└────────────────────────────────────┘
           │
           │ Encrypted Meshnet
           ▼
┌────────────────────────────────────┐
│  Home GPU Server (Windows)         │
│  • Ollama + Your GPU               │
│  • All your AI models              │
└────────────────────────────────────┘
```

---

## Setup (Already Automated!)

The `LAPTOP_SETUP.sh` script automatically:
1. ✅ Installs Docker Desktop
2. ✅ Pulls Open WebUI container
3. ✅ Configures it with your GPU URL
4. ✅ Creates desktop launcher
5. ✅ Starts the web interface

**You don't need to do anything manually!**

---

## How to Use

### First Time:
1. **Double-click `Open_WebUI.command`** on your desktop
2. Browser opens to `http://localhost:3000`
3. **Create an account** (stored locally, not cloud)
4. **Start chatting!** Your GPU models appear automatically

### Daily Use:
1. **Wake GPU if needed:** `gpu-wake wake` (or double-click GPU_Wake.command)
2. **Launch Open WebUI:** Double-click `Open_WebUI.command`
3. **Chat with AI!** Select a model and start typing

---

## Features

### ChatGPT-Like Interface:
- 💬 **Clean chat interface** - Just like ChatGPT
- 📚 **Chat history** - All conversations saved
- 🎨 **Multiple conversations** - Switch between chats
- 🔧 **Model selector** - Pick any model from GPU
- ⚙️ **Settings** - Customize temperature, tokens, etc.

### Automatic GPU Integration:
- ✅ **Pre-configured** - Points to your GPU automatically
- ✅ **Model sync** - Models from GPU appear instantly
- ✅ **No manual setup** - Works out of the box
- ✅ **Secure** - All traffic over encrypted meshnet

### Local & Private:
- 🔒 **Runs on your Mac** - Nothing in the cloud
- 🔒 **Data stays local** - Chats saved on your computer
- 🔒 **E2E encrypted** - GPU traffic over meshnet
- 🔒 **Zero tracking** - Completely private

---

## Desktop Workflow

### Recommended Daily Routine:

```bash
Morning:
1. Double-click "GPU_Wake.command"     # Wake home PC
2. Wait 60 seconds for GPU to wake
3. Double-click "Open_WebUI.command"   # Start web UI
4. Browse to http://localhost:3000
5. Start chatting!

Evening:
Just close the browser. GPU auto-sleeps after 30 min.
```

---

## Troubleshooting

### Problem: "Can't connect to Docker"
**Fix:**
1. Open Applications → Docker Desktop
2. Wait for whale icon in menu bar
3. Try again

---

### Problem: "No models showing in Open WebUI"
**Fix:**
1. GPU is probably asleep
2. Run: `gpu-wake wake`
3. Wait 60 seconds
4. Refresh browser (⌘+R)

---

### Problem: "Open WebUI won't start"
**Fix:**
```bash
# Restart it manually
docker stop open-webui
docker rm open-webui
~/gpu-tools/start-webui
```

---

### Problem: "Models loading but inference fails"
**Fix:**
1. Check GPU status: `gpu-wake status`
2. Should show all ✅
3. If not, wake GPU: `gpu-wake wake`

---

## Advanced Usage

### Change GPU Connection:
```bash
# If your GPU IP changes
docker stop open-webui
docker rm open-webui

# Edit ~/gpu-tools/start-webui
# Update GPU_URL="http://NEW-IP:11434"

~/gpu-tools/start-webui
```

### View Open WebUI Logs:
```bash
docker logs open-webui
```

### Access from Another Device on Same Network:
```bash
# Find your Mac's IP
ipconfig getifaddr en0

# On other device, browse to:
http://[mac-ip]:3000
```

### Update Open WebUI:
```bash
docker stop open-webui
docker rm open-webui
docker pull ghcr.io/open-webui/open-webui:main
~/gpu-tools/start-webui
```

---

## vs CLI Usage

| Feature | Open WebUI | CLI (ollama-gpu) |
|---------|-----------|------------------|
| Interface | Web (ChatGPT-like) | Terminal |
| Chat history | ✅ Saved automatically | ❌ Not saved |
| Multiple chats | ✅ Yes | ❌ No |
| Model switching | ✅ Dropdown menu | Manual command |
| Settings | ✅ Visual sliders | Manual flags |
| Learning curve | Easy (like ChatGPT) | Requires CLI knowledge |
| Use case | Daily chatting | Scripts, automation |

**Recommendation:** Use Open WebUI for interactive chatting, CLI for scripts.

---

## What Gets Installed

### Docker Container:
- **Image:** `ghcr.io/open-webui/open-webui:main`
- **Port:** 3000 (Mac) → 8080 (container)
- **Volume:** `open-webui` (persistent chat storage)
- **Auto-restart:** Yes (unless-stopped)

### Environment Variables:
- `OLLAMA_BASE_URL=http://[your-gpu-ip]:11434`

### Files Created:
- `~/gpu-tools/start-webui` - Restart script
- `~/Desktop/Open_WebUI.command` - Desktop launcher

---

## Security

### Data Storage:
- **Chats:** Stored locally in Docker volume on your Mac
- **Models:** On home GPU (not copied to Mac)
- **Account:** Local only (no cloud sync)

### Network:
- **Open WebUI → Mac:** localhost (127.0.0.1)
- **Mac → GPU:** Encrypted meshnet
- **No external access:** Firewall-friendly

### Privacy:
- ✅ Zero telemetry to Open WebUI developers
- ✅ No cloud storage
- ✅ All inference on your hardware
- ✅ Chats never leave your devices

---

## Uninstall

### Remove Open WebUI:
```bash
# Stop and remove container
docker stop open-webui
docker rm open-webui

# Remove data (optional - deletes chat history!)
docker volume rm open-webui

# Remove image
docker rmi ghcr.io/open-webui/open-webui:main

# Remove scripts
rm ~/gpu-tools/start-webui
rm ~/Desktop/Open_WebUI.command
```

### Keep Docker:
Docker Desktop is useful for other things. Only uninstall if you want:
```bash
# Uninstall Docker Desktop
brew uninstall --cask docker
```

---

## Tips & Tricks

### 💡 Auto-start on Mac Login:
1. System Settings → General → Login Items
2. Click "+" → Add `Docker.app`
3. Add `Open_WebUI.command` (optional)

### 💡 Keyboard Shortcuts:
- `⌘+K` - New chat
- `⌘+/` - Search chats
- `⌘+Enter` - Send message
- `⌘+R` - Refresh (if models not showing)

### 💡 Model Management:
**Download new models on GPU:**
```bash
# From Mac terminal
ollama-gpu pull llama3
ollama-gpu pull codellama
ollama-gpu pull mistral

# Models appear in Open WebUI immediately
```

### 💡 Share Chats:
- Export: Click chat → "..." → Export
- Import: Upload exported JSON

### 💡 Customize Appearance:
- Settings → Interface → Theme (Light/Dark)
- Settings → Interface → Language

---

## Example Workflows

### Workflow 1: Code Assistant
1. Open WebUI → New Chat
2. Select `codellama` model
3. Type: "Write a Python function to parse JSON"
4. Get code + explanations
5. Copy code to your IDE

### Workflow 2: Writing Assistant
1. Open WebUI → New Chat
2. Select `llama3` model
3. Type: "Help me write a professional email"
4. Iterate on the response
5. Copy final version

### Workflow 3: Learning
1. Open WebUI → New Chat
2. Select `llama3` model
3. Type: "Explain quantum computing like I'm 5"
4. Ask follow-up questions
5. All Q&A saved in chat history

---

## Comparison to Other Solutions

### vs ChatGPT:
| | Open WebUI + Home GPU | ChatGPT |
|---|---|---|
| Privacy | ✅ 100% local | ❌ Cloud-based |
| Cost | ✅ Free (your hardware) | 💰 $20/month |
| Speed | ⚡ GPU-dependent | ⚡ Fast |
| Offline | ⚠️ Needs GPU connection | ❌ Needs internet |
| Models | ⚡ Ollama library | GPT-3.5/4 |

### vs Ollama CLI:
| | Open WebUI | Ollama CLI |
|---|---|---|
| Interface | Web UI | Terminal |
| Chat history | ✅ Saved | ❌ Not saved |
| Easy to use | ✅ Very | ⚠️ CLI knowledge needed |
| Automation | ❌ Manual | ✅ Scriptable |

---

## FAQ

**Q: Do I need to install Ollama on my Mac?**
A: Yes, but only for the `ollama-gpu` CLI tool. Open WebUI connects directly to your GPU's Ollama via meshnet.

**Q: Can I use Open WebUI without the GPU?**
A: Not with this setup. Open WebUI is configured to use your home GPU. Without GPU access, it won't work.

**Q: Does Open WebUI download models to my Mac?**
A: No! Models stay on your home GPU. Open WebUI just sends/receives text over meshnet.

**Q: Can I access Open WebUI on my phone?**
A: If your phone is on the same WiFi as your Mac, yes:
1. Find Mac IP: `ipconfig getifaddr en0`
2. On phone browser: `http://[mac-ip]:3000`

**Q: What if I'm on cellular and want to use my phone?**
A: You'd need to expose Open WebUI over meshnet (advanced setup, not covered here).

**Q: Is my chat history synced between devices?**
A: No. Chat history is stored locally on your Mac in a Docker volume.

**Q: Can I export my chats?**
A: Yes! Each chat has an export option (... menu → Export).

**Q: Does this work on Windows laptop instead of Mac?**
A: Yes! Use Docker Desktop for Windows and adjust paths accordingly.

---

## System Requirements

### Mac Requirements:
- macOS 10.15+ (Catalina or newer)
- 4GB+ RAM (8GB+ recommended)
- 5GB free disk space (for Docker + Open WebUI)
- Docker Desktop

### GPU Server Requirements:
- Already covered by main setup
- Just needs Ollama running and accessible

---

## Performance

### Response Time:
- **Web UI overhead:** ~10ms (negligible)
- **Meshnet latency:** ~5-20ms
- **GPU inference:** Model-dependent
- **Total:** About the same as direct GPU access

### Resource Usage (on Mac):
- **Open WebUI container:** ~200-500MB RAM
- **Docker Desktop:** ~1-2GB RAM
- **Browser tab:** ~100-200MB RAM
- **Total:** ~1.5-3GB RAM

**Low RAM?** Close Open WebUI when not in use:
```bash
docker stop open-webui
# Restart later with: start-webui
```

---

## Credits

- **Open WebUI:** https://github.com/open-webui/open-webui
- **Ollama:** https://ollama.ai
- **Docker:** https://docker.com

**License:** Open WebUI is MIT licensed (open source)

---

## Summary

✅ **What you get:**
- ChatGPT-like interface on your Mac
- Connected to your home GPU automatically
- Private, local, secure
- Beautiful web UI instead of CLI
- Chat history saved
- Zero configuration needed

✅ **How to use:**
1. Wake GPU: `gpu-wake wake` (or double-click shortcut)
2. Start Open WebUI: Double-click `Open_WebUI.command`
3. Browse to http://localhost:3000
4. Chat with AI!

✅ **Best for:**
- Daily interactive chatting
- Non-technical users
- Anyone who prefers UI over CLI
- Keeping chat history

**Enjoy your private AI assistant! 🎉**
