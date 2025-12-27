"""
Infrastructure Validator
========================

Validates infrastructure ONCE at startup, then caches result.
Prevents infinite validation loops while ensuring autonomous operation.

Works for all modes: greenfield, backlog, enhancement, bugfix.
"""

import json
import socket
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class InfrastructureValidator:
    """
    Validates project infrastructure requirements.
    
    Validates ONCE per run, caches result to prevent loops.
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.cache_file = project_dir / ".cursor" / "infra-validation-cache.json"
    
    def validate_once(self, mode: str = "greenfield") -> Tuple[bool, str]:
        """
        Validate infrastructure requirements ONCE.
        
        Args:
            mode: greenfield, backlog, enhancement, or bugfix
        
        Returns:
            (is_valid, message)
        """
        
        # Check cache first
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    cache = json.load(f)
                
                # If validated in last 24 hours, trust it
                from datetime import datetime, timedelta
                cached_time = datetime.fromisoformat(cache['validated_at'])
                if datetime.now() - cached_time < timedelta(hours=24):
                    print(f"   ✅ Infrastructure validated (cached from {cache['validated_at']})")
                    return cache['is_valid'], cache.get('message', '')
            except:
                pass  # Cache invalid, re-validate
        
        print("\n🔍 Validating infrastructure (one-time check)...")
        
        # Run validation based on mode
        if mode == "greenfield":
            is_valid, message = self._validate_greenfield()
        else:
            is_valid, message = self._validate_brownfield()
        
        # Cache result
        self._save_cache(is_valid, message)
        
        return is_valid, message
    
    def _validate_greenfield(self) -> Tuple[bool, str]:
        """
        Validate greenfield requirements.
        
        Greenfield usually needs:
        - Git initialized
        - Directory writable
        - (Docker is optional - will be created)
        """
        
        checks = []
        
        # Check 1: Directory writable
        try:
            test_file = self.project_dir / ".cursor" / ".write_test"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("test")
            test_file.unlink()
            checks.append(("Directory writable", True, ""))
        except Exception as e:
            checks.append(("Directory writable", False, str(e)))
        
        # Check 2: Git initialized (or can initialize)
        git_dir = self.project_dir / ".git"
        if git_dir.exists():
            checks.append(("Git initialized", True, ""))
        else:
            # Try to init
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=5
                )
                checks.append(("Git initialized", True, "Auto-initialized"))
            except Exception as e:
                checks.append(("Git initialized", False, str(e)))
        
        # Print results
        print("\n   Infrastructure Checks (Greenfield):")
        for name, passed, detail in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {name}" + (f": {detail}" if detail else ""))
        
        # All must pass
        all_passed = all(check[1] for check in checks)
        
        if all_passed:
            return True, "All greenfield requirements met"
        else:
            failed = [check[0] for check in checks if not check[1]]
            return False, f"Missing requirements: {', '.join(failed)}"
    
    def _validate_brownfield(self) -> Tuple[bool, str]:
        """
        Validate brownfield/backlog requirements.
        
        Brownfield needs:
        - Git repository exists
        - Docker Compose file (if applicable)
        - Services running (if specified)
        """
        
        checks = []
        
        # Check 1: Git repository
        git_dir = self.project_dir / ".git"
        checks.append(("Git repository", git_dir.exists(), ""))
        
        # Check 2: Docker Compose (optional but check if exists)
        docker_compose = self.project_dir / "docker-compose.yml"
        if docker_compose.exists():
            # Try to check if services running
            try:
                result = subprocess.run(
                    ["docker", "compose", "ps", "--quiet"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=10
                )
                running_containers = len([line for line in result.stdout.decode().split('\n') if line.strip()])
                
                if running_containers > 0:
                    checks.append(("Docker services", True, f"{running_containers} containers running"))
                else:
                    checks.append(("Docker services", False, "No containers running - run 'docker compose up -d'"))
            except Exception as e:
                checks.append(("Docker services", False, str(e)))
        else:
            checks.append(("Docker Compose", True, "Not using Docker"))
        
        # Print results
        print("\n   Infrastructure Checks (Brownfield):")
        for name, passed, detail in checks:
            status = "✅" if passed else "⚠️ "
            print(f"   {status} {name}" + (f": {detail}" if detail else ""))
        
        # For brownfield, warn but don't fail on Docker
        git_ok = checks[0][1]  # Git must exist
        
        if git_ok:
            return True, "Brownfield infrastructure validated"
        else:
            return False, "Git repository required for brownfield mode"
    
    def _save_cache(self, is_valid: bool, message: str):
        """Save validation result to cache."""
        from datetime import datetime
        
        cache = {
            "is_valid": is_valid,
            "message": message,
            "validated_at": datetime.now().isoformat()
        }
        
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def invalidate_cache(self):
        """Clear validation cache (for forcing re-validation)."""
        if self.cache_file.exists():
            self.cache_file.unlink()
            print("   🔄 Infrastructure validation cache cleared")


def check_port_available(port: int, host: str = "localhost") -> bool:
    """Check if a port is available."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0  # 0 = port in use, non-zero = available
    except:
        return True  # Assume available if check fails


def check_database_connection(db_url: str) -> Tuple[bool, str]:
    """
    Check database connection.
    
    Args:
        db_url: Database URL (postgresql://...)
    
    Returns:
        (is_connected, message)
    """
    try:
        # Try to import database library
        import psycopg2
        
        # Parse connection string
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.close()
        return True, "Database connected"
    except ImportError:
        return True, "Database library not installed (will be added by project)"
    except Exception as e:
        return False, f"Database connection failed: {e}"

