"""Infrastructure self-healing."""

import subprocess
import time
from pathlib import Path


class InfrastructureHealer:
    """Auto-fix infrastructure issues."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def heal(self) -> bool:
        """Validate and fix infrastructure."""
        
        fixes = []
        
        # Docker
        if self._has_docker_compose():
            if not self._docker_running():
                print("   🔧 Starting Docker...")
                if self._start_docker():
                    fixes.append("Docker")
        
        # Database migrations
        if self._has_alembic():
            print("   🔧 Running migrations...")
            if self._run_migrations():
                fixes.append("Migrations")
        
        # MinIO buckets
        if self._minio_running():
            print("   🔧 Creating buckets...")
            if self._create_buckets():
                fixes.append("Buckets")
        
        if fixes:
            print(f"   ✅ Fixed: {', '.join(fixes)}")
        
        return True
    
    def _has_docker_compose(self) -> bool:
        return (self.project_dir / "docker-compose.yml").exists()
    
    def _docker_running(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=10
            )
            return len(result.stdout.strip()) > 0
        except:
            return False
    
    def _start_docker(self) -> bool:
        try:
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=120,
                check=True
            )
            time.sleep(10)
            return True
        except:
            return False
    
    def _has_alembic(self) -> bool:
        return (self.project_dir / "alembic").exists()
    
    def _run_migrations(self) -> bool:
        try:
            subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=30,
                check=True
            )
            return True
        except:
            return False
    
    def _minio_running(self) -> bool:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 9000))
            sock.close()
            return result == 0
        except:
            return False
    
    def _create_buckets(self) -> bool:
        buckets = ['diagrams', 'exports', 'uploads']
        for bucket in buckets:
            try:
                subprocess.run(
                    ["docker", "exec", "-i", "autograph-minio", "mc", "mb", "-p", f"local/{bucket}"],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
        return True

