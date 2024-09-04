import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    def __init__(self):
        self.MAX_CONTINUATION_ITERATIONS = int(os.getenv('MAX_CONTINUATION_ITERATIONS', 10))
        self.CONTINUATION_EXIT_PHRASE = os.getenv('CONTINUATION_EXIT_PHRASE', "AUTOMODE_COMPLETE")
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
        self.tools = [
            {
                "name": "create_folders",
                "description": "Create new folders at the specified paths. This tool should be used when you need to create one or more directories in the project structure. It will create all necessary parent directories if they don't exist.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "An array of absolute or relative paths where the folders should be created. Use forward slashes (/) for path separation, even on Windows systems."
                        }
                    },
                    "required": ["paths"]
                }
            },
            {
                "name": "scan_folder",
                "description": "Scan a specified folder and create a Markdown file with the contents of all coding text files, excluding binary files and common ignored folders.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "folder_path": {
                            "type": "string",
                            "description": "The absolute or relative path of the folder to scan. Use forward slashes (/) for path separation, even on Windows systems."
                        },
                        "output_file": {
                            "type": "string",
                            "description": "The name of the output Markdown file to create with the scanned contents."
                        }
                    },
                    "required": ["folder_path", "output_file"]
                }
            },
            {
                "name": "create_files",
                "description": "Create one or more new files with the given contents. This tool should be used when you need to create files in the project structure. It will create all necessary parent directories if they don't exist.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "The absolute or relative path where the file should be created. Use forward slashes (/) for path separation, even on Windows systems."
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The content of the file. This should include all necessary code, comments, and formatting."
                                    }
                                },
                                "required": ["path", "content"]
                            }
                        }
                    }
                }
            },
            {
                "name": "edit_and_apply_multiple",
                "description": "Apply AI-powered improvements to multiple files based on specific instructions and detailed project context.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "The absolute or relative path of the file to edit."
                                    },
                                    "instructions": {
                                        "type": "string",
                                        "description": "Specific instructions for editing this file."
                                    }
                                },
                                "required": ["path", "instructions"]
                            }
                        },
                        "project_context": {
                            "type": "string",
                            "description": "Comprehensive context about the project, including recent changes, new variables or functions, interconnections between files, coding standards, and any other relevant information that might affect the edits."
                        }
                    },
                    "required": ["files", "project_context"]
                }
            },
            {
                "name": "execute_code",
                "description": "Execute Python code in the 'code_execution_env' virtual environment and return the output. This tool should be used when you need to run code and see its output or check for errors. All code execution happens exclusively in this isolated environment. The tool will return the standard output, standard error, and return code of the executed code. Long-running processes will return a process ID for later management.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to execute in the 'code_execution_env' virtual environment. Include all necessary imports and ensure the code is complete and self-contained."
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "stop_process",
                "description": "Stop a running process by its ID. This tool should be used to terminate long-running processes that were started by the execute_code tool. It will attempt to stop the process gracefully, but may force termination if necessary. The tool will return a success message if the process is stopped, and an error message if the process doesn't exist or can't be stopped.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "process_id": {
                            "type": "string",
                            "description": "The ID of the process to stop, as returned by the execute_code tool for long-running processes."
                        }
                    },
                    "required": ["process_id"]
                }
            },
            {
                "name": "read_multiple_files",
                "description": "Read the contents of one or more existing files at once. This tool now handles both single and multiple file reads. Use this when you need to examine or work with file contents.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "description": "The absolute or relative path of a single file to read."
                                },
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "An array of absolute or relative paths of the files to read."
                                }
                            ],
                            "description": "The path(s) of the file(s) to read. Use forward slashes (/) for path separation, even on Windows systems."
                        }
                    },
                    "required": ["paths"]
                }
            },
            {
                "name": "list_files",
                "description": "List all files and directories in the specified folder. This tool should be used when you need to see the contents of a directory. It will return a list of all files and subdirectories in the specified path. If the directory doesn't exist or can't be read, an appropriate error message will be returned.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The absolute or relative path of the folder to list. Use forward slashes (/) for path separation, even on Windows systems. If not provided, the current working directory will be used."
                        }
                    }
                }
            },
            {
                "name": "tavily_search",
                "description": "Perform a web search using the Tavily API to get up-to-date information or additional context. This tool should be used when you need current information or feel a search could provide a better answer to the user's query. It will return a summary of the search results, including relevant snippets and source URLs.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query. Be as specific and detailed as possible to get the most relevant results."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    def update_system_prompt(self, current_iteration=None, max_iterations=None):
        base_prompt = """You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest. Your primary function is to assist users with coding tasks, answer questions, and provide guidance on software development topics."""
        
        if current_iteration is not None and max_iterations is not None:
            base_prompt += f"\nCurrent iteration: {current_iteration}/{max_iterations}"
        
        return base_prompt

    def get_api_key(self, key_name):
        api_key = getattr(self, key_name, None)
        if not api_key:
            raise ValueError(f"{key_name} not found in environment variables")
        return api_key
