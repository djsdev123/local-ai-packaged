# Local AI Package - Self-Bootstrapping Guide

This guide explains how to use the new self-bootstrapping system with Gitea, Infisical, and SOPS encryption for a fully portable, self-hosted AI development environment.

## 🎯 Overview

The enhanced Local AI Package now includes:

- **🤖 Interactive Bootstrap Wizard** - Auto-generates secrets and prompts only for necessary credentials
- **🔐 SOPS Encryption** - Encrypt secrets with Age for safe Git storage
- **📦 Gitea Integration** - Self-hosted Git server for version control
- **🔑 Infisical Integration** - Modern secret management with UI
- **💾 Export/Import System** - Complete environment portability

## 📋 Prerequisites

### Required
- **Docker** & **Docker Compose** - Container orchestration
- **Python 3.8+** - For bootstrap scripts
- **Git** - Version control

### Optional (for encryption)
- **SOPS** - Secret encryption tool
- **Age** - Modern encryption tool

### Installation

```bash
# macOS
brew install docker python3 git sops age

# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose python3 python3-pip git
# Install SOPS and Age from releases:
# https://github.com/getsops/sops/releases
# https://github.com/FiloSottile/age/releases

# Verify installation
docker --version
docker compose version
python3 --version
git --version
sops --version  # optional
age --version   # optional
```

## 🚀 Quick Start

### Step 1: Clone Repository

```bash
git clone https://github.com/coleam00/local-ai-packaged.git
cd local-ai-packaged
```

### Step 2: Run Bootstrap Wizard

```bash
python3 bootstrap.py
```

The wizard will:
1. ✅ Check prerequisites
2. 🔍 Auto-detect hardware (CPU/GPU)
3. 💬 Prompt for necessary credentials
4. 🔐 Auto-generate all cryptographic secrets
5. ✍️ Create `.env` configuration file

**Example Session:**

```
============================================================
                Checking Prerequisites
============================================================

✓ docker is installed
✓ docker-compose is installed
✓ git is installed
⚠ sops is not installed (optional - needed for encryption)
⚠ age is not installed (optional - needed for encryption)

============================================================
              Credential Configuration
============================================================

ℹ Detecting hardware configuration...
✓ Detected NVIDIA GPU
? Use GPU acceleration? [Y/n]: y

ℹ Environment types:
  1. Private (development) - All ports exposed locally
  2. Public (production) - Only ports 80/443 exposed via Caddy
? Select environment [1]: 1

ℹ Generating n8n secrets...
✓ n8n secrets generated

ℹ PostgreSQL Configuration
? Auto-generate PostgreSQL password? [Y/n]: y
✓ PostgreSQL password generated

? Supabase dashboard username [supabase]: admin
? Supabase dashboard password: ************
✓ Supabase secrets generated

? Neo4j password: ************

✓ Langfuse secrets generated
✓ Gitea secrets generated
✓ Infisical secrets generated

============================================================
              Bootstrap Complete!
============================================================

✓ Hardware Profile: gpu-nvidia
✓ Environment: private
✓ Configuration saved to: .env

Next steps:
  1. Review your configuration: cat .env
  2. Start services: python start_services.py --profile gpu-nvidia --environment private
  3. (Optional) Encrypt secrets: sops --encrypt .env > .env.enc
  4. Access services at:
     - n8n: http://localhost:5678
     - Open WebUI: http://localhost:8080
     - Gitea: http://localhost:9000
     - Infisical: http://localhost:9001
     - Langfuse: http://localhost:3000
```

### Step 3: Start Services

```bash
# The wizard tells you the exact command based on your hardware
python start_services.py --profile gpu-nvidia --environment private
```

### Step 4: Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **n8n** | http://localhost:5678 | Workflow automation |
| **Open WebUI** | http://localhost:8080 | ChatGPT-like interface |
| **Gitea** | http://localhost:9000 | Self-hosted Git |
| **Infisical** | http://localhost:9001 | Secret management |
| **Langfuse** | http://localhost:3000 | LLM observability |
| **Flowise** | http://localhost:3001 | AI agent builder |
| **Supabase** | http://localhost:8005 | Database & storage |
| **Neo4j** | http://localhost:7474 | Knowledge graphs |

## 🔐 Secret Management Workflow

### Option 1: SOPS + Age (Recommended for Git)

Encrypt secrets for safe storage in version control:

```bash
# 1. Encrypt secrets
python localai_cli.py encrypt

# This will:
# - Generate Age encryption key
# - Update .sops.yaml with public key
# - Encrypt .env → .env.enc
# - Update .gitignore
# - Commit encrypted file

# 2. Push to Git
git push

# 3. On another machine, decrypt:
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
sops --decrypt .env.enc > .env
```

**⚠️ Important:** Back up your Age private key at `~/.config/sops/age/keys.txt`

### Option 2: Gitea (Self-Hosted Git)

Push your repository to the local Gitea instance:

```bash
# 1. Setup Gitea and create repository
python localai_cli.py setup-gitea

# 2. Push code and encrypted secrets
git push gitea main

# Access: http://localhost:9000
```

### Option 3: Infisical (Secret Management UI)

Use Infisical for team-based secret management:

```bash
# 1. Open Infisical: http://localhost:9001
# 2. Create account and project
# 3. Sync secrets:

python localai_cli.py sync-infisical --push

# Or use Infisical CLI:
infisical login
infisical init
infisical secrets set --env dev --from-file .env
```

## 💾 Export/Import System

### Export Complete Environment

```bash
# Full backup (includes Docker volumes)
python localai_cli.py export --format full

# Config only (no volumes, faster)
python localai_cli.py export --format config

# Output: backups/localai_backup_YYYYMMDD_HHMMSS.tar.gz
```

