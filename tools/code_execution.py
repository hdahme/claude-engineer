import os
import asyncio
import subprocess
import sys
import signal
import logging
from typing import Dict, Any, Optional
import json

class CodeExecutor:
    def __init__(self, claude_client):
        self.venv_path, self.activate_script = self.setup_virtual_environment()
        self.running_processes: Dict[int, subprocess.Popen] = {}
        self.claude_client = claude_client

    def setup_virtual_environment(self):
        venv_name = "code_execution_env"
        venv_path = os.path.join(os.getcwd(), venv_name)
        try:
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

            # Determine the activation script based on the OS
            if sys.platform == "win32":
                activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
            else:
                activate_script = os.path.join(venv_path, "bin", "activate")

            return venv_path, activate_script
        except Exception as e:
            logging.error(f"Error setting up virtual environment: {str(e)}")
            raise

    async def execute_code(self, code: str) -> Dict[str, Any]:
        try:
            # Create a temporary Python file
            with open("temp_code.py", "w") as f:
                f.write(code)

            # Prepare the command to run the code in the virtual environment
            if sys.platform == "win32":
                cmd = f'cmd /c "{self.activate_script} && python temp_code.py"'
            else:
                cmd = f'source {self.activate_script} && python temp_code.py'

            # Execute the code
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Store the process
            self.running_processes[process.pid] = process

            # Wait for the process to complete or timeout after 60 seconds
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            except asyncio.TimeoutError:
                return {
                    "output": "Execution timed out after 60 seconds.",
                    "error": None,
                    "process_id": process.pid
                }

            # Remove the process from running_processes
            del self.running_processes[process.pid]

            # Remove the temporary file
            os.remove("temp_code.py")

            execution_result = {
                "output": stdout.decode(),
                "error": stderr.decode() if stderr else None,
                "process_id": None  # Process completed, so no need to return ID
            }

            # Analyze the code execution
            analysis = await self.analyze_code_execution(code, execution_result)
            execution_result["analysis"] = analysis

            return execution_result
        except Exception as e:
            logging.error(f"Error executing code: {str(e)}")
            return {"output": None, "error": str(e), "process_id": None, "analysis": None}

    async def analyze_code_execution(self, code: str, execution_result: Dict[str, Any]) -> str:
        messages = [
            {"role": "user", "content": f"Analyze this code execution from the 'code_execution_env' virtual environment:\n\nCode:\n{code}\n\nExecution Result:\n{json.dumps(execution_result, indent=2)}"}
        ]

        try:
            response = await self.claude_client.generate_response(
                messages=messages,
                system_prompt="You are an AI code execution agent. Analyze the provided code and its execution result, then provide a concise summary of what worked, what didn't work, and any important observations.",
                tools=None
            )
            return response.content[0].text if response.content else "No analysis available."
        except Exception as e:
            logging.error(f"Error in AI code execution analysis: {str(e)}")
            return f"Error analyzing code execution: {str(e)}"

    def stop_process(self, process_id: int) -> Dict[str, Any]:
        process = self.running_processes.get(process_id)
        if process:
            try:
                os.kill(process_id, signal.SIGTERM)
                process.wait(timeout=5)  # Wait for up to 5 seconds for the process to terminate
                del self.running_processes[process_id]
                return {"success": True, "message": f"Process {process_id} has been terminated."}
            except subprocess.TimeoutExpired:
                os.kill(process_id, signal.SIGKILL)  # Force kill if it doesn't terminate
                return {"success": True, "message": f"Process {process_id} has been forcefully terminated."}
            except Exception as e:
                return {"success": False, "message": f"Error stopping process {process_id}: {str(e)}"}
        else:
            return {"success": False, "message": f"Process {process_id} not found or already terminated."}

    def install_package(self, package_name: str) -> Dict[str, Any]:
        try:
            if sys.platform == "win32":
                cmd = f'cmd /c "{self.activate_script} && pip install {package_name}"'
            else:
                cmd = f'source {self.activate_script} && pip install {package_name}'

            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return {"success": True, "message": f"Package {package_name} installed successfully.", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Error installing package {package_name}", "error": e.stderr}

    def list_installed_packages(self) -> Dict[str, Any]:
        try:
            if sys.platform == "win32":
                cmd = f'cmd /c "{self.activate_script} && pip list"'
            else:
                cmd = f'source {self.activate_script} && pip list'

            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return {"success": True, "packages": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": "Error listing installed packages", "error": e.stderr}

    def cleanup(self):
        # Terminate all running processes
        for pid in list(self.running_processes.keys()):
            self.stop_process(pid)
