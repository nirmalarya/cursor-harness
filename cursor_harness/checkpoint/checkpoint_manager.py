"""
Git checkpoint manager for autonomous coding sessions.

Creates safety checkpoints after successful verifications.
Enables rollback on failures.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Checkpoint:
    """A git checkpoint."""
    commit_hash: str
    timestamp: str
    session_id: str
    iteration: int
    message: str
    verification_passed: bool
    files_changed: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'Checkpoint':
        return Checkpoint(**data)


class CheckpointManager:
    """
    Manages git checkpoints during autonomous coding sessions.
    
    Creates automatic commits after successful verifications.
    Supports rollback to previous known-good states.
    """
    
    def __init__(self, project_dir: Path, session_id: str):
        """
        Initialize checkpoint manager.
        
        Args:
            project_dir: Project directory (must be git repo)
            session_id: Unique session identifier
        """
        self.project_dir = Path(project_dir)
        self.session_id = session_id
        
        self.checkpoint_dir = self.project_dir / ".cursor" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoint_file = self.checkpoint_dir / f"{session_id}.json"
        
        self.checkpoints: List[Checkpoint] = []
        self._load_session_checkpoints()
        
        # Ensure git repo exists
        self._ensure_git_repo()
    
    def _ensure_git_repo(self):
        """Ensure project is a git repository."""
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(
                    ['git', 'init'],
                    cwd=self.project_dir,
                    check=True,
                    capture_output=True
                )
                # Set user if not configured
                result = subprocess.run(
                    ['git', 'config', 'user.email'],
                    cwd=self.project_dir,
                    capture_output=True
                )
                if result.returncode != 0:
                    subprocess.run(
                        ['git', 'config', 'user.email', 'cursor-harness@localhost'],
                        cwd=self.project_dir,
                        check=True
                    )
                    subprocess.run(
                        ['git', 'config', 'user.name', 'Cursor Harness'],
                        cwd=self.project_dir,
                        check=True
                    )
            except subprocess.CalledProcessError:
                pass
    
    def create_checkpoint(
        self,
        iteration: int,
        verification_passed: bool,
        message: Optional[str] = None
    ) -> Optional[Checkpoint]:
        """
        Create a checkpoint by committing current state.
        
        Args:
            iteration: Current session iteration
            verification_passed: Whether verification passed
            message: Optional commit message override
        
        Returns:
            Checkpoint object or None if commit failed
        """
        # Get changed files
        changed_files = self._get_changed_files()
        
        if not changed_files:
            # Nothing to checkpoint
            return None
        
        # Build commit message
        if not message:
            status = "✅" if verification_passed else "⚠️"
            message = f"{status} Session {self.session_id[:8]} iteration {iteration}"
        
        # Add checkpoint metadata to commit message
        metadata = {
            'session_id': self.session_id,
            'iteration': iteration,
            'verification_passed': verification_passed,
            'timestamp': datetime.utcnow().isoformat()
        }
        full_message = f"{message}\n\n[cursor-harness-checkpoint]\n{json.dumps(metadata)}"
        
        # Commit
        try:
            # Stage all changes
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', full_message],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()
            
            # Create checkpoint object
            checkpoint = Checkpoint(
                commit_hash=commit_hash,
                timestamp=metadata['timestamp'],
                session_id=self.session_id,
                iteration=iteration,
                message=message,
                verification_passed=verification_passed,
                files_changed=changed_files
            )
            
            self.checkpoints.append(checkpoint)
            self._save_session_checkpoints()
            
            return checkpoint
            
        except subprocess.CalledProcessError as e:
            # Commit failed (might be nothing to commit)
            return None
    
    def rollback_to_checkpoint(
        self,
        checkpoint: Checkpoint,
        hard: bool = False
    ) -> bool:
        """
        Rollback to a checkpoint.
        
        Args:
            checkpoint: Checkpoint to restore
            hard: If True, uses git reset --hard (discards changes)
                  If False, uses git reset --soft (keeps changes staged)
        
        Returns:
            True if rollback successful
        """
        try:
            mode = '--hard' if hard else '--soft'
            subprocess.run(
                ['git', 'reset', mode, checkpoint.commit_hash],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def rollback_iterations(self, count: int, hard: bool = False) -> bool:
        """
        Rollback N iterations from current position.
        
        Args:
            count: Number of iterations to roll back
            hard: Whether to discard changes
        
        Returns:
            True if rollback successful
        """
        if count > len(self.checkpoints):
            return False
        
        target = self.checkpoints[-(count + 1)]
        return self.rollback_to_checkpoint(target, hard=hard)
    
    def get_last_good_checkpoint(self) -> Optional[Checkpoint]:
        """
        Get the most recent checkpoint with passing verification.
        
        Returns:
            Last checkpoint where verification_passed=True
        """
        for checkpoint in reversed(self.checkpoints):
            if checkpoint.verification_passed:
                return checkpoint
        return None
    
    def auto_rollback_on_failure(
        self,
        consecutive_failures: int,
        threshold: int = 3
    ) -> bool:
        """
        Automatically rollback if failures exceed threshold.
        
        Args:
            consecutive_failures: Current failure count
            threshold: Max consecutive failures before rollback
        
        Returns:
            True if rollback was triggered
        """
        if consecutive_failures >= threshold:
            last_good = self.get_last_good_checkpoint()
            if last_good:
                print(f"\n   🔄 Auto-rollback triggered ({consecutive_failures} consecutive failures)")
                print(f"   ⏪ Restoring checkpoint from iteration {last_good.iteration}")
                return self.rollback_to_checkpoint(last_good, hard=True)
        
        return False
    
    def get_checkpoint_history(self) -> List[Checkpoint]:
        """Get all checkpoints for current session."""
        return self.checkpoints.copy()
    
    def get_session_stats(self) -> Dict:
        """Get checkpoint statistics for session."""
        total = len(self.checkpoints)
        passed = sum(1 for cp in self.checkpoints if cp.verification_passed)
        
        return {
            'total_checkpoints': total,
            'passed_checkpoints': passed,
            'failed_checkpoints': total - passed,
            'success_rate': passed / total if total > 0 else 0
        }
    
    def _get_changed_files(self) -> List[str]:
        """Get list of files with uncommitted changes."""
        # Check if we have any commits yet
        try:
            subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_dir,
                capture_output=True,
                timeout=5,
                check=True
            )
            has_commits = True
        except:
            has_commits = False
        
        if has_commits:
            # Normal case: compare against HEAD
            try:
                result = subprocess.run(
                    ['git', 'diff', '--name-only', 'HEAD'],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                    if files:
                        return files
            except:
                pass
            
            # Fallback: unstaged changes
            try:
                result = subprocess.run(
                    ['git', 'diff', '--name-only'],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                    if files:
                        return files
            except:
                pass
        
        # Initial commit case: check untracked files
        try:
            result = subprocess.run(
                ['git', 'ls-files', '--others', '--exclude-standard'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                return files
        except:
            pass
        
        return []
    
    def _load_session_checkpoints(self):
        """Load checkpoints from session file."""
        if not self.checkpoint_file.exists():
            return
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                self.checkpoints = [Checkpoint.from_dict(cp) for cp in data]
        except:
            pass
    
    def _save_session_checkpoints(self):
        """Save checkpoints to session file."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(
                    [cp.to_dict() for cp in self.checkpoints],
                    f,
                    indent=2
                )
        except:
            pass
