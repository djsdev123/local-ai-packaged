#!/usr/bin/env python3
"""
localai_cli.py - Complete CLI for Local AI Package Management

Commands:
- export: Export complete environment (configs, volumes, secrets)
- import: Import and restore environment from backup
- encrypt: Encrypt secrets with SOPS
- decrypt: Decrypt secrets from SOPS
- setup-gitea: Initialize Gitea and create repository
- sync-infisical: Sync secrets with Infisical
- validate: Validate environment configuration
"""

import os
import sys
import json
import subprocess
import tarfile
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class LocalAICLI:
    def __init__(self):
        self.project_name = "localai"
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'=' * 60}")
        print(f"{text.center(60)}")
        print(f"{'=' * 60}\n")

    def run_command(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command and return result"""
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)

    def get_running_containers(self) -> List[str]:
        """Get list of running containers for this project"""
        result = self.run_command([
            "docker", "ps",
            "--filter", f"name={self.project_name}",
            "--format", "{{.Names}}"
        ])

        if result.returncode == 0:
            return [name for name in result.stdout.strip().split('\n') if name]
        return []

    def get_docker_volumes(self) -> List[str]:
        """Get list of Docker volumes for this project"""
        result = self.run_command([
            "docker", "volume", "ls",
            "--filter", f"name={self.project_name}",
            "--format", "{{.Name}}"
        ])

        if result.returncode == 0:
            return [name for name in result.stdout.strip().split('\n') if name]
        return []

    def export_docker_volume(self, volume_name: str, output_dir: Path) -> bool:
        """Export a Docker volume to a tar file"""
        print(f"  Exporting volume: {volume_name}")

        output_file = output_dir / f"{volume_name}.tar"

        # Create a temporary container to export the volume
        result = self.run_command([
            "docker", "run", "--rm",
            "-v", f"{volume_name}:/volume",
            "-v", f"{output_dir.absolute()}:/backup",
            "alpine",
            "tar", "czf", f"/backup/{volume_name}.tar.gz", "-C", "/volume", "."
        ], timeout=300)

        if result.returncode == 0:
            print(f"    ✓ Exported to {volume_name}.tar.gz")
            return True
        else:
            print(f"    ✗ Failed to export: {result.stderr}")
            return False

    def import_docker_volume(self, volume_name: str, backup_file: Path) -> bool:
        """Import a Docker volume from a tar file"""
        print(f"  Importing volume: {volume_name}")

        # Create the volume if it doesn't exist
        self.run_command(["docker", "volume", "create", volume_name])

        # Import the data
        backup_dir = backup_file.parent

        result = self.run_command([
            "docker", "run", "--rm",
            "-v", f"{volume_name}:/volume",
            "-v", f"{backup_dir.absolute()}:/backup",
            "alpine",
            "tar", "xzf", f"/backup/{backup_file.name}", "-C", "/volume"
        ], timeout=300)

        if result.returncode == 0:
            print(f"    ✓ Imported {backup_file.name}")
            return True
        else:
            print(f"    ✗ Failed to import: {result.stderr}")
            return False

    def export_environment(self, output_name: str = None, format: str = "full") -> Path:
        """Export complete environment"""
        self.print_header("Exporting Local AI Package")

        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"localai_backup_{timestamp}"

        export_dir = self.backup_dir / output_name
        export_dir.mkdir(exist_ok=True)

        # Export metadata
        print("📋 Collecting metadata...")
        metadata = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "format": format,
            "containers": self.get_running_containers(),
            "volumes": self.get_docker_volumes(),
        }

        # Load bootstrap metadata if exists
        if Path(".bootstrap_metadata.json").exists():
            with open(".bootstrap_metadata.json", 'r') as f:
                bootstrap_meta = json.load(f)
                metadata.update(bootstrap_meta)

        with open(export_dir / "manifest.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print("✓ Metadata saved")

        # Export configuration files
        print("\n📄 Exporting configuration files...")
        config_files = [
            ".env",
            ".env.enc",
            ".sops.yaml",
            "docker-compose.yml",
            "docker-compose.override.private.yml",
            "docker-compose.override.public.yml",
            "Caddyfile",
            ".bootstrap_metadata.json"
        ]

        config_dir = export_dir / "configs"
        config_dir.mkdir(exist_ok=True)

        for config_file in config_files:
            if Path(config_file).exists():
                subprocess.run(["cp", config_file, str(config_dir)])
                print(f"  ✓ {config_file}")

        # Export custom configurations
        if Path("searxng/settings.yml").exists():
            searxng_dir = config_dir / "searxng"
            searxng_dir.mkdir(exist_ok=True)
            subprocess.run(["cp", "searxng/settings.yml", str(searxng_dir)])
            print("  ✓ searxng/settings.yml")

        # Export Docker volumes (if full backup)
        if format == "full":
            print("\n💾 Exporting Docker volumes...")
            volumes_dir = export_dir / "volumes"
            volumes_dir.mkdir(exist_ok=True)

            volumes = self.get_docker_volumes()
            for volume in volumes:
                self.export_docker_volume(volume, volumes_dir)

        # Create tarball
        print("\n📦 Creating backup archive...")
        archive_path = self.backup_dir / f"{output_name}.tar.gz"

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(export_dir, arcname=output_name)

        # Calculate checksum
        print("🔐 Calculating checksum...")
        sha256 = hashlib.sha256()
        with open(archive_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

        checksum = sha256.hexdigest()
        with open(f"{archive_path}.sha256", 'w') as f:
            f.write(f"{checksum}  {archive_path.name}\n")

        # Cleanup temporary directory
        subprocess.run(["rm", "-rf", str(export_dir)])

        # Summary
        archive_size = archive_path.stat().st_size / (1024 * 1024)  # MB
        print("\n✓ Export Complete!")
        print(f"\n📦 Archive: {archive_path}")
        print(f"📊 Size: {archive_size:.2f} MB")
        print(f"🔐 SHA256: {checksum}")

        return archive_path

    def import_environment(self, backup_file: str, skip_volumes: bool = False) -> bool:
        """Import and restore environment from backup"""
        self.print_header("Importing Local AI Package")

        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"✗ Backup file not found: {backup_file}")
            return False

        # Verify checksum if exists
        checksum_file = Path(f"{backup_file}.sha256")
        if checksum_file.exists():
            print("🔐 Verifying checksum...")
            with open(checksum_file, 'r') as f:
                expected_checksum = f.read().split()[0]

            sha256 = hashlib.sha256()
            with open(backup_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)

            if sha256.hexdigest() == expected_checksum:
                print("✓ Checksum verified")
            else:
                print("✗ Checksum mismatch! File may be corrupted.")
                return False

        # Extract archive
        print("\n📦 Extracting backup archive...")
        extract_dir = self.backup_dir / "restore_temp"
        extract_dir.mkdir(exist_ok=True)

        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(extract_dir)

        # Find the backup directory (should be the only subdirectory)
        backup_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if not backup_dirs:
            print("✗ Invalid backup structure")
            return False

        restore_dir = backup_dirs[0]

        # Read manifest
        manifest_file = restore_dir / "manifest.json"
        if not manifest_file.exists():
            print("✗ Manifest not found in backup")
            return False

        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        print(f"\n📋 Backup Info:")
        print(f"  Created: {manifest.get('timestamp', 'unknown')}")
        print(f"  Format: {manifest.get('format', 'unknown')}")
        print(f"  Profile: {manifest.get('hardware_profile', 'unknown')}")
        print(f"  Environment: {manifest.get('environment', 'unknown')}")

        # Restore configuration files
        print("\n📄 Restoring configuration files...")
        config_dir = restore_dir / "configs"

        if config_dir.exists():
            for config_file in config_dir.iterdir():
                if config_file.is_file():
                    dest = Path(config_file.name)
                    subprocess.run(["cp", str(config_file), str(dest)])
                    print(f"  ✓ {config_file.name}")

        # Restore Docker volumes (if not skipped)
        if not skip_volumes and manifest.get('format') == 'full':
            print("\n💾 Restoring Docker volumes...")
            print("⚠  This will stop running containers...")

            # Stop containers
            subprocess.run([
                "docker", "compose", "-p", self.project_name,
                "down"
            ])

            volumes_dir = restore_dir / "volumes"
            if volumes_dir.exists():
                for volume_backup in volumes_dir.glob("*.tar.gz"):
                    volume_name = volume_backup.stem.replace(".tar", "")
                    self.import_docker_volume(volume_name, volume_backup)

        # Cleanup
        subprocess.run(["rm", "-rf", str(extract_dir)])

        print("\n✓ Import Complete!")
        print("\n📚 Next steps:")
        print("  1. Review imported configuration: cat .env")
        print("  2. Start services: python start_services.py")

        return True

    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        self.print_header("Validating Environment")

        issues = []
        warnings = []

        # Check if .env exists
        if not Path(".env").exists():
            issues.append(".env file not found")
        else:
            print("✓ .env file exists")

            # Read and validate .env
            required_vars = [
                "POSTGRES_PASSWORD",
                "N8N_ENCRYPTION_KEY",
                "N8N_USER_MANAGEMENT_JWT_SECRET",
                "JWT_SECRET",
                "NEO4J_AUTH",
                "ENCRYPTION_KEY",
            ]

            env_vars = {}
            with open(".env", 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

            for var in required_vars:
                if var not in env_vars:
                    issues.append(f"Missing required variable: {var}")
                elif not env_vars[var] or env_vars[var].startswith('generate-'):
                    issues.append(f"Variable not set: {var}")

            if not issues:
                print("✓ All required variables are set")

        # Check Docker
        result = self.run_command(["docker", "--version"])
        if result.returncode == 0:
            print("✓ Docker is installed")
        else:
            issues.append("Docker is not installed or not running")

        # Check Docker Compose
        result = self.run_command(["docker", "compose", "version"])
        if result.returncode == 0:
            print("✓ Docker Compose is installed")
        else:
            issues.append("Docker Compose is not installed")

        # Check optional tools
        for tool in ["sops", "age"]:
            result = self.run_command([tool, "--version"])
            if result.returncode != 0:
                warnings.append(f"{tool} is not installed (optional - needed for encryption)")

        # Summary
        print("\n" + "=" * 60)
        if issues:
            print("❌ Validation Failed")
            print("\nIssues found:")
            for issue in issues:
                print(f"  ✗ {issue}")
        else:
            print("✅ Validation Passed")

        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  ⚠ {warning}")

        return len(issues) == 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Local AI Package Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export complete environment
  python localai_cli.py export --format full

  # Export only configs (no volumes)
  python localai_cli.py export --format config

  # Import environment
  python localai_cli.py import backups/localai_backup_20250101_120000.tar.gz

  # Validate environment
  python localai_cli.py validate

  # Encrypt secrets
  python localai_cli.py encrypt

  # Setup Gitea
  python localai_cli.py setup-gitea
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export environment')
    export_parser.add_argument('--output', help='Output file name')
    export_parser.add_argument('--format', choices=['full', 'config', 'minimal'],
                               default='full', help='Export format')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import environment')
    import_parser.add_argument('backup_file', help='Backup file to import')
    import_parser.add_argument('--skip-volumes', action='store_true',
                              help='Skip Docker volume restoration')

    # Validate command
    subparsers.add_parser('validate', help='Validate environment configuration')

    # Encrypt command
    subparsers.add_parser('encrypt', help='Encrypt secrets with SOPS')

    # Decrypt command
    subparsers.add_parser('decrypt', help='Decrypt secrets from SOPS')

    # Setup Gitea command
    subparsers.add_parser('setup-gitea', help='Initialize Gitea repository')

    # Sync Infisical command
    sync_parser = subparsers.add_parser('sync-infisical', help='Sync secrets with Infisical')
    sync_parser.add_argument('--push', action='store_true', help='Push secrets to Infisical')
    sync_parser.add_argument('--pull', action='store_true', help='Pull secrets from Infisical')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli = LocalAICLI()

    # Execute command
    if args.command == 'export':
        cli.export_environment(args.output, args.format)

    elif args.command == 'import':
        cli.import_environment(args.backup_file, args.skip_volumes)

    elif args.command == 'validate':
        if not cli.validate_environment():
            sys.exit(1)

    elif args.command == 'encrypt':
        print("Running SOPS encryption...")
        subprocess.run(["python", "scripts/encrypt_secrets.py"])

    elif args.command == 'decrypt':
        print("Decrypting .env.enc with SOPS...")
        result = subprocess.run([
            "sops", "--decrypt", ".env.enc"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            with open(".env", 'w') as f:
                f.write(result.stdout)
            print("✓ Decrypted to .env")
        else:
            print(f"✗ Decryption failed: {result.stderr}")
            sys.exit(1)

    elif args.command == 'setup-gitea':
        print("Setting up Gitea...")
        subprocess.run(["python", "scripts/gitea_setup.py"])

    elif args.command == 'sync-infisical':
        cmd = ["python", "scripts/infisical_sync.py"]
        if args.push:
            cmd.append("--push")
        elif args.pull:
            cmd.append("--pull")
        subprocess.run(cmd)


if __name__ == "__main__":
    main()
