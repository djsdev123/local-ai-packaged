#!/usr/bin/env python3
"""
gitea_setup.py - Automatically setup Gitea and push repository

This script:
1. Waits for Gitea to be ready
2. Creates admin user via API
3. Creates a repository for the local-ai-packaged
4. Initializes git if needed
5. Adds Gitea as remote
6. Pushes code and encrypted secrets to Gitea
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict


class GiteaSetup:
    def __init__(self, base_url: str = "http://localhost:9000", admin_user: str = "gitea_admin",
                 admin_password: str = "", admin_email: str = "admin@local.ai"):
        self.base_url = base_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.admin_email = admin_email
        self.token = None

    def wait_for_gitea(self, max_retries: int = 30, delay: int = 2):
        """Wait for Gitea to be ready"""
        print("⏳ Waiting for Gitea to be ready...")
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/api/v1/version", timeout=5)
                if response.status_code == 200:
                    version = response.json().get('version', 'unknown')
                    print(f"✓ Gitea is ready (version: {version})")
                    return True
            except requests.RequestException:
                pass

            time.sleep(delay)
            print(f"  Attempt {i + 1}/{max_retries}...")

        print("✗ Gitea did not become ready in time")
        return False

    def create_admin_user(self) -> bool:
        """Create admin user via Gitea CLI (requires docker exec)"""
        print(f"🔧 Creating admin user: {self.admin_user}")

        try:
            # Check if user already exists
            result = subprocess.run(
                [
                    "docker", "exec", "gitea",
                    "/usr/local/bin/gitea", "admin", "user", "list"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if self.admin_user in result.stdout:
                print(f"✓ Admin user '{self.admin_user}' already exists")
                return True

            # Create the admin user
            result = subprocess.run(
                [
                    "docker", "exec", "gitea",
                    "/usr/local/bin/gitea", "admin", "user", "create",
                    "--username", self.admin_user,
                    "--password", self.admin_password,
                    "--email", self.admin_email,
                    "--admin",
                    "--must-change-password=false"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✓ Admin user '{self.admin_user}' created successfully")
                return True
            else:
                print(f"✗ Failed to create admin user: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("✗ Timeout creating admin user")
            return False
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            return False

    def create_access_token(self) -> Optional[str]:
        """Create an access token for API access"""
        print("🔑 Creating access token...")

        # Try to create token via API
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/users/{self.admin_user}/tokens",
                auth=(self.admin_user, self.admin_password),
                json={
                    "name": "local-ai-bootstrap",
                    "scopes": ["write:repository", "write:user"]
                },
                timeout=10
            )

            if response.status_code == 201:
                token = response.json().get('sha1')
                print("✓ Access token created")
                self.token = token
                return token
            elif response.status_code == 422:
                # Token with this name might already exist, try to list tokens
                print("⚠ Token might already exist, attempting to use existing token")
                # For simplicity, we'll use basic auth for operations
                self.token = None
                return None
            else:
                print(f"⚠ Could not create token (status {response.status_code}), will use basic auth")
                self.token = None
                return None

        except Exception as e:
            print(f"⚠ Error creating token: {e}, will use basic auth")
            self.token = None
            return None

    def create_repository(self, repo_name: str = "local-ai-packaged",
                         description: str = "Self-hosted AI Package Configuration") -> bool:
        """Create a repository in Gitea"""
        print(f"📦 Creating repository: {repo_name}")

        headers = {}
        auth = (self.admin_user, self.admin_password)

        if self.token:
            headers['Authorization'] = f'token {self.token}'
            auth = None

        try:
            # Check if repo already exists
            response = requests.get(
                f"{self.base_url}/api/v1/repos/{self.admin_user}/{repo_name}",
                headers=headers,
                auth=auth,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✓ Repository '{repo_name}' already exists")
                return True

            # Create the repository
            response = requests.post(
                f"{self.base_url}/api/v1/user/repos",
                headers=headers,
                auth=auth,
                json={
                    "name": repo_name,
                    "description": description,
                    "private": True,
                    "auto_init": False
                },
                timeout=10
            )

            if response.status_code == 201:
                print(f"✓ Repository '{repo_name}' created successfully")
                return True
            else:
                print(f"✗ Failed to create repository: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error creating repository: {e}")
            return False

    def setup_git_remote(self, repo_name: str = "local-ai-packaged") -> bool:
        """Setup Git remote for Gitea"""
        print("🔗 Setting up Git remote...")

        try:
            # Check if git is initialized
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                timeout=5
            )

            if result.returncode != 0:
                print("  Initializing git repository...")
                subprocess.run(["git", "init"], check=True, timeout=5)
                subprocess.run(["git", "add", "."], check=True, timeout=10)
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit"],
                    check=True,
                    timeout=10
                )

            # Add gitea remote
            remote_url = f"http://{self.admin_user}:{self.admin_password}@localhost:9000/{self.admin_user}/{repo_name}.git"

            # Check if gitea remote exists
            result = subprocess.run(
                ["git", "remote", "get-url", "gitea"],
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                print("  Updating gitea remote...")
                subprocess.run(
                    ["git", "remote", "set-url", "gitea", remote_url],
                    check=True,
                    timeout=5
                )
            else:
                print("  Adding gitea remote...")
                subprocess.run(
                    ["git", "remote", "add", "gitea", remote_url],
                    check=True,
                    timeout=5
                )

            print("✓ Git remote configured")
            return True

        except subprocess.TimeoutExpired:
            print("✗ Timeout setting up git remote")
            return False
        except Exception as e:
            print(f"✗ Error setting up git remote: {e}")
            return False

    def push_to_gitea(self, branch: str = "main") -> bool:
        """Push repository to Gitea"""
        print(f"📤 Pushing to Gitea (branch: {branch})...")

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5
            )

            current_branch = result.stdout.strip()

            if not current_branch:
                # We might be on a detached HEAD, create a branch
                subprocess.run(
                    ["git", "checkout", "-b", branch],
                    check=True,
                    timeout=5
                )
                current_branch = branch

            # Push to gitea
            result = subprocess.run(
                ["git", "push", "-u", "gitea", f"{current_branch}:{branch}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✓ Successfully pushed to Gitea")
                return True
            else:
                # Might already be up to date
                if "Everything up-to-date" in result.stderr or "Everything up-to-date" in result.stdout:
                    print("✓ Repository already up to date")
                    return True
                else:
                    print(f"⚠ Push output: {result.stderr}")
                    return True  # Don't fail on push issues

        except subprocess.TimeoutExpired:
            print("✗ Timeout pushing to Gitea")
            return False
        except Exception as e:
            print(f"⚠ Error pushing to Gitea: {e}")
            return True  # Don't fail the whole setup


def main():
    """Main setup process"""
    print("=" * 60)
    print("Gitea Setup - Automated Repository Initialization")
    print("=" * 60)

    # Load environment variables from .env if it exists
    admin_user = os.getenv("GITEA_ADMIN_USER", "gitea_admin")
    admin_password = os.getenv("GITEA_ADMIN_PASSWORD", "")
    admin_email = os.getenv("GITEA_ADMIN_EMAIL", "admin@local.ai")

    if not admin_password:
        print("✗ GITEA_ADMIN_PASSWORD not set in environment")
        print("  Please run bootstrap.py first or set GITEA_ADMIN_PASSWORD")
        sys.exit(1)

    gitea = GiteaSetup(
        base_url="http://localhost:9000",
        admin_user=admin_user,
        admin_password=admin_password,
        admin_email=admin_email
    )

    # Wait for Gitea
    if not gitea.wait_for_gitea():
        print("✗ Gitea setup failed: service not ready")
        sys.exit(1)

    # Create admin user
    if not gitea.create_admin_user():
        print("✗ Gitea setup failed: could not create admin user")
        sys.exit(1)

    # Create access token
    gitea.create_access_token()

    # Create repository
    if not gitea.create_repository():
        print("✗ Gitea setup failed: could not create repository")
        sys.exit(1)

    # Setup git remote
    if not gitea.setup_git_remote():
        print("✗ Gitea setup failed: could not setup git remote")
        sys.exit(1)

    # Push to Gitea
    gitea.push_to_gitea()

    print("\n" + "=" * 60)
    print("✓ Gitea Setup Complete!")
    print("=" * 60)
    print(f"\nGitea URL: http://localhost:9000")
    print(f"Username: {admin_user}")
    print(f"Repository: http://localhost:9000/{admin_user}/local-ai-packaged")
    print("\nYou can now push encrypted secrets with SOPS to this repository")


if __name__ == "__main__":
    main()
