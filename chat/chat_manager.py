import asyncio
import os
import json
import traceback
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from .conversation import Conversation
from models.claude_client import ClaudeClient
from models.tavily_client import TavilyClient
from tools.file_operations import FileOperations
from tools.code_execution import CodeExecutor
from tools.image_processing import ImageProcessor
from utils.console_utils import (
    get_user_input, display_assistant_response, display_code,
    display_error, display_info, display_success,
    display_file_contents, display_tool_result,
    confirm_action, clear_console, display_welcome_message
)
from utils.token_tracker import TokenTracker
from utils.config import Config

class ChatManager:
    def __init__(self):
        self.console = Console()
        self.conversation = Conversation()
        self.config = Config()
        self.claude_client = ClaudeClient(self.config)
        self.tavily_client = TavilyClient(self.config)
        self.file_ops = FileOperations()
        self.code_executor = CodeExecutor(self.claude_client)
        self.image_processor = ImageProcessor()
        self.token_tracker = TokenTracker()
        self.automode = False
        display_welcome_message()

    async def run(self):
        try:
            while True:
                user_input = await get_user_input()

                if user_input.lower() == 'exit':
                    display_info("Thank you for chatting. Goodbye!")
                    break

                if user_input.lower() == 'reset':
                    if await confirm_action("Are you sure you want to reset the conversation?"):
                        self.reset_conversation()
                        display_success("Conversation has been reset.")
                    continue

                if user_input.lower() == 'save chat':
                    self.save_chat()
                    continue

                if user_input.lower() == 'image':
                    await self.handle_image_input()
                elif user_input.lower().startswith('automode'):
                    await self.handle_automode(user_input)
                else:
                    await self.handle_regular_chat(user_input)

                # self.token_tracker.display_token_usage()
        finally:
            await self.cleanup()

    def reset_conversation(self):
        self.conversation.reset()
        self.token_tracker.reset()
        self.file_ops.reset_file_contents()
        self.claude_client.reset_code_editor_memory()
        self.code_executor.reset()
        display_success("Conversation history, token counts, file contents, code editor memory, and code editor files have been reset.")
        self.token_tracker.display_token_usage()
        clear_console()
        display_welcome_message()

    def save_chat(self):
        filename = self.conversation.save_to_file()
        display_success(f"Chat saved to {filename}")

    async def handle_image_input(self):
        image_path = (await get_user_input("Drag and drop your image here, then press enter: ")).strip().replace("'", "")

        if os.path.isfile(image_path):
            image_metadata = self.image_processor.get_image_metadata(image_path)
            if image_metadata:
                display_info(f"Image metadata: {json.dumps(image_metadata, indent=2)}")
            
            user_input = await get_user_input("You (prompt for image): ")
            response, _ = await self.chat_with_claude(user_input, image_path)
            display_assistant_response(response)
        else:
            display_error("Invalid image path. Please try again.")

    async def handle_automode(self, user_input):
        try:
            parts = user_input.split()
            max_iterations = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else self.config.MAX_CONTINUATION_ITERATIONS

            self.automode = True
            display_info(f"Entering automode with {max_iterations} iterations. Please provide the goal of the automode.")
            display_info("Press Ctrl+C at any time to exit the automode loop.")
            user_input = await get_user_input()

            iteration_count = 0
            error_count = 0
            max_errors = 3

            try:
                while self.automode and iteration_count < max_iterations:
                    try:
                        response, exit_continuation = await self.chat_with_claude(user_input, current_iteration=iteration_count+1, max_iterations=max_iterations)
                        error_count = 0
                    except Exception as e:
                        display_error(f"Error in automode iteration: {str(e)}")
                        error_count += 1
                        if error_count >= max_errors:
                            display_error(f"Exiting automode due to {max_errors} consecutive errors.")
                            self.automode = False
                            break
                        continue

                    if exit_continuation or self.config.CONTINUATION_EXIT_PHRASE in response:
                        display_success("Automode completed.")
                        self.automode = False
                    else:
                        display_info(f"Continuation iteration {iteration_count + 1} completed. Press Ctrl+C to exit automode. ")
                        user_input = "Continue with the next step. Or STOP by saying 'AUTOMODE_COMPLETE' if you think you've achieved the results established in the original request."
                    iteration_count += 1

                    if iteration_count >= max_iterations:
                        display_error("Max iterations reached. Exiting automode.")
                        self.automode = False
            except KeyboardInterrupt:
                display_error("\nAutomode interrupted by user. Exiting automode.")
                self.automode = False
                self.conversation.add_message("assistant", "Automode interrupted. How can I assist you further?")
        except KeyboardInterrupt:
            display_error("\nAutomode interrupted by user. Exiting automode.")
            self.automode = False
            self.conversation.add_message("assistant", "Automode interrupted. How can I assist you further?")

        display_success("Exited automode. Returning to regular chat.")

    async def handle_regular_chat(self, user_input):
        response, _ = await self.chat_with_claude(user_input)
        display_assistant_response(response)

    async def chat_with_claude(self, user_input, image_path=None, current_iteration=None, max_iterations=None):
        current_conversation = []

        if image_path:
            display_info(f"Processing image at path: {image_path}")
            image_data = self.image_processor.encode_image_to_base64(image_path)
            if image_data:
                image_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_data["mime_type"],
                                "data": image_data["base64_image"]
                            }
                        },
                        {
                            "type": "text",
                            "text": f"User input for image: {user_input}"
                        }
                    ]
                }
                current_conversation.append(image_message)
                self.conversation.add_message("user", image_message["content"])
                display_success("Image message added to conversation history")
            else:
                return "Error processing the image. Please try again with a different image.", False
        else:
            user_message = {"role": "user", "content": user_input}
            current_conversation.append(user_message)
            self.conversation.add_message("user", user_input)

        filtered_conversation_history = self.conversation.filter_history()
        
        # Ensure roles alternate
        messages = self.ensure_alternating_roles(filtered_conversation_history + current_conversation)

        try:
            response = await self.claude_client.generate_response(
                messages=messages,
                system_prompt=self.config.update_system_prompt(current_iteration, max_iterations),
                tools=self.config.tools  # Always pass the tools, Claude will decide whether to use them
            )
            self.token_tracker.update_token_usage('main_model', response.usage.input_tokens, response.usage.output_tokens)
        except Exception as e:
            error_message = f"Error communicating with the AI: {str(e)}"
            display_error(error_message)
            traceback.print_exc()
            return error_message, False

        assistant_response = ""
        exit_continuation = False
        tool_uses = []

        for content_block in response.content:
            if content_block.type == "text":
                assistant_response += content_block.text
                if self.config.CONTINUATION_EXIT_PHRASE in content_block.text:
                    exit_continuation = True
            elif content_block.type == "tool_use":
                tool_uses.append(content_block)

        display_assistant_response(assistant_response)

        self.file_ops.display_files_in_context()

        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            tool_use_id = tool_use.id

            display_info(f"Tool Used: {tool_name}")
            display_info(f"Tool Input: {json.dumps(tool_input, indent=2)}")

            if tool_name == 'create_files':
                tool_result = self.file_ops.create_files(tool_input.get('files', [tool_input]))
            elif tool_name == 'tavily_search':
                tool_result = await self.tavily_client.search(tool_input['query'])
            else:
                tool_result = await self.execute_tool(tool_name, tool_input)

            if isinstance(tool_result, dict) and tool_result.get("is_error"):
                display_error(tool_result["content"])
            else:
                formatted_result = json.dumps(tool_result, indent=2) if isinstance(tool_result, (dict, list)) else str(tool_result)
                display_tool_result(tool_name, formatted_result)

            current_conversation.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": tool_use_id,
                        "name": tool_name,
                        "input": tool_input
                    }
                ]
            })

            tool_result_content = {
                "type": "text",
                "text": json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
            }

            current_conversation.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": [tool_result_content],
                        "is_error": tool_result.get("is_error", False) if isinstance(tool_result, dict) else False
                    }
                ]
            })

            self.file_ops.update_file_contents(tool_name, tool_input)

            messages = filtered_conversation_history + current_conversation

            try:
                tool_response = await self.claude_client.generate_response(
                    messages=messages,
                    system_prompt=self.config.update_system_prompt(current_iteration, max_iterations),
                    tools=self.config.tools
                )
                self.token_tracker.update_token_usage('tool_checker', tool_response.usage.input_tokens, tool_response.usage.output_tokens)

                tool_checker_response = "".join(block.text for block in tool_response.content if block.type == "text")
                # display_assistant_response(tool_checker_response)
                assistant_response += "\n\n" + tool_checker_response

                if tool_name == 'edit_and_apply_multiple':
                    retry_decision = await self.decide_retry(tool_checker_response, tool_result)
                    if retry_decision["retry"]:
                        display_info(f"AI has decided to retry editing for files: {', '.join(retry_decision['files_to_retry'])}")
                        retry_files = [file for file in tool_input['files'] if file['path'] in retry_decision['files_to_retry']]
                        retry_result, retry_console_output = await self.file_ops.edit_and_apply_multiple(retry_files, tool_input['project_context'])
                        display_info(retry_console_output)
                        assistant_response += f"\n\nRetry result: {json.dumps(retry_result, indent=2)}"
                    else:
                        display_success("Claude has decided not to retry editing")

            except Exception as e:
                error_message = f"Error in tool response: {str(e)}"
                display_error(error_message)
                assistant_response += f"\n\n{error_message}"

        if assistant_response:
            messages.append({"role": "assistant", "content": assistant_response})
            # self.conversation.add_message("assistant", assistant_response)

            conversation_history = messages

        self.token_tracker.display_token_usage()

        return assistant_response, exit_continuation

    async def execute_tool(self, tool_name, tool_input):
        try:
            if tool_name == 'create_folders':
                return self.file_ops.create_folders(tool_input['paths'])
            elif tool_name == 'edit_and_apply_multiple':
                return await self.file_ops.edit_and_apply_multiple(tool_input['files'], tool_input['project_context'])
            elif tool_name == 'execute_code':
                return await self.code_executor.execute_code(tool_input['code'])
            elif tool_name == 'stop_process':
                return self.code_executor.stop_process(tool_input['process_id'])
            elif tool_name == 'read_multiple_files':
                return self.file_ops.read_multiple_files(tool_input['paths'])
            elif tool_name == 'list_files':
                return self.file_ops.list_files(tool_input.get('path', './_generations'))
            elif tool_name == 'execute_code':
                return await self.code_executor.execute_code(tool_input['code'])
            else:
                return {"is_error": True, "content": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"is_error": True, "content": f"Error executing {tool_name}: {str(e)}"}

    async def decide_retry(self, tool_checker_response, edit_results):
        retry_decision = {
            "retry": False,
            "files_to_retry": []
        }

        errors_present = any(result.get("is_error", False) for result in edit_results)

        retry_phrases = [
            "need to retry",
            "should try again",
            "another attempt is necessary",
            "errors that need addressing",
            "requires further editing"
        ]

        if errors_present or any(phrase in tool_checker_response.lower() for phrase in retry_phrases):
            retry_decision["retry"] = True

            file_paths = re.findall(r"(?:retry|edit again|fix).*?['\"](.*?)['\"]", tool_checker_response, re.IGNORECASE)
            retry_decision["files_to_retry"] = list(set(file_paths))

            if not retry_decision["files_to_retry"]:
                retry_decision["files_to_retry"] = [result["path"] for result in edit_results if "path" in result]

        if retry_decision["retry"]:
            display_info(f"Decided to retry editing for files: {', '.join(retry_decision['files_to_retry'])}")
        else:
            display_success("No retry needed")

        return retry_decision

    async def cleanup(self):
        """Perform cleanup operations before shutting down."""
        self.code_executor.cleanup()
        # Add any other cleanup operations here

    def ensure_alternating_roles(self, messages):
        """Ensure that roles alternate between 'user' and 'assistant'."""
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
