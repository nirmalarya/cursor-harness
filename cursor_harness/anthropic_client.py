"""
Anthropic API Client Wrapper
=============================

Handles communication with the Anthropic API and tool execution.
"""

import os
from pathlib import Path
from typing import Any

import anthropic

from tools import (
    BashTool,
    EditTool,
    GlobTool,
    GrepTool,
    ListDirectoryTool,
    ReadTool,
    WriteTool,
)


class AgentClient:
    """Client for running agent sessions with the Anthropic API."""

    def __init__(
        self,
        project_dir: Path,
        model: str,
        max_tokens: int,
        security_validator,
    ):
        self.project_dir = project_dir
        self.model = model
        self.max_tokens = max_tokens
        self.security_validator = security_validator

        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set.\n"
                "Get your API key from: https://console.anthropic.com/"
            )

        self.client = anthropic.Anthropic(api_key=api_key)

        # Initialize tools
        self.tools = self._setup_tools()

        # Message history for this session
        self.messages = []

    def _setup_tools(self) -> list:
        """Set up all available tools."""
        read_tool = ReadTool(self.project_dir)
        write_tool = WriteTool(self.project_dir)
        edit_tool = EditTool(self.project_dir)
        glob_tool = GlobTool(self.project_dir)
        grep_tool = GrepTool(self.project_dir)
        list_tool = ListDirectoryTool(self.project_dir)
        bash_tool = BashTool(self.project_dir, self.security_validator)

        tool_instances = [
            read_tool,
            write_tool,
            edit_tool,
            glob_tool,
            grep_tool,
            list_tool,
            bash_tool,
        ]

        # Store tool instances for execution
        self.tool_instances = {tool.name: tool for tool in tool_instances}

        # Return Anthropic tool definitions
        return [tool.to_anthropic_tool() for tool in tool_instances]

    async def run_session(self, initial_message: str, max_turns: int = 1000) -> tuple[str, str]:
        """
        Run an agent session.

        Args:
            initial_message: The initial prompt/message
            max_turns: Maximum number of conversation turns

        Returns:
            Tuple of (status, final_response_text)
            status is "complete", "max_turns", or "error"
        """
        # Add initial user message
        self.messages.append({"role": "user", "content": initial_message})

        final_response = ""
        turn = 0

        try:
            while turn < max_turns:
                turn += 1
                print(f"\n[Turn {turn}/{max_turns}]", flush=True)

                # Call Anthropic API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=self.messages,
                    tools=self.tools,
                )

                # Add assistant response to messages
                assistant_message = {
                    "role": "assistant",
                    "content": response.content,
                }
                self.messages.append(assistant_message)

                # Process response content
                tool_uses = []
                text_content = []

                for block in response.content:
                    if block.type == "text":
                        text_content.append(block.text)
                        final_response = block.text
                        print(block.text, flush=True)

                    elif block.type == "tool_use":
                        tool_uses.append(block)
                        print(f"\n[Tool: {block.name}]", flush=True)
                        # Print truncated input
                        input_str = str(block.input)
                        if len(input_str) > 200:
                            print(f"   Input: {input_str[:200]}...", flush=True)
                        else:
                            print(f"   Input: {input_str}", flush=True)

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Agent is done
                    print("\n" + "-" * 70)
                    return "complete", final_response

                elif response.stop_reason == "tool_use":
                    # Execute tools
                    tool_results = await self._execute_tools(tool_uses)

                    # Add tool results to messages
                    self.messages.append({
                        "role": "user",
                        "content": tool_results,
                    })

                elif response.stop_reason == "max_tokens":
                    print("\n[Warning: Hit max_tokens in response]", flush=True)
                    # Continue the conversation
                    continue

                else:
                    print(f"\n[Unknown stop reason: {response.stop_reason}]", flush=True)
                    return "error", f"Unknown stop reason: {response.stop_reason}"

            # Hit max turns
            print(f"\n[Reached max turns: {max_turns}]", flush=True)
            return "max_turns", final_response

        except Exception as e:
            print(f"\n[Error: {e}]", flush=True)
            return "error", str(e)

    async def _execute_tools(self, tool_uses: list) -> list[dict]:
        """Execute tool use blocks and return results."""
        results = []

        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            tool_use_id = tool_use.id

            # Find and execute tool
            if tool_name not in self.tool_instances:
                result_text = f"Error: Unknown tool '{tool_name}'"
                is_error = True
            else:
                tool = self.tool_instances[tool_name]
                result_text, is_error = await tool.execute(**tool_input)

            # Show result
            if is_error:
                # Show errors (truncated)
                error_str = str(result_text)[:500]
                print(f"   [Error] {error_str}", flush=True)
            elif "BLOCKED" in result_text:
                # Security block
                print(f"   [BLOCKED] {result_text}", flush=True)
            else:
                # Success
                print("   [Done]", flush=True)

            # Add to results
            results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_text,
                "is_error": is_error,
            })

        return results



