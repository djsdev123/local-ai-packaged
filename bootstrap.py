#!/usr/bin/env python3
"""
bootstrap.py - Self-Bootstrapping Wizard for Local AI Package

Interactive CLI that:
- Detects hardware (CPU/GPU type)
- Prompts only for required credentials
- Auto-generates secure secrets
- Validates configurations
- Integrates with Gitea and Infisical
- Encrypts secrets with SOPS
"""

import os
import sys
import subprocess
import secrets
import re
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
import getpass

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def generate_secret(length: int = 32) -> str:
    """Generate a cryptographically secure random secret"""
    return secrets.token_hex(length)


def generate_jwt_secret() -> str:
    """Generate a JWT secret (at least 32 characters)"""
    return secrets.token_urlsafe(48)


def detect_gpu() -> str:
    """Detect GPU type (NVIDIA, AMD, or none)"""
    try:
        # Check for NVIDIA GPU
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            return "gpu-nvidia"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        # Check for AMD GPU (ROCm)
        result = subprocess.run(
            ["rocm-smi"],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            return "gpu-amd"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "cpu"


def check_prerequisites() -> Tuple[bool, list]:
    """Check if required tools are installed"""
    print_header("Checking Prerequisites")

    required = {
        "docker": ["docker", "--version"],
        "docker-compose": ["docker", "compose", "version"],
        "git": ["git", "--version"],
    }

    optional = {
        "sops": ["sops", "--version"],
        "age": ["age", "--version"],
    }

    missing = []
    warnings = []

    for name, cmd in required.items():
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            if result.returncode == 0:
                print_success(f"{name} is installed")
            else:
                print_error(f"{name} is not working properly")
                missing.append(name)
        except FileNotFoundError:
            print_error(f"{name} is not installed")
            missing.append(name)
        except subprocess.TimeoutExpired:
            print_error(f"{name} check timed out")
            missing.append(name)

    for name, cmd in optional.items():
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            if result.returncode == 0:
                print_success(f"{name} is installed (optional)")
            else:
                print_warning(f"{name} is not installed (optional - needed for encryption)")
                warnings.append(name)
        except FileNotFoundError:
            print_warning(f"{name} is not installed (optional - needed for encryption)")
            warnings.append(name)
        except subprocess.TimeoutExpired:
            print_warning(f"{name} check timed out")
            warnings.append(name)

    return len(missing) == 0, missing


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Prompt user for yes/no answer"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{Colors.OKCYAN}? {question} [{default_str}]: {Colors.ENDC}").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print_error("Please answer 'y' or 'n'")


def prompt_input(question: str, default: str = "", allow_empty: bool = False, validator=None) -> str:
    """Prompt user for text input"""
    default_display = f" [{default}]" if default else ""
    while True:
        response = input(f"{Colors.OKCYAN}? {question}{default_display}: {Colors.ENDC}").strip()
        if not response:
            if default:
                return default
            if allow_empty:
                return ""
            print_error("This field is required")
            continue

        if validator:
            valid, message = validator(response)
            if not valid:
                print_error(message)
                continue

        return response


def prompt_password(question: str, min_length: int = 8) -> str:
    """Prompt user for password (hidden input)"""
    while True:
        password = getpass.getpass(f"{Colors.OKCYAN}? {question}: {Colors.ENDC}")
        if len(password) < min_length:
            print_error(f"Password must be at least {min_length} characters")
            continue

        # Check for @ symbol in postgres password
        if "postgres" in question.lower() and "@" in password:
            print_error("Postgres password cannot contain '@' character")
            continue

        confirm = getpass.getpass(f"{Colors.OKCYAN}? Confirm password: {Colors.ENDC}")
        if password != confirm:
            print_error("Passwords do not match")
            continue

        return password


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, ""
    return False, "Invalid email format"


def validate_domain(domain: str) -> Tuple[bool, str]:
    """Validate domain format"""
    if domain.startswith("http://") or domain.startswith("https://"):
        return False, "Domain should not include http:// or https://"

    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(pattern, domain):
        return True, ""
    return False, "Invalid domain format"


