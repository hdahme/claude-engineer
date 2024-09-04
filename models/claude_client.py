from anthropic import Anthropic, APIStatusError, APIError
import asyncio
from typing import List, Dict, Any
import json

class ClaudeClient:
    def __init__(self, config):
        self.client = Anthropic(api_key=config.get_api_key("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20240620"
        self.code_editor_memory = []
        self.code_editor_files = set()

    async def generate_response(self, messages: List[Dict[str, Any]], system_prompt: str, tools: List[Dict[str, Any]] = None):
        try:
            # Ensure the messages alternate between "user" and "assistant" roles
            messages = self.ensure_alternating_roles(messages)

            kwargs = {
                "model": self.model,
                "max_tokens": 8000,
                "system": [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                "messages": messages,
                "extra_headers": {"anthropic-beta": "prompt-caching-2024-07-31"}
            }

            if tools:
                kwargs["system"].append({
                    "type": "text",
                    "text": json.dumps(tools),
                    "cache_control": {"type": "ephemeral"}
                })
                kwargs["tools"] = tools
                kwargs["tool_choice"] = {"type": "auto"}

            response = await asyncio.to_thread(
                self.client.beta.prompt_caching.messages.create,
                **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    def ensure_alternating_roles(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alternating_messages = []
        last_role = None
        for message in messages:
            if message['role'] != last_role:
                alternating_messages.append(message)
                last_role = message['role']
            elif message['role'] == 'user':
                # If we encounter consecutive user messages, insert a placeholder assistant message
                alternating_messages.append({"role": "assistant", "content": "Continuing the conversation..."})
                alternating_messages.append(message)
                last_role = 'user'
            # If we encounter consecutive assistant messages, we can safely ignore the duplicates
        return alternating_messages

    async def generate_edit_instructions(self, file_path: str, file_content: str, instructions: str, project_context: str, full_file_contents: Dict[str, str]):
        try:
            messages = [
                {"role": "user", "content": f"Generate edit instructions for the file '{file_path}'. The project context is: {project_context}\n\nHere's the current content of the file:\n\n{file_content}\n\nInstructions for editing:\n{instructions}"}
            ]
            
            response = await self.generate_response(
                messages=messages,
                system_prompt="You are an AI assistant tasked with generating edit instructions. Generate specific edit instructions using <SEARCH> and <REPLACE> tags.",
                tools=[]
            )
            
            edit_instructions = "".join(block.text for block in response.content if block.type == "text")
            return edit_instructions
        except Exception as e:
            raise Exception(f"Error generating edit instructions: {str(e)}")

    def update_code_editor_memory(self, new_memory: str):
        self.code_editor_memory.append(new_memory)
        if len(self.code_editor_memory) > 5:  # Keep only the last 5 memories
            self.code_editor_memory = self.code_editor_memory[-5:]

    def update_code_editor_files(self, file_path: str):
        self.code_editor_files.add(file_path)

    def reset_code_editor_memory(self):
        self.code_editor_memory = []
        self.code_editor_files = set()
