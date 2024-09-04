import os
import json
import re
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel

class FileOperations:
    def __init__(self):
        self.console = Console()
        self.file_contents = {}

    def create_folders(self, paths: List[str]) -> Dict[str, Any]:
        """Create new directories."""
        results = []
        for path in paths:
            try:
                os.makedirs(os.path.join('_generations', path), exist_ok=True)
                results.append({"path": path, "status": "success"})
            except Exception as e:
                results.append({"path": path, "status": "error", "message": str(e)})
        return {"results": results}

    def create_files(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create new files with specified content in the '_generations' directory."""
        results = []
        generations_dir = os.path.join(os.getcwd(), '_generations')
        os.makedirs(generations_dir, exist_ok=True)
        for file in files:
            try:
                path = os.path.join(generations_dir, file['path'])
                content = file['content']
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content)
                self.file_contents[path] = content
                results.append({"path": path, "status": "success"})
            except Exception as e:
                results.append({"path": file['path'], "status": "error", "message": str(e)})
        return {"results": results}

    async def edit_and_apply_multiple(self, files: List[Dict[str, Any]], project_context: str) -> List[Dict[str, Any]]:
        """Edit multiple files based on instructions."""
        results = []
        generations_dir = os.path.join(os.getcwd(), '_generations')
        for file in files:
            try:
                relative_path = file['path']
                full_path = os.path.join(generations_dir, relative_path)
                instructions = file['instructions']
                
                # Check if the file is within the _generations directory
                if not full_path.startswith(generations_dir):
                    raise ValueError(f"File {relative_path} is not within the _generations directory")
                
                # Read the current content of the file
                with open(full_path, 'r') as f:
                    current_content = f.read()

                # Generate edit instructions using ClaudeClient
                edit_instructions = await self.claude_client.generate_edit_instructions(
                    relative_path, current_content, instructions, project_context, self.file_contents
                )

                # Apply the edits
                new_content = self.apply_edits(current_content, edit_instructions)

                # Write the new content back to the file
                with open(full_path, 'w') as f:
                    f.write(new_content)

                self.file_contents[full_path] = new_content
                results.append({"path": relative_path, "status": "success", "message": "File edited successfully"})
            except Exception as e:
                results.append({"path": file['path'], "status": "error", "message": str(e)})
        return results

    def read_multiple_files(self, paths: List[str]) -> Dict[str, Any]:
        """Read the contents of multiple files from the '_generations' directory."""
        results = {}
        generations_dir = os.path.join(os.getcwd(), '_generations')
        for path in paths:
            full_path = os.path.join(generations_dir, path)
            if any(w in full_path for w in ['__pycache__', 'venv', '.git', 'site-packages', 'code_execution_env']):
                continue
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                self.file_contents[full_path] = content
                results[path] = {"status": "success", "content": content}
            except Exception as e:
                results[path] = {"status": "error", "message": str(e)}
        return results

    def list_files(self, path: str = ".") -> Dict[str, Any]:
        """List all files and directories in the '_generations' folder."""
        try:
            generations_dir = os.path.join(os.getcwd(), '_generations', path)
            files = []
            for root, dirs, filenames in os.walk(generations_dir):
                print(root, dirs, filenames)
                for filename in filenames:
                    print(filename, '----')
                    if any(w in os.path.join(root, filename) for w in ['__pycache__', 'venv', '.git', 'site-packages', 'code_execution_env']):
                        continue
                    relative_path = os.path.join('_generations', os.path.relpath(os.path.join(root, filename), generations_dir))
                    print('included', relative_path)
                    files.append(relative_path)
            return {"status": "success", "files": files}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def apply_edits(self, content: str, edit_instructions: str) -> str:
        """Apply edit instructions to the file content."""
        search_replace_pairs = re.findall(r'<SEARCH>(.*?)</SEARCH>\s*<REPLACE>(.*?)</REPLACE>', edit_instructions, re.DOTALL)
        
        for search, replace in search_replace_pairs:
            content = content.replace(search.strip(), replace.strip())
        
        return content

    def reset_file_contents(self):
        """Reset the file contents dictionary."""
        self.file_contents = {}

    def update_file_contents(self, file_path: str, content: str):
        """Update the contents of a file in the file_contents dictionary."""
        generations_path = os.path.join(os.getcwd(), '_generations', file_path)
        self.file_contents[generations_path] = content

    def display_files_in_context(self):
        """Display files currently in context."""
        if self.file_contents:
            files_in_context = "\n".join(self.file_contents.keys())
        else:
            files_in_context = "No files in context. Read, create, or edit files to add."
        self.console.print(Panel(files_in_context, title="Files in Context", title_align="left", border_style="white", expand=False))

    async def generate_edit_instructions(self, file_path: str, file_content: str, instructions: str, project_context: str) -> str:
        # This method should be called from ChatManager, passing the claude_client
        raise NotImplementedError("This method should be implemented in ChatManager")
