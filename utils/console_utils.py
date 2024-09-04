import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from typing import Optional

console = Console()

async def get_user_input(prompt: str = "You: ") -> str:
    """
    Asynchronously get user input with a styled prompt.

    Args:
    prompt (str): The prompt to display before user input.

    Returns:
    str: The user's input.
    """
    style = Style.from_dict({
        'prompt': 'cyan bold',
    })
    session = PromptSession(style=style)
    return await session.prompt_async(prompt, multiline=False)

def display_assistant_response(response: str):
    """
    Display the assistant's response in a formatted panel.

    Args:
    response (str): The assistant's response to display.
    """
    console.print(Panel(Markdown(response), title="Claude's Response", title_align="left", border_style="blue", expand=False))

def display_code(code: str, language: str = "python"):
    """
    Display code with syntax highlighting.

    Args:
    code (str): The code to display.
    language (str): The programming language of the code (default is "python").
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"{language.capitalize()} Code", border_style="green"))

def display_error(message: str):
    """
    Display an error message in a formatted panel.

    Args:
    message (str): The error message to display.
    """
    console.print(Panel(message, title="Error", style="bold red"))

def display_info(message: str):
    """
    Display an informational message in a formatted panel.

    Args:
    message (str): The informational message to display.
    """
    console.print(Panel(message, title="Info", style="bold yellow"))

def display_success(message: str):
    """
    Display a success message in a formatted panel.

    Args:
    message (str): The success message to display.
    """
    console.print(Panel(message, title="Success", style="bold green"))

def display_file_contents(file_path: str, content: str):
    """
    Display the contents of a file in a formatted panel.

    Args:
    file_path (str): The path of the file.
    content (str): The content of the file.
    """
    console.print(Panel(content, title=f"File: {file_path}", border_style="cyan", expand=False))

def display_tool_result(tool_name: str, result: str):
    """
    Display the result of a tool execution in a formatted panel.

    Args:
    tool_name (str): The name of the tool.
    result (str): The result of the tool execution.
    """
    console.print(Panel(result, title=f"Tool Result: {tool_name}", border_style="magenta", expand=False))

async def confirm_action(prompt: str) -> bool:
    """
    Ask for user confirmation before performing an action.

    Args:
    prompt (str): The confirmation prompt to display.

    Returns:
    bool: True if the user confirms, False otherwise.
    """
    response = await get_user_input(f"{prompt} (y/n): ")
    return response.lower().strip() == 'y'

def clear_console():
    """
    Clear the console screen.
    """
    console.clear()

def display_welcome_message():
    """
    Display a welcome message when the application starts.
    """
    welcome_message = """
    Welcome to the Claude-3-Sonnet Engineer Chat!
    
    - Type 'exit' to end the conversation.
    - Type 'image' to include an image in your message.
    - Type 'automode [number]' to enter Autonomous mode with a specific number of iterations.
    - Type 'reset' to clear the conversation history.
    - Type 'save chat' to save the conversation to a Markdown file.
    
    While in automode, press Ctrl+C at any time to exit and return to regular chat.
    """
    console.print(Panel(welcome_message, title="Welcome", style="bold green"))

