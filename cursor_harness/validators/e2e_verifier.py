"""
E2E Verification for cursor-harness v3.0.4

Lightweight verification that E2E testing was performed.
Based on Anthropic's autonomous-coding demo pattern.

Checks:
1. Screenshots exist in .cursor/verification/
2. User-facing features require E2E testing
3. Backend features can skip E2E testing

Philosophy:
- Trust the agent to do E2E testing (Anthropic pattern)
- Verify artifacts exist (production enhancement)
- Keep it simple and lightweight
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class E2EVerificationResult:
    """Result of E2E verification."""
    passed: bool
    reason: str
    screenshot_count: int


class E2EVerifier:
    """
    Lightweight E2E verification - checks that testing was performed.

    Based on Anthropic's pattern:
    - Agent performs E2E testing using Puppeteer MCP
    - Agent saves screenshots to .cursor/verification/
    - Harness verifies screenshots exist (proof of testing)

    This prevents agent from marking features as passing without E2E testing.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.verification_dir = project_dir / ".cursor" / "verification"

    def verify(self, work_item: Optional[dict]) -> E2EVerificationResult:
        """
        Verify E2E testing was performed for this work item.

        Args:
            work_item: Feature from feature_list.json (or None if no work)

        Returns:
            E2EVerificationResult with pass/fail status
        """

        if not work_item:
            return E2EVerificationResult(
                passed=True,
                reason="No work item - skipping E2E verification",
                screenshot_count=0
            )

        # Only check user-facing features
        if not self._is_user_facing(work_item):
            return E2EVerificationResult(
                passed=True,
                reason="Backend/infrastructure feature - E2E not required",
                screenshot_count=0
            )

        # Check verification directory exists
        if not self.verification_dir.exists():
            return E2EVerificationResult(
                passed=False,
                reason="No .cursor/verification directory found - E2E testing not performed",
                screenshot_count=0
            )

        # Check screenshots exist
        screenshots = list(self.verification_dir.glob("*.png")) + \
                     list(self.verification_dir.glob("*.jpg")) + \
                     list(self.verification_dir.glob("*.jpeg"))

        if not screenshots:
            return E2EVerificationResult(
                passed=False,
                reason="No screenshots found in .cursor/verification/ - E2E testing not performed",
                screenshot_count=0
            )

        # Success: Screenshots exist = E2E testing was done
        return E2EVerificationResult(
            passed=True,
            reason=f"E2E testing verified - found {len(screenshots)} screenshot(s)",
            screenshot_count=len(screenshots)
        )

    def _is_user_facing(self, work_item: dict) -> bool:
        """
        Check if feature requires E2E testing.

        User-facing features have:
        - UI-related keywords (click, button, page, form, etc.)
        - Test steps (E2E test cases)
        - Category: functional or style

        Backend features don't require E2E:
        - API endpoints (unless testing via UI)
        - Database migrations
        - Infrastructure setup
        """

        description = work_item.get('description', '').lower()
        steps = work_item.get('steps', [])
        category = work_item.get('category', '')

        # Keywords that indicate user-facing features
        ui_keywords = [
            'click', 'button', 'page', 'form', 'display', 'navigate',
            'user can', 'user sees', 'ui', 'interface', 'screen',
            'menu', 'modal', 'dialog', 'input', 'select', 'dropdown',
            'view', 'show', 'hide', 'toggle', 'render', 'layout'
        ]

        # Check description for UI keywords
        if any(keyword in description for keyword in ui_keywords):
            return True

        # Check if has test steps (E2E test cases from feature_list.json)
        if steps and len(steps) > 0:
            # Check if steps contain user interactions
            steps_text = ' '.join(steps).lower()
            if any(keyword in steps_text for keyword in ui_keywords):
                return True

        # Check category (functional/style usually need E2E)
        if category in ['functional', 'style', 'ui', 'ux']:
            return True

        # Backend keywords that DON'T need E2E
        backend_keywords = [
            'api endpoint', 'database', 'migration', 'schema',
            'model', 'orm', 'query', 'service', 'controller',
            'middleware', 'authentication token', 'session storage'
        ]

        if any(keyword in description for keyword in backend_keywords):
            # Backend features usually don't need E2E
            # UNLESS they also have UI keywords
            return False

        # Default: If unsure, require E2E testing (safe default)
        return True

    def clear_screenshots(self):
        """
        Clear screenshots directory (for next session).

        Call this after successfully validating a feature
        to ensure fresh screenshots for next feature.
        """
        if self.verification_dir.exists():
            for screenshot in self.verification_dir.glob("*"):
                screenshot.unlink()
