"""
MCP Server Setup for cursor-harness v3.0.5

Configures Model Context Protocol servers for:
1. Browser automation (Puppeteer or Playwright)
2. Azure DevOps integration (for backlog mode)

Based on:
- Anthropic's MCP pattern: https://www.anthropic.com/news/model-context-protocol
- Azure DevOps MCP: https://learn.microsoft.com/en-us/azure/devops/mcp-server/
- Puppeteer MCP: https://www.npmjs.com/package/@modelcontextprotocol/server-puppeteer
- Playwright MCP: https://github.com/executeautomation/mcp-playwright

cursor-agent automatically discovers mcp.json configurations.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class MCPServerSetup:
    """Setup and configure MCP servers for cursor-harness."""

    def __init__(self, project_dir: Path, mode: str):
        self.project_dir = project_dir
        self.mode = mode
        self.mcp_config_file = project_dir / "mcp.json"

    def setup(self, ado_org: Optional[str] = None, ado_project: Optional[str] = None):
        """
        Setup MCP servers based on mode.

        Args:
            ado_org: Azure DevOps organization (for backlog mode)
            ado_project: Azure DevOps project (for backlog mode)
        """
        print("🔧 Setting up MCP servers...")

        servers = {}

        # Browser automation for greenfield/enhancement modes
        if self.mode in ['greenfield', 'enhancement']:
            browser_server = self._setup_browser_automation()
            if browser_server:
                servers.update(browser_server)

        # Azure DevOps for backlog mode
        if self.mode == 'backlog':
            if not ado_org or not ado_project:
                print("   ⚠️  Azure DevOps mode requires --org and --project")
            else:
                ado_server = self._setup_azure_devops(ado_org, ado_project)
                if ado_server:
                    servers.update(ado_server)

        if servers:
            self._write_mcp_config(servers)
            self._verify_mcp_setup()
        else:
            print("   ℹ️  No MCP servers configured (not required for this mode)")

    def _setup_browser_automation(self) -> Optional[Dict]:
        """
        Setup browser automation MCP server (Puppeteer or Playwright).

        Returns:
            MCP server config dict or None
        """
        print("   🌐 Configuring browser automation MCP...")

        # Try Puppeteer first (Anthropic's official choice)
        if self._check_npm_package_available("@modelcontextprotocol/server-puppeteer"):
            print("      ✅ Using Puppeteer MCP (@modelcontextprotocol/server-puppeteer)")
            return {
                "puppeteer": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-puppeteer"
                    ],
                    "env": {}
                }
            }

        # Fallback to Playwright if available
        if self._check_npm_package_available("@executeautomation/mcp-playwright"):
            print("      ✅ Using Playwright MCP (@executeautomation/mcp-playwright)")
            return {
                "playwright": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@executeautomation/mcp-playwright"
                    ],
                    "env": {}
                }
            }

        # Neither available - install Puppeteer (Anthropic's choice)
        print("      📦 Installing Puppeteer MCP server...")
        if self._install_puppeteer_mcp():
            print("      ✅ Puppeteer MCP installed successfully")
            return {
                "puppeteer": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-puppeteer"
                    ],
                    "env": {}
                }
            }

        print("      ⚠️  Could not setup browser automation MCP")
        print("      💡 Install Node.js and run: npm install -g @modelcontextprotocol/server-puppeteer")
        return None

    def _setup_azure_devops(self, org: str, project: str) -> Optional[Dict]:
        """
        Setup Azure DevOps MCP server.

        Args:
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            MCP server config dict or None
        """
        print("   📋 Configuring Azure DevOps MCP...")

        # Check if Azure DevOps MCP is available
        # Microsoft's official: @microsoft/azure-devops-mcp-server
        # Community: @tiberriver256/mcp-server-azure-devops

        if self._check_npm_package_available("@microsoft/azure-devops-mcp-server"):
            print("      ✅ Using Microsoft Azure DevOps MCP (official)")
            return {
                "azure-devops": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@microsoft/azure-devops-mcp-server"
                    ],
                    "env": {
                        "AZURE_DEVOPS_ORG": org,
                        "AZURE_DEVOPS_PROJECT": project
                    }
                }
            }

        # Try community version
        if self._check_npm_package_available("@tiberriver256/mcp-server-azure-devops"):
            print("      ✅ Using community Azure DevOps MCP")
            return {
                "azure-devops": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@tiberriver256/mcp-server-azure-devops"
                    ],
                    "env": {
                        "AZURE_DEVOPS_ORG": org,
                        "AZURE_DEVOPS_PROJECT": project
                    }
                }
            }

        # Try to install Microsoft's official version
        print("      📦 Installing Azure DevOps MCP server...")
        try:
            subprocess.run(
                ["npm", "install", "-g", "@microsoft/azure-devops-mcp-server"],
                capture_output=True,
                timeout=60,
                check=True
            )
            print("      ✅ Azure DevOps MCP installed successfully")
            return {
                "azure-devops": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@microsoft/azure-devops-mcp-server"
                    ],
                    "env": {
                        "AZURE_DEVOPS_ORG": org,
                        "AZURE_DEVOPS_PROJECT": project
                    }
                }
            }
        except:
            pass

        print("      ⚠️  Could not setup Azure DevOps MCP")
        print("      💡 Install manually: npm install -g @microsoft/azure-devops-mcp-server")
        print("      💡 Or use community version: npm install -g @tiberriver256/mcp-server-azure-devops")
        return None

    def _check_npm_package_available(self, package_name: str) -> bool:
        """Check if npm package is available (installed or in registry)."""
        try:
            # Check if installed globally
            result = subprocess.run(
                ["npm", "list", "-g", package_name],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True

            # Check if available in npm registry
            result = subprocess.run(
                ["npm", "view", package_name, "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _install_puppeteer_mcp(self) -> bool:
        """Install Puppeteer MCP server globally."""
        try:
            result = subprocess.run(
                ["npm", "install", "-g", "@modelcontextprotocol/server-puppeteer"],
                capture_output=True,
                timeout=120,
                check=True
            )
            return result.returncode == 0
        except:
            return False

    def _write_mcp_config(self, servers: Dict):
        """Write mcp.json configuration file."""
        config = {
            "mcpServers": servers
        }

        # Merge with existing config if it exists
        if self.mcp_config_file.exists():
            try:
                with open(self.mcp_config_file) as f:
                    existing = json.load(f)
                    existing_servers = existing.get("mcpServers", {})
                    # Add new servers, preserve existing ones
                    existing_servers.update(servers)
                    config["mcpServers"] = existing_servers
            except:
                pass

        with open(self.mcp_config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"   ✅ MCP configuration written to {self.mcp_config_file.name}")
        print(f"   📦 Configured {len(servers)} MCP server(s):")
        for server_name in servers.keys():
            print(f"      - {server_name}")

    def _verify_mcp_setup(self):
        """Verify MCP servers are configured correctly."""
        try:
            # Check if cursor-agent can list MCP servers
            result = subprocess.run(
                ["cursor-agent", "mcp", "list"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=10,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                print(f"   ✅ MCP servers verified (cursor-agent mcp list works)")
            else:
                print(f"   ℹ️  MCP configured (cursor-agent will auto-discover)")
        except:
            # cursor-agent mcp list might not work in all versions
            print(f"   ℹ️  MCP configured (cursor-agent will auto-discover)")

    def get_browser_tools(self) -> List[str]:
        """
        Get list of browser automation tools available.

        Returns:
            List of tool names (e.g., ['puppeteer_navigate', 'puppeteer_screenshot'])
        """
        if not self.mcp_config_file.exists():
            return []

        try:
            with open(self.mcp_config_file) as f:
                config = json.load(f)
                servers = config.get("mcpServers", {})

                if "puppeteer" in servers:
                    return [
                        "puppeteer_navigate",
                        "puppeteer_screenshot",
                        "puppeteer_click",
                        "puppeteer_fill",
                        "puppeteer_select",
                        "puppeteer_hover",
                        "puppeteer_evaluate"
                    ]
                elif "playwright" in servers:
                    return [
                        "playwright_navigate",
                        "playwright_screenshot",
                        "playwright_click",
                        "playwright_fill",
                        "playwright_type"
                    ]
        except:
            pass

        return []
