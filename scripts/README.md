# Scripts Directory

This directory contains helper scripts for the Local AI Package bootstrap system.

## Scripts Overview

### `gitea_setup.py`
**Purpose**: Automatically initialize Gitea and create a repository for the project.

**What it does**:
- Waits for Gitea container to be ready
- Creates admin user via Gitea CLI
- Creates access token for API operations
- Creates a private repository for local-ai-packaged
- Configures git remote pointing to Gitea
- Pushes code to Gitea

**Usage**:
```bash
# Ensure .env has GITEA_ADMIN_USER, GITEA_ADMIN_PASSWORD, GITEA_ADMIN_EMAIL
python scripts/gitea_setup.py

# Or use via CLI
python localai_cli.py setup-gitea
```

**Environment Variables**:
- `GITEA_ADMIN_USER` - Admin username (default: gitea_admin)
- `GITEA_ADMIN_PASSWORD` - Admin password
- `GITEA_ADMIN_EMAIL` - Admin email

---

### `encrypt_secrets.py`
**Purpose**: Encrypt `.env` file with SOPS and Age for safe Git storage.

**What it does**:
- Checks if SOPS and Age are installed
- Generates Age encryption key if not exists
- Updates `.sops.yaml` with Age public key
- Encrypts `.env` → `.env.enc`
- Updates `.gitignore` to allow `.env.enc` but block `.env`
- Commits encrypted file to git
- Optionally pushes to Gitea

**Usage**:
```bash
# Encrypt secrets
python scripts/encrypt_secrets.py

# Or use via CLI
python localai_cli.py encrypt
```

**Prerequisites**:
```bash
# macOS
brew install sops age

# Linux
# Download from:
# - SOPS: https://github.com/getsops/sops/releases
# - Age: https://github.com/FiloSottile/age/releases
```

**Decryption**:
```bash
# On another machine, with Age private key
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
sops --decrypt .env.enc > .env
```

---

### `infisical_sync.py`
**Purpose**: Sync secrets between `.env` file and Infisical secret manager.

**What it does**:
- Waits for Infisical container to be ready
- Reads secrets from `.env` file
- Pushes secrets to Infisical (via CLI or API)
- Provides setup instructions for manual Infisical configuration

**Usage**:
```bash
# Show setup instructions
python scripts/infisical_sync.py

# Push secrets to Infisical
python scripts/infisical_sync.py --push --environment dev

# Pull secrets from Infisical
python scripts/infisical_sync.py --pull --environment dev

# Or use via CLI
python localai_cli.py sync-infisical --push
```

**Manual Setup**:
1. Open Infisical: http://localhost:9001
2. Create account and organization
3. Create project (e.g., "local-ai-packaged")
4. Get service token from Project Settings
5. Export token: `export INFISICAL_TOKEN=<your-token>`
6. Run sync: `python scripts/infisical_sync.py --push`

---

## Integration with Main CLI

All scripts are integrated into the main CLI (`localai_cli.py`):

```bash
# Setup Gitea
python localai_cli.py setup-gitea

# Encrypt secrets
python localai_cli.py encrypt

# Decrypt secrets
python localai_cli.py decrypt

# Sync with Infisical
python localai_cli.py sync-infisical --push
```

## Development

### Adding New Scripts

1. Create script in `scripts/` directory
2. Add execute permission: `chmod +x scripts/your_script.py`
3. Add integration to `localai_cli.py` if needed
4. Document in this README

### Testing

```bash
# Test gitea_setup.py
docker compose -p localai up -d gitea postgres
python scripts/gitea_setup.py

# Test encrypt_secrets.py
echo "TEST_VAR=secret_value" > .env.test
python scripts/encrypt_secrets.py  # Modify to use .env.test

# Test infisical_sync.py
docker compose -p localai up -d infisical infisical-mongo infisical-redis
python scripts/infisical_sync.py
```

## Troubleshooting

### Gitea Setup Fails

```bash
# Check Gitea is running
docker ps | grep gitea

# View Gitea logs
docker logs gitea

# Manually create admin user
docker exec gitea /usr/local/bin/gitea admin user create \
  --username admin --password password --email admin@local.ai --admin
```

### SOPS Encryption Fails

```bash
# Check SOPS and Age are installed
sops --version
age --version

# Verify Age key exists
ls ~/.config/sops/age/keys.txt

# Check .sops.yaml configuration
cat .sops.yaml
```

### Infisical Sync Fails

```bash
# Check Infisical is running
docker ps | grep infisical

# Check Infisical logs
docker logs infisical

# Test Infisical API
curl http://localhost:9001/api/status
```

## Security Notes

- **Never commit `.env` to Git** - Always use `.env.enc` (encrypted)
- **Back up Age private key** - Store at `~/.config/sops/age/keys.txt`
- **Use strong passwords** - Bootstrap wizard enforces minimums
- **Rotate secrets regularly** - Especially for production
- **Secure Age key distribution** - Use secure channels for team sharing

## Contributing

When adding new scripts:

1. Follow Python best practices
2. Add comprehensive error handling
3. Include help text and examples
4. Update this README
5. Add integration to main CLI if appropriate
