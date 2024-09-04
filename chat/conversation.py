import json
from datetime import datetime
from typing import List, Dict, Any

class Conversation:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.file_contents: Dict[str, str] = {}

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.history.append({"role": role, "content": content})

    def filter_history(self) -> List[Dict[str, Any]]:
        """Filter conversation history to maintain context."""
        filtered_history = []
        for message in self.history:
            if isinstance(message['content'], list):
                filtered_content = [
                    content for content in message['content']
                    if content.get('type') != 'tool_result' or (
                        content.get('type') == 'tool_result' and
                        not any(keyword in content.get('output', '') for keyword in [
                            "File contents updated in system prompt",
                            "File created and added to system prompt",
                            "has been read and stored in the system prompt"
                        ])
                    )
                ]
                if filtered_content:
                    filtered_history.append({**message, 'content': filtered_content})
            else:
                filtered_history.append(message)
        return filtered_history

    def reset(self):
        """Reset the conversation history and file contents."""
        self.history = []
        self.file_contents = {}

    def save_to_file(self) -> str:
        """Save the conversation history to a Markdown file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Chat History\n\n")
            for message in self.history:
                role = message["role"].capitalize()
                content = message["content"]
                f.write(f"## {role}\n\n")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "image":
                                f.write(f"[Image data not displayed]\n\n")
                            elif item.get("type") == "text":
                                f.write(f"{item['text']}\n\n")
                        else:
                            f.write(f"{item}\n\n")
                else:
                    f.write(f"{content}\n\n")
            
            f.write("## File Contents\n\n")
            for file_path, content in self.file_contents.items():
                f.write(f"### {file_path}\n\n")
                f.write("```\n")
                f.write(content)
                f.write("\n```\n\n")

        return filename

    def update_file_contents(self, file_path: str, content: str):
        """Update the contents of a file in the conversation context."""
        self.file_contents[file_path] = content

    def get_file_contents(self, file_path: str) -> str:
        """Get the contents of a file from the conversation context."""
        return self.file_contents.get(file_path, "")

    def remove_file_contents(self, file_path: str):
        """Remove a file from the conversation context."""
        self.file_contents.pop(file_path, None)

    def get_context_summary(self) -> str:
        """Get a summary of the current conversation context."""
        summary = f"Conversation history: {len(self.history)} messages\n"
        summary += f"Files in context: {len(self.file_contents)} files\n"
        for file_path in self.file_contents.keys():
            summary += f"- {file_path}\n"
        return summary
