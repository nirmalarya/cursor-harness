"""Secrets scanner to prevent committing sensitive data."""

import re
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class SecretMatch:
    file: str
    line: int
    type: str
    match: str


class SecretsScanner:
    """Scan for exposed secrets."""
    
    PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'secret_key': r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'password': r'(?i)password\s*[:=]\s*["\']([^"\']{8,})["\']',
        'jwt_secret': r'(?i)jwt[_-]?secret\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'private_key': r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
        'aws_key': r'(?i)aws[_-]?access[_-]?key[_-]?id\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?',
        'github_token': r'(?i)github[_-]?token\s*[:=]\s*["\']?([a-zA-Z0-9_]{40,})["\']?',
    }
    
    IGNORE_PATTERNS = [
        'example',
        'sample',
        'test',
        'dummy',
        'placeholder',
        'your_',
        '<',
        '>',
    ]
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def scan(self) -> List[SecretMatch]:
        """Scan for secrets."""
        secrets = []
        
        for pattern_name, pattern in self.PATTERNS.items():
            matches = self._scan_pattern(pattern, pattern_name)
            secrets.extend(matches)
        
        return secrets
    
    def _scan_pattern(self, pattern: str, pattern_name: str) -> List[SecretMatch]:
        """Scan for a specific pattern."""
        matches = []
        
        for file_path in self._get_files():
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        # Check if it's a false positive
                        if not self._is_false_positive(line):
                            matches.append(SecretMatch(
                                file=str(file_path.relative_to(self.project_dir)),
                                line=i,
                                type=pattern_name,
                                match=line.strip()[:100]
                            ))
            except:
                pass
        
        return matches
    
    def _is_false_positive(self, line: str) -> bool:
        """Check if match is a false positive."""
        lower_line = line.lower()
        return any(ignore in lower_line for ignore in self.IGNORE_PATTERNS)
    
    def _get_files(self) -> List[Path]:
        """Get all files to scan."""
        files = []
        
        for ext in ['.py', '.js', '.ts', '.go', '.java', '.rb', '.env', '.yml', '.yaml', '.json']:
            files.extend(self.project_dir.rglob(f'*{ext}'))
        
        # Filter out node_modules, .git, etc
        files = [f for f in files if not any(
            part in f.parts for part in ['.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build']
        )]
        
        return files

