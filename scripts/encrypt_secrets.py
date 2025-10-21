#!/usr/bin/env python3
"""
encrypt_secrets.py - Encrypt secrets with SOPS and push to Gitea

This script:
1. Checks if SOPS and Age are installed
2. Generates Age key if needed
3. Updates .sops.yaml with the Age public key
4. Encrypts .env file with SOPS
5. Commits encrypted file to git
6. Pushes to Gitea
"""

import os
import sys
import subprocess
import re
from pathlib import Path


def check_sops_age_installed() -> bool:
    """Check if SOPS and Age are installed"""
    print("🔍 Checking for SOPS and Age...")

    sops_installed = False
    age_installed = False

    try:
        result = subprocess.run(["sops", "--version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✓ SOPS is installed")
            sops_installed = True
    except FileNotFoundError:
        print("✗ SOPS is not installed")

    try:
        result = subprocess.run(["age", "--version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✓ Age is installed")
            age_installed = True
    except FileNotFoundError:
        print("✗ Age is not installed")

    if not sops_installed or not age_installed:
        print("\n⚠ Missing required tools. Please install:")
        if not sops_installed:
            print("  SOPS: https://github.com/getsops/sops")
            print("    - macOS: brew install sops")
            print("    - Linux: Download from releases")
        if not age_installed:
            print("  Age: https://github.com/FiloSottile/age")
            print("    - macOS: brew install age")
            print("    - Linux: sudo apt install age")
        return False

    return True


def generate_age_key() -> tuple[str, str]:
    """Generate Age key pair"""
    print("\n🔑 Generating Age encryption key...")

    # Create age directory if it doesn't exist
    age_dir = Path.home() / ".config" / "sops" / "age"
    age_dir.mkdir(parents=True, exist_ok=True)

    key_file = age_dir / "keys.txt"

    # Check if key already exists
    if key_file.exists():
        print(f"✓ Age key already exists at {key_file}")

        # Read the existing key
        with open(key_file, 'r') as f:
            content = f.read()

        # Extract public key
        public_key_match = re.search(r'# public key: (age1[a-z0-9]+)', content)
        if public_key_match:
            public_key = public_key_match.group(1)
            print(f"  Public key: {public_key}")
            return str(key_file), public_key
        else:
            print("⚠ Could not find public key in existing key file")

    # Generate new key
    try:
        result = subprocess.run(
            ["age-keygen", "-o", str(key_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"✓ Age key generated and saved to {key_file}")

            # Extract public key from output
            public_key_match = re.search(r'Public key: (age1[a-z0-9]+)', result.stdout)
            if public_key_match:
                public_key = public_key_match.group(1)
                print(f"  Public key: {public_key}")
                return str(key_file), public_key
            else:
                print("⚠ Could not extract public key from age-keygen output")
                return str(key_file), ""
        else:
            print(f"✗ Failed to generate Age key: {result.stderr}")
            return "", ""

    except Exception as e:
        print(f"✗ Error generating Age key: {e}")
        return "", ""


def update_sops_config(public_key: str) -> bool:
    """Update .sops.yaml with the Age public key"""
    print("\n📝 Updating .sops.yaml configuration...")

    sops_config = Path(".sops.yaml")

    if not sops_config.exists():
        print("✗ .sops.yaml not found")
        return False

    try:
        with open(sops_config, 'r') as f:
            content = f.read()

        # Replace placeholder with actual public key
        updated_content = re.sub(
            r'age1x+',
            public_key,
            content
        )

        with open(sops_config, 'w') as f:
            f.write(updated_content)

        print("✓ .sops.yaml updated with Age public key")
        return True

    except Exception as e:
        print(f"✗ Error updating .sops.yaml: {e}")
        return False


def encrypt_env_file(env_file: str = ".env") -> bool:
    """Encrypt .env file with SOPS"""
    print(f"\n🔐 Encrypting {env_file}...")

    env_path = Path(env_file)
    encrypted_path = Path(f"{env_file}.enc")

    if not env_path.exists():
        print(f"✗ {env_file} not found")
        return False

    # Set SOPS_AGE_KEY_FILE environment variable
    age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"
    env = os.environ.copy()
    env['SOPS_AGE_KEY_FILE'] = str(age_key_file)

    try:
        # Encrypt with SOPS
        result = subprocess.run(
            ["sops", "--encrypt", str(env_path)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )

        if result.returncode == 0:
            # Write encrypted content
            with open(encrypted_path, 'w') as f:
                f.write(result.stdout)

            print(f"✓ {env_file} encrypted to {encrypted_path}")
            return True
        else:
            print(f"✗ SOPS encryption failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error encrypting file: {e}")
        return False


def update_gitignore() -> bool:
    """Update .gitignore to exclude .env but allow .env.enc"""
    print("\n📄 Updating .gitignore...")

    gitignore = Path(".gitignore")

    # Read existing .gitignore
    existing_content = ""
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            existing_content = f.read()

    # Check if .env is already ignored
    if ".env" not in existing_content:
        with open(gitignore, 'a') as f:
            f.write("\n# Environment files (unencrypted)\n")
            f.write(".env\n")
            f.write(".env.local\n")
            f.write(".env.*.local\n")
            f.write("\n# Allow encrypted environment files\n")
            f.write("!.env.enc\n")
            f.write("!.env.*.enc\n")

        print("✓ .gitignore updated")
    else:
        print("✓ .gitignore already configured")

    return True


def commit_and_push_encrypted() -> bool:
    """Commit encrypted file and push to Gitea"""
    print("\n📤 Committing and pushing encrypted secrets...")

    try:
        # Add encrypted file
        subprocess.run(
            ["git", "add", ".env.enc", ".sops.yaml", ".gitignore"],
            check=True,
            timeout=5
        )

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", "Add encrypted environment configuration with SOPS"],
            capture_output=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✓ Changes committed")
        elif "nothing to commit" in result.stdout.decode() or "nothing to commit" in result.stderr.decode():
            print("✓ No changes to commit (already up to date)")
        else:
            print(f"⚠ Commit result: {result.stderr.decode()}")

        # Push to gitea remote if it exists
        result = subprocess.run(
            ["git", "remote", "get-url", "gitea"],
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            print("  Pushing to Gitea...")
            result = subprocess.run(
                ["git", "push", "gitea"],
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✓ Successfully pushed to Gitea")
            else:
                print(f"⚠ Push result: {result.stderr.decode()}")
        else:
            print("⚠ Gitea remote not configured, skipping push")

        return True

    except Exception as e:
        print(f"⚠ Error committing/pushing: {e}")
        return True  # Don't fail the whole process


def decrypt_instructions():
    """Print instructions for decrypting"""
    print("\n" + "=" * 60)
    print("📚 Decryption Instructions")
    print("=" * 60)
    print("\nTo decrypt the .env file on another machine:")
    print("\n1. Install SOPS and Age:")
    print("   brew install sops age  # macOS")
    print("   sudo apt install sops age  # Linux")
    print("\n2. Copy your Age private key to the new machine:")
    print(f"   Key location: {Path.home()}/.config/sops/age/keys.txt")
    print("\n3. Decrypt the file:")
    print("   export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt")
    print("   sops --decrypt .env.enc > .env")
    print("\n4. Or edit encrypted file in place:")
    print("   sops .env.enc")
    print("\n⚠ Important: Keep your Age private key secure and backed up!")
    print("  If you lose it, you won't be able to decrypt your secrets.")


def main():
    """Main encryption process"""
    print("=" * 60)
    print("SOPS Encryption Setup")
    print("=" * 60)

    # Check prerequisites
    if not check_sops_age_installed():
        sys.exit(1)

    # Generate or load Age key
    key_file, public_key = generate_age_key()
    if not public_key:
        print("✗ Failed to generate or load Age key")
        sys.exit(1)

    # Update SOPS config
    if not update_sops_config(public_key):
        print("✗ Failed to update SOPS configuration")
        sys.exit(1)

    # Encrypt .env file
    if not encrypt_env_file(".env"):
        print("✗ Failed to encrypt .env file")
        sys.exit(1)

    # Update .gitignore
    update_gitignore()

    # Commit and push
    commit_and_push_encrypted()

    # Print decryption instructions
    decrypt_instructions()

    print("\n" + "=" * 60)
    print("✓ Encryption Setup Complete!")
    print("=" * 60)
    print(f"\n✓ Encrypted file: .env.enc")
    print(f"✓ Age key location: {key_file}")
    print(f"✓ SOPS config: .sops.yaml")


if __name__ == "__main__":
    main()
