#!/usr/bin/env python3
"""
infisical_sync.py - Sync secrets with Infisical

This script:
1. Waits for Infisical to be ready
2. Creates a project in Infisical
3. Syncs secrets from .env to Infisical
4. Provides commands to pull secrets from Infisical
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, Optional


class InfisicalSync:
    def __init__(self, base_url: str = "http://localhost:9001"):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.project_id = None

    def wait_for_infisical(self, max_retries: int = 30, delay: int = 2) -> bool:
        """Wait for Infisical to be ready"""
        print("⏳ Waiting for Infisical to be ready...")

        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/api/status", timeout=5)
                if response.status_code == 200:
                    print("✓ Infisical is ready")
                    return True
            except requests.RequestException:
                pass

            time.sleep(delay)
            if (i + 1) % 5 == 0:
                print(f"  Still waiting... ({i + 1}/{max_retries})")

        print("✗ Infisical did not become ready in time")
        return False

    def setup_instructions(self):
        """Print setup instructions for Infisical"""
        print("\n" + "=" * 60)
        print("📚 Infisical Setup Instructions")
        print("=" * 60)
        print("\nInfisical is running at: http://localhost:9001")
        print("\n1. Open http://localhost:9001 in your browser")
        print("2. Create an admin account")
        print("3. Create a new organization")
        print("4. Create a new project (e.g., 'local-ai-packaged')")
        print("5. Go to Project Settings → Service Tokens")
        print("6. Create a service token with read/write access")
        print("7. Save the token and use it with this script:")
        print("\n   export INFISICAL_TOKEN=<your-token>")
        print("   python scripts/infisical_sync.py --push")
        print("\n" + "=" * 60)

    def read_env_file(self, env_file: str = ".env") -> Dict[str, str]:
        """Read .env file and parse key-value pairs"""
        print(f"📖 Reading {env_file}...")

        env_path = Path(env_file)
        if not env_path.exists():
            print(f"✗ {env_file} not found")
            return {}

        secrets = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Skip placeholder values
                    if value and not value.startswith('generate-') and not value.startswith('your-'):
                        secrets[key] = value

        print(f"✓ Found {len(secrets)} secrets in {env_file}")
        return secrets

    def push_to_infisical_cli(self, env_file: str = ".env", environment: str = "dev") -> bool:
        """Push secrets to Infisical using CLI"""
        print(f"\n📤 Pushing secrets to Infisical (environment: {environment})...")

        # Check if infisical CLI is installed
        try:
            result = subprocess.run(
                ["infisical", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                print("⚠ Infisical CLI not installed")
                print("  Install with: brew install infisical/get-cli/infisical")
                return False
        except FileNotFoundError:
            print("⚠ Infisical CLI not installed")
            print("  Install from: https://infisical.com/docs/cli/overview")
            return False

        # Try to push secrets
        try:
            result = subprocess.run(
                ["infisical", "secrets", "set", "--env", environment, f"--from-file={env_file}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✓ Secrets pushed to Infisical")
                return True
            else:
                print(f"✗ Failed to push secrets: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ Error pushing secrets: {e}")
            return False


def main():
    """Main sync process"""
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description='Sync secrets with Infisical')
    parser.add_argument('--push', action='store_true', help='Push secrets from .env to Infisical')
    parser.add_argument('--pull', action='store_true', help='Pull secrets from Infisical to .env')
    parser.add_argument('--env-file', default='.env', help='Path to .env file')
    parser.add_argument('--environment', default='dev', help='Infisical environment (dev, staging, prod)')
    args = parser.parse_args()

    print("=" * 60)
    print("Infisical Secret Management")
    print("=" * 60)

    infisical = InfisicalSync()

    # Wait for Infisical to be ready
    if not infisical.wait_for_infisical():
        print("\n⚠ Infisical is not ready. Make sure it's running:")
        print("  docker ps | grep infisical")
        sys.exit(1)

    if args.push:
        # Read secrets from .env
        secrets = infisical.read_env_file(args.env_file)
        if not secrets:
            print("✗ No secrets found to push")
            sys.exit(1)

        # Try to push with CLI
        if not infisical.push_to_infisical_cli(args.env_file, args.environment):
            print("\n⚠ Could not push secrets automatically")
            infisical.setup_instructions()

    elif args.pull:
        print("\n📥 Pulling secrets from Infisical...")
        print("\nUse the Infisical CLI to pull secrets:")
        print(f"  infisical secrets pull --env {args.environment} > {args.env_file}")
        print("\nOr use the Infisical dashboard to manage secrets:")
        print("  http://localhost:9001")

    else:
        # Just show setup instructions
        infisical.setup_instructions()

    print("\n" + "=" * 60)
    print("💡 Infisical Tips")
    print("=" * 60)
    print("\n• Use Infisical to manage secrets across environments")
    print("• Service tokens allow automated access in CI/CD")
    print("• Secrets are encrypted at rest and in transit")
    print("• Audit logs track all secret access and changes")
    print("\nFor more info: https://infisical.com/docs")


if __name__ == "__main__":
    main()