def collect_credentials() -> Dict[str, str]:
    """Interactively collect all required credentials"""
    print_header("Credential Configuration")

    creds = {}

    # Auto-detect hardware
    print_info("Detecting hardware configuration...")
    gpu_type = detect_gpu()

    if gpu_type == "gpu-nvidia":
        print_success("Detected NVIDIA GPU")
        use_gpu = prompt_yes_no("Use GPU acceleration?", default=True)
        creds['HARDWARE_PROFILE'] = "gpu-nvidia" if use_gpu else "cpu"
    elif gpu_type == "gpu-amd":
        print_success("Detected AMD GPU")
        use_gpu = prompt_yes_no("Use GPU acceleration?", default=True)
        creds['HARDWARE_PROFILE'] = "gpu-amd" if use_gpu else "cpu"
    else:
        print_info("No GPU detected, using CPU")
        creds['HARDWARE_PROFILE'] = "cpu"

    # Environment selection
    print("\n")
    print_info("Environment types:")
    print("  1. Private (development) - All ports exposed locally")
    print("  2. Public (production) - Only ports 80/443 exposed via Caddy")

    env_choice = prompt_input("Select environment", default="1")
    creds['ENVIRONMENT'] = "private" if env_choice == "1" else "public"

    # Generate n8n secrets
    print("\n")
    print_info("Generating n8n secrets...")
    creds['N8N_ENCRYPTION_KEY'] = generate_secret(32)
    creds['N8N_USER_MANAGEMENT_JWT_SECRET'] = generate_secret(32)
    print_success("n8n secrets generated")

    # PostgreSQL credentials
    print("\n")
    print_info("PostgreSQL Configuration")
    auto_postgres = prompt_yes_no("Auto-generate PostgreSQL password?", default=True)
    if auto_postgres:
        # Generate a secure password without @ symbol
        creds['POSTGRES_PASSWORD'] = generate_secret(32)
        print_success("PostgreSQL password generated")
    else:
        creds['POSTGRES_PASSWORD'] = prompt_password("PostgreSQL password (no @ symbol)", min_length=16)

    # Supabase JWT secrets
    print("\n")
    print_info("Generating Supabase secrets...")
    creds['JWT_SECRET'] = generate_jwt_secret()
    creds['ANON_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE"
    creds['SERVICE_ROLE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q"
    creds['DASHBOARD_USERNAME'] = prompt_input("Supabase dashboard username", default="supabase")
    creds['DASHBOARD_PASSWORD'] = prompt_password("Supabase dashboard password", min_length=12)
    creds['POOLER_TENANT_ID'] = "1000"
    print_success("Supabase secrets generated")

    # Neo4j credentials
    print("\n")
    print_info("Neo4j Configuration")
    neo4j_password = prompt_password("Neo4j password", min_length=8)
    creds['NEO4J_AUTH'] = f"neo4j/{neo4j_password}"

    # Langfuse secrets
    print("\n")
    print_info("Generating Langfuse secrets...")
    creds['CLICKHOUSE_PASSWORD'] = generate_secret(32)
    creds['MINIO_ROOT_PASSWORD'] = generate_secret(32)
    creds['LANGFUSE_SALT'] = generate_secret(32)
    creds['NEXTAUTH_SECRET'] = generate_secret(32)
    creds['ENCRYPTION_KEY'] = generate_secret(32)
    print_success("Langfuse secrets generated")

    # Gitea credentials
    print("\n")
    print_info("Gitea Configuration")
    creds['GITEA_SECRET_KEY'] = generate_secret(32)
    creds['GITEA_INTERNAL_TOKEN'] = generate_secret(32)
    creds['GITEA_ADMIN_USER'] = prompt_input("Gitea admin username", default="gitea_admin")
    creds['GITEA_ADMIN_PASSWORD'] = prompt_password("Gitea admin password", min_length=8)
    creds['GITEA_ADMIN_EMAIL'] = prompt_input("Gitea admin email", default="admin@local.ai", validator=validate_email)
    creds['GITEA_DISABLE_REGISTRATION'] = "false"

    # Infisical credentials
    print("\n")
    print_info("Generating Infisical secrets...")
    creds['INFISICAL_ENCRYPTION_KEY'] = generate_secret(32)
    creds['INFISICAL_JWT_SECRET'] = generate_secret(32)
    creds['INFISICAL_MONGO_USER'] = "infisical"
    creds['INFISICAL_MONGO_PASSWORD'] = generate_secret(32)
    creds['INFISICAL_REDIS_PASSWORD'] = generate_secret(32)
    creds['INFISICAL_SITE_URL'] = "http://localhost:9001"
    creds['INFISICAL_TELEMETRY_ENABLED'] = "false"
    print_success("Infisical secrets generated")

    # Production domain configuration
    if creds['ENVIRONMENT'] == "public":
        print("\n")
        print_info("Production Domain Configuration")
        if prompt_yes_no("Configure custom domains?", default=False):
            creds['N8N_HOSTNAME'] = prompt_input("n8n domain (e.g., n8n.yourdomain.com)", validator=validate_domain)
            creds['WEBUI_HOSTNAME'] = prompt_input("Open WebUI domain", validator=validate_domain)
            creds['FLOWISE_HOSTNAME'] = prompt_input("Flowise domain", validator=validate_domain)
            creds['SUPABASE_HOSTNAME'] = prompt_input("Supabase domain", validator=validate_domain)
            creds['LANGFUSE_HOSTNAME'] = prompt_input("Langfuse domain", validator=validate_domain)
            creds['NEO4J_HOSTNAME'] = prompt_input("Neo4j domain", validator=validate_domain)
            creds['GITEA_HOSTNAME'] = prompt_input("Gitea domain", validator=validate_domain)
            creds['INFISICAL_HOSTNAME'] = prompt_input("Infisical domain", validator=validate_domain)
            creds['LETSENCRYPT_EMAIL'] = prompt_input("Let's Encrypt email", validator=validate_email)

    # Additional optional settings
    creds['POSTGRES_HOST'] = "db"
    creds['POSTGRES_DB'] = "postgres"
    creds['POSTGRES_PORT'] = "5432"
    creds['POSTGRES_USER'] = "postgres"

    return creds


def write_env_file(creds: Dict[str, str], output_path: str = ".env"):
    """Write credentials to .env file"""
    print_header("Writing Configuration")

    env_content = f"""# Generated by bootstrap.py
# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Hardware Profile: {creds.get('HARDWARE_PROFILE', 'cpu')}
# Environment: {creds.get('ENVIRONMENT', 'private')}

############
# n8n credentials
############
N8N_ENCRYPTION_KEY={creds['N8N_ENCRYPTION_KEY']}
N8N_USER_MANAGEMENT_JWT_SECRET={creds['N8N_USER_MANAGEMENT_JWT_SECRET']}

############
# Supabase Secrets
############
POSTGRES_PASSWORD={creds['POSTGRES_PASSWORD']}
JWT_SECRET={creds['JWT_SECRET']}
ANON_KEY={creds['ANON_KEY']}
SERVICE_ROLE_KEY={creds['SERVICE_ROLE_KEY']}
DASHBOARD_USERNAME={creds['DASHBOARD_USERNAME']}
DASHBOARD_PASSWORD={creds['DASHBOARD_PASSWORD']}
POOLER_TENANT_ID={creds['POOLER_TENANT_ID']}

############
# Neo4j credentials
############
NEO4J_AUTH={creds['NEO4J_AUTH']}

############
# Langfuse credentials
############
CLICKHOUSE_PASSWORD={creds['CLICKHOUSE_PASSWORD']}
MINIO_ROOT_PASSWORD={creds['MINIO_ROOT_PASSWORD']}
LANGFUSE_SALT={creds['LANGFUSE_SALT']}
NEXTAUTH_SECRET={creds['NEXTAUTH_SECRET']}
ENCRYPTION_KEY={creds['ENCRYPTION_KEY']}

############
# Gitea credentials
############
GITEA_SECRET_KEY={creds['GITEA_SECRET_KEY']}
GITEA_INTERNAL_TOKEN={creds['GITEA_INTERNAL_TOKEN']}
GITEA_ADMIN_USER={creds['GITEA_ADMIN_USER']}
GITEA_ADMIN_PASSWORD={creds['GITEA_ADMIN_PASSWORD']}
GITEA_ADMIN_EMAIL={creds['GITEA_ADMIN_EMAIL']}
GITEA_DISABLE_REGISTRATION={creds['GITEA_DISABLE_REGISTRATION']}

############
# Infisical credentials
############
INFISICAL_ENCRYPTION_KEY={creds['INFISICAL_ENCRYPTION_KEY']}
INFISICAL_JWT_SECRET={creds['INFISICAL_JWT_SECRET']}
INFISICAL_MONGO_USER={creds['INFISICAL_MONGO_USER']}
INFISICAL_MONGO_PASSWORD={creds['INFISICAL_MONGO_PASSWORD']}
INFISICAL_REDIS_PASSWORD={creds['INFISICAL_REDIS_PASSWORD']}
INFISICAL_SITE_URL={creds['INFISICAL_SITE_URL']}
INFISICAL_TELEMETRY_ENABLED={creds['INFISICAL_TELEMETRY_ENABLED']}

############
# Database Configuration
############
POSTGRES_HOST={creds['POSTGRES_HOST']}
POSTGRES_DB={creds['POSTGRES_DB']}
POSTGRES_PORT={creds['POSTGRES_PORT']}
POSTGRES_USER={creds['POSTGRES_USER']}

############
# Supavisor -- Database pooler
############
POOLER_PROXY_PORT_TRANSACTION=6543
POOLER_DEFAULT_POOL_SIZE=20
POOLER_MAX_CLIENT_CONN=100
SECRET_KEY_BASE=UpNVntn3cDxHJpq99YMc1T1AQgQpc8kfYTuRgBiYa15BLrx8etQoXz3gZv1/u2oq
VAULT_ENC_KEY=your-32-character-encryption-key

############
# API Proxy - Configuration for the Kong Reverse proxy
############
KONG_HTTP_PORT=8000
KONG_HTTPS_PORT=8443

############
# API - Configuration for PostgREST
############
PGRST_DB_SCHEMAS=public,storage,graphql_public

############
# Auth - Configuration for the GoTrue authentication server
############
SITE_URL=http://localhost:3000
ADDITIONAL_REDIRECT_URLS=
JWT_EXPIRY=3600
DISABLE_SIGNUP=false
API_EXTERNAL_URL=http://localhost:8000

## Mailer Config
MAILER_URLPATHS_CONFIRMATION="/auth/v1/verify"
MAILER_URLPATHS_INVITE="/auth/v1/verify"
MAILER_URLPATHS_RECOVERY="/auth/v1/verify"
MAILER_URLPATHS_EMAIL_CHANGE="/auth/v1/verify"

## Email auth
ENABLE_EMAIL_SIGNUP=true
ENABLE_EMAIL_AUTOCONFIRM=true
SMTP_ADMIN_EMAIL=admin@example.com
SMTP_HOST=supabase-mail
SMTP_PORT=2500
SMTP_USER=fake_mail_user
SMTP_PASS=fake_mail_password
SMTP_SENDER_NAME=fake_sender
ENABLE_ANONYMOUS_USERS=false

## Phone auth
ENABLE_PHONE_SIGNUP=true
ENABLE_PHONE_AUTOCONFIRM=true

############
# Studio - Configuration for the Dashboard
############
STUDIO_DEFAULT_ORGANIZATION=Default Organization
STUDIO_DEFAULT_PROJECT=Default Project
STUDIO_PORT=3000
SUPABASE_PUBLIC_URL=http://localhost:8000
IMGPROXY_ENABLE_WEBP_DETECTION=true

############
# Functions - Configuration for Functions
############
FUNCTIONS_VERIFY_JWT=false

############
# Logs - Configuration for Analytics
############
LOGFLARE_PUBLIC_ACCESS_TOKEN=your-super-secret-and-long-logflare-key-public
LOGFLARE_PRIVATE_ACCESS_TOKEN=your-super-secret-and-long-logflare-key-private
DOCKER_SOCKET_LOCATION=/var/run/docker.sock
"""

    # Add production domains if configured
    if creds['ENVIRONMENT'] == "public" and 'N8N_HOSTNAME' in creds:
        env_content += f"""
############
# Production Domains
############
N8N_HOSTNAME={creds.get('N8N_HOSTNAME', '')}
WEBUI_HOSTNAME={creds.get('WEBUI_HOSTNAME', '')}
FLOWISE_HOSTNAME={creds.get('FLOWISE_HOSTNAME', '')}
SUPABASE_HOSTNAME={creds.get('SUPABASE_HOSTNAME', '')}
LANGFUSE_HOSTNAME={creds.get('LANGFUSE_HOSTNAME', '')}
NEO4J_HOSTNAME={creds.get('NEO4J_HOSTNAME', '')}
GITEA_HOSTNAME={creds.get('GITEA_HOSTNAME', '')}
INFISICAL_HOSTNAME={creds.get('INFISICAL_HOSTNAME', '')}
LETSENCRYPT_EMAIL={creds.get('LETSENCRYPT_EMAIL', '')}
"""

    with open(output_path, 'w') as f:
        f.write(env_content)

    print_success(f"Configuration written to {output_path}")

    # Save metadata
    metadata = {
        'hardware_profile': creds.get('HARDWARE_PROFILE', 'cpu'),
        'environment': creds.get('ENVIRONMENT', 'private'),
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    with open('.bootstrap_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata


def main():
    """Main bootstrap process"""
    parser = argparse.ArgumentParser(description='Bootstrap Local AI Package')
    parser.add_argument('--skip-checks', action='store_true', help='Skip prerequisite checks')
    parser.add_argument('--output', default='.env', help='Output file path (default: .env)')
    args = parser.parse_args()

    print_header("Local AI Package - Self-Bootstrapping Wizard")

    # Check prerequisites
    if not args.skip_checks:
        prereqs_ok, missing = check_prerequisites()
        if not prereqs_ok:
            print_error(f"Missing required tools: {', '.join(missing)}")
            print_info("Please install missing tools and try again")
            sys.exit(1)

    # Check if .env already exists
    if os.path.exists(args.output):
        print_warning(f"{args.output} already exists")
        if not prompt_yes_no("Overwrite existing configuration?", default=False):
            print_info("Bootstrap cancelled")
            sys.exit(0)

    # Collect credentials
    creds = collect_credentials()

    # Write .env file
    metadata = write_env_file(creds, args.output)

    # Summary
    print_header("Bootstrap Complete!")
    print_success(f"Hardware Profile: {metadata['hardware_profile']}")
    print_success(f"Environment: {metadata['environment']}")
    print_success(f"Configuration saved to: {args.output}")

    print("\n")
    print_info("Next steps:")
    print(f"  1. Review your configuration: cat {args.output}")
    print(f"  2. Start services: python start_services.py --profile {metadata['hardware_profile']} --environment {metadata['environment']}")
    print(f"  3. (Optional) Encrypt secrets: sops --encrypt {args.output} > {args.output}.enc")
    print(f"  4. Access services at:")
    print(f"     - n8n: http://localhost:5678")
    print(f"     - Open WebUI: http://localhost:8080")
    print(f"     - Gitea: http://localhost:9000")
    print(f"     - Infisical: http://localhost:9001")
    print(f"     - Langfuse: http://localhost:3000")


if __name__ == "__main__":
    main()