**Export includes:**
- ✅ All configuration files (`.env`, docker-compose, Caddyfile, etc.)
- ✅ Encrypted secrets (`.env.enc`)
- ✅ Docker volumes (n8n workflows, databases, etc.) - if `--format full`
- ✅ Metadata (hardware profile, timestamp, checksums)

### Import on New Machine

```bash
# 1. Clone repository
git clone https://github.com/coleam00/local-ai-packaged.git
cd local-ai-packaged

# 2. Import backup
python localai_cli.py import backups/localai_backup_20250121_120000.tar.gz

# 3. Decrypt secrets (if needed)
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
python localai_cli.py decrypt

# 4. Start services
python start_services.py
```

## 🔄 Complete Workflow Examples

### Scenario 1: Development → Production Migration

```bash
# On development machine
python bootstrap.py  # Create dev environment
python localai_cli.py encrypt  # Encrypt secrets
python localai_cli.py export --format full  # Full backup

# Copy backup to production server
scp backups/localai_backup_*.tar.gz user@prod-server:~/

# On production server
python localai_cli.py import localai_backup_*.tar.gz
python localai_cli.py decrypt
python bootstrap.py  # Reconfigure for production domains
python start_services.py --environment public
```

### Scenario 2: Team Collaboration with Gitea

```bash
# Team Lead (initial setup)
python bootstrap.py
python localai_cli.py setup-gitea
python scripts/encrypt_secrets.py
git push gitea main

# Team Member (clone and setup)
git clone http://gitea-server:9000/admin/local-ai-packaged.git
cd local-ai-packaged

# Get Age key from team lead (secure channel!)
# Copy to ~/.config/sops/age/keys.txt

sops --decrypt .env.enc > .env
python start_services.py
```

### Scenario 3: Multi-Environment Setup

```bash
# Development
python bootstrap.py  # Use private environment
cp .env .env.dev

# Staging
python bootstrap.py  # Generate new secrets
cp .env .env.staging

# Production
python bootstrap.py  # Generate new secrets
cp .env .env.prod

# Switch environments
cp .env.dev .env && python start_services.py --environment private
cp .env.prod .env && python start_services.py --environment public
```

## 🛠️ Advanced Configuration

### Custom Hardware Profiles

Edit `start_services.py` to add custom profiles:

```python
# For Apple Silicon
if creds['HARDWARE_PROFILE'] == "apple-silicon":
    # Use native Ollama on macOS
    # Point Docker containers to host.docker.internal:11434
```

### Custom Domain Setup (Production)

```bash
# 1. Bootstrap with public environment
python bootstrap.py
# Select: 2. Public (production)
# Enter your domains when prompted

# 2. Configure DNS A records:
# n8n.yourdomain.com → server-ip
# openwebui.yourdomain.com → server-ip
# etc.

# 3. Start with public profile
python start_services.py --environment public

# Caddy automatically handles Let's Encrypt SSL!
```

### Firewall Configuration (Production)

```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw status
```

## 🐛 Troubleshooting

### Bootstrap Issues

```bash
# Validate environment
python localai_cli.py validate

# Check Docker status
docker ps
docker compose -p localai ps

# View logs
docker compose -p localai logs -f
```

### SOPS Encryption Issues

```bash
# Check Age key exists
ls ~/.config/sops/age/keys.txt

# Verify SOPS config
cat .sops.yaml

# Test encryption manually
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
sops --encrypt .env > test.enc
sops --decrypt test.enc
```

### Gitea Connection Issues

```bash
# Check Gitea is running
docker ps | grep gitea

# Test connection
curl http://localhost:9000/api/v1/version

# Reset Gitea admin user
docker exec gitea /usr/local/bin/gitea admin user list
```

### Import Failures

```bash
# Verify backup integrity
sha256sum -c backups/localai_backup_*.tar.gz.sha256

# Import configs only (skip volumes)
python localai_cli.py import --skip-volumes backups/backup.tar.gz

# Manually inspect backup
tar -tzf backups/localai_backup_*.tar.gz
```

## 📚 Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Secret Management**: [SECRETS.md](docs/SECRETS.md)
- **Migration Guide**: [MIGRATION.md](docs/MIGRATION.md)
- **SOPS Documentation**: https://github.com/getsops/sops
- **Age Documentation**: https://github.com/FiloSottile/age
- **Infisical Documentation**: https://infisical.com/docs

## 🔒 Security Best Practices

1. **Never commit `.env` to Git** - Always use `.env.enc` (encrypted)
2. **Back up Age private key** - Store securely (password manager, hardware key)
3. **Use different secrets per environment** - Don't reuse dev secrets in prod
4. **Rotate secrets regularly** - Especially for production
5. **Use strong passwords** - Bootstrap wizard enforces minimum lengths
6. **Enable 2FA on Gitea/Infisical** - For production deployments
7. **Restrict Gitea registration** - Set `GITEA_DISABLE_REGISTRATION=true` in prod

## 🎓 Learning Path

1. **Start Simple**: Use `bootstrap.py` → `start_services.py`
2. **Add Encryption**: Learn SOPS with `localai_cli.py encrypt`
3. **Setup Gitea**: Push to local Git with `localai_cli.py setup-gitea`
4. **Export/Import**: Practice portability with `localai_cli.py export/import`
5. **Production Deploy**: Use public environment with custom domains

## 🤝 Contributing

Found a bug or have an enhancement? Please open an issue or PR!

## 📝 License

[Same as parent project]

---

**Need Help?** Open an issue on GitHub or check existing documentation in the `docs/` folder.
