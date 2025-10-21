# Local AI Package - Quick Start Guide

## 🚀 TL;DR - Get Running in 5 Minutes

```bash
# 1. Clone
git clone https://github.com/coleam00/local-ai-packaged.git
cd local-ai-packaged

# 2. Bootstrap (auto-generates all secrets)
python3 bootstrap.py

# 3. Start (use the command the wizard gives you)
python start_services.py --profile gpu-nvidia --environment private

# 4. Access
# n8n: http://localhost:5678
# Open WebUI: http://localhost:8080
# Gitea: http://localhost:9000
# Infisical: http://localhost:9001
```

## 📦 What You Get

| Service | Port | Purpose |
|---------|------|---------|
| **n8n** | 5678 | Workflow automation (like Zapier) |
| **Open WebUI** | 8080 | ChatGPT-like interface for local LLMs |
| **Gitea** | 9000 | Your own GitHub (self-hosted Git) |
| **Infisical** | 9001 | Secret management with UI |
| **Langfuse** | 3000 | LLM observability & analytics |
| **Flowise** | 3001 | No-code AI agent builder |
| **Supabase** | 8005 | Database & backend (like Firebase) |
| **Neo4j** | 7474 | Knowledge graph database |

## 🔑 Secret Management Options

### Option 1: Just Use It (Development)
```bash
python3 bootstrap.py  # Done! Secrets stored in .env
```

### Option 2: Encrypt for Git (Recommended)
```bash
# Install SOPS & Age
brew install sops age  # macOS
# or download from GitHub releases

# Encrypt
python localai_cli.py encrypt

# Now safe to commit .env.enc to Git!
git add .env.enc .sops.yaml
git commit -m "Add encrypted secrets"
git push
```

### Option 3: Use Gitea (Self-Hosted Git)
```bash
# Setup local Git server
python localai_cli.py setup-gitea

# Push to it
git push gitea main

# Access at http://localhost:9000
```

### Option 4: Use Infisical (Team Secret Management)
```bash
# Open http://localhost:9001
# Create account → Create project → Get token

# Sync secrets
python localai_cli.py sync-infisical --push
```

## 💾 Backup & Restore

### Backup Everything
```bash
python localai_cli.py export --format full
# Creates: backups/localai_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Restore on New Machine
```bash
python localai_cli.py import backups/localai_backup_*.tar.gz
python localai_cli.py decrypt  # if encrypted
python start_services.py
```

## 🎓 Next Steps

1. **Read Full Docs**: [BOOTSTRAP.md](BOOTSTRAP.md)
2. **Learn n8n**: http://localhost:5678 - Pre-loaded with AI workflows
3. **Try Open WebUI**: http://localhost:8080 - Chat with local LLMs
4. **Build AI Agents**: http://localhost:3001 - Flowise drag-and-drop
5. **Monitor LLMs**: http://localhost:3000 - Langfuse analytics

## 🔥 Common Tasks

### Change Hardware Profile
```bash
# Was using CPU, now have GPU
python start_services.py --profile gpu-nvidia --environment private
```

### Deploy to Production
```bash
# 1. Re-run bootstrap for production
python bootstrap.py
# Select: 2. Public (production)
# Enter your domains

# 2. Configure DNS A records
# n8n.yourdomain.com → your-server-ip

# 3. Start
python start_services.py --environment public
# Caddy auto-handles SSL with Let's Encrypt!
```

### Share with Team
```bash
# Encrypt secrets
python localai_cli.py encrypt

# Push to Gitea
python localai_cli.py setup-gitea
git push gitea main

# Team clones from Gitea
# Share Age encryption key securely
# Team decrypts and runs
```

## ❓ Troubleshooting

```bash
# Check everything is OK
python localai_cli.py validate

# View logs
docker compose -p localai logs -f

# Restart everything
docker compose -p localai restart

# Nuclear option (start fresh)
docker compose -p localai down -v
python bootstrap.py
python start_services.py
```

## 📚 Full Documentation

- **Complete Guide**: [BOOTSTRAP.md](BOOTSTRAP.md)
- **Main README**: [README.md](README.md)
- **Original Docs**: Check the repo for detailed service configs

## 🆘 Help

- **GitHub Issues**: Report bugs or ask questions
- **Docker Issues**: Ensure Docker Desktop is running
- **Port Conflicts**: Services already running on ports? Stop them or use different ports

---

**Happy Building! 🚀**
