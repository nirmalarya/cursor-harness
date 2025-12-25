"""
Output Formatter for Better Readability
========================================

Formats agent tool use output to be more human-readable.
"""

def format_tool_output(tool_name: str, tool_input: dict, result: str = None) -> str:
    """Format tool usage in a readable way (compact version)."""
    
    # Map tool names to readable labels
    tool_labels = {
        "TodoWrite": "📝",
        "Edit": "✏️",
        "Write": "📄",
        "Read": "📖",
        "Bash": "⚡",
        "mcp__puppeteer__puppeteer_navigate": "🌐",
        "mcp__puppeteer__puppeteer_click": "🖱️",
        "mcp__puppeteer__puppeteer_screenshot": "📸",
        "Grep": "🔍",
        "Glob": "📂",
    }
    
    emoji = tool_labels.get(tool_name, "🔧")
    
    output = f"\n{emoji} {tool_name}: "
    
    # Format based on tool type (compact!)
    if tool_name == "TodoWrite":
        todos = tool_input.get('todos', [])
        status_emoji = {'completed': '✅', 'in_progress': '🔄', 'pending': '⏳', 'cancelled': '❌'}
        tasks = ', '.join([f"{status_emoji.get(t.get('status','pending'), '📌')} {t.get('content','')[:40]}" for t in todos[:3]])
        output += tasks
        if len(todos) > 3:
            output += f" (+{len(todos)-3} more)"
    
    elif tool_name == "Edit":
        file = tool_input.get('file_path', '').split('/')[-1]  # Just filename
        output += file
    
    elif tool_name == "Write":
        file = tool_input.get('file_path', '').split('/')[-1]
        output += file
    
    elif tool_name == "Read":
        file = tool_input.get('target_file', '').split('/')[-1]
        output += file
    
    elif tool_name == "Bash":
        desc = tool_input.get('description', '')
        if desc:
            output += desc
        else:
            cmd = tool_input.get('command', '')[:50]
            output += cmd
    
    elif "puppeteer" in tool_name:
        if "navigate" in tool_name:
            output += tool_input.get('url', '')
        elif "click" in tool_name:
            output += str(tool_input.get('selector', tool_input.get('element', '')))[:40]
        elif "screenshot" in tool_name:
            output += tool_input.get('name', 'screenshot')
        else:
            output += "browser action"
    
    else:
        # Generic fallback - just show tool name
        output += "executing..."
    
    return output


# Example usage in progress display
def print_session_progress(session_num: int, total_features: int, passing_features: int):
    """Print formatted session progress."""
    
    percentage = (passing_features / total_features * 100) if total_features > 0 else 0
    
    separator = "━" * 70
    
    print(f"\n{separator}")
    print(f"📊 Session {session_num} Progress")
    print(f"{separator}\n")
    print(f"Features: {passing_features}/{total_features} passing ({percentage:.1f}%)")
    print(f"Remaining: {total_features - passing_features} features\n")
    print(f"{separator}\n")

