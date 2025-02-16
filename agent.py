import subprocess
import re
import os
import json
from dotenv import load_dotenv
from helpers import request_ai_proxy

load_dotenv()

MAX_TRIES = 3

class AIAgent:
    def __init__(self, debug=False):
        self.history = []
        self.payload = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "messages": self.history
        }
        self.debug = debug

    def refresh_payload(self):
        self.payload = {
            "model": "gpt-4o-mini",
            "messages": self.history
        }

    def generate_initial_prompt(self, task):
        return [
            {"role": "system", "content": f"""You are an AI programming assistant that follows this strict workflow:
1. Task Analysis - Understand the task requirements
2. Environment Preparation - Identify required tools/packages and install them
3. Code Generation - Write executable Python code
4. Error Correction - If errors occur, analyze and fix the code
5. Iterate - Repeat until the task is completed

Current Task: {task}

Please generate the complete code to accomplish the task. Always prefer to perform actions using bash commands using the `subprocess` module in Python if possible. If not, then use other Python code. Always return some code. Never return a blank/null response, also never leave any placeholder in the code. Always replace the placeholder values with actual values before running the code.
For tasks that require mouse and keyboard access, use pyautogui to perform them
Additionally, if any Python packages are required, please list them in the response and also install them by running pip install commands using subprocess.
"""}
        ]

    def extract_code_and_packages_from_response(self, response):
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        packages_match = re.search(r'Packages: (.*?)\n', response, re.DOTALL)
        code = code_match.group(1).strip() if code_match else None
        packages = packages_match.group(1).strip().split(', ') if packages_match else []
        return code, packages

    def install_packages(self, packages):
        if not packages:
            return True
        try:
            subprocess.run(['pip', 'install'] + packages, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            return False

    def execute_code(self, code):
        try:
            result = subprocess.run(['python3', '-c', code],
                                    capture_output=True,
                                    text=True,
                                    check=True)
            return {
                "success": True,
                "output": result.stdout,
                "error": None
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": None,
                "error": f"{e.stderr}\nExit code: {e.returncode}"
            }

    def handle_error(self, code, error):
        debug_prompt = {
            "role": "user",
            "content": f"""Code failed with error: {error}
Original code: ```python {code} ```

Please:
1. Analyze the error in detail.
2. Explain the fix.
3. Provide corrected code.

Context:
- The code was intended to: [describe the intended action of the code]
- The error occurred during: [describe the context or action when the error happened]

Output format:
Analysis: [analysis of the error]
Fix: [explanation of the fix]
Code: [corrected code]

NOTE: Always prefer to perform actions using bash commands if possible. If not, then use Python code.
"""
        }
        self.history.append(debug_prompt)
        self.refresh_payload()
        return request_ai_proxy(self.payload)

    def run_task(self, task):
        self.history = self.generate_initial_prompt(task)
        self.refresh_payload()
        response = request_ai_proxy(self.payload)
        print("Initial response:\n", response)
        tries_count = 0

        while tries_count < MAX_TRIES:
            code, packages = self.extract_code_and_packages_from_response(response)
            if not code:
                raise ValueError("No code found in AI response")

            if not self.install_packages(packages):
                print("Failed to install required packages. Exiting.")
                return "Failed to install required packages."

            execution_result = self.execute_code(code)

            if execution_result['success']:
                print("Task completed successfully!")
                print(f"Output: {execution_result['output']}")
                break
            else:
                print(f"Error in task execution:")
                print(execution_result['error'])
                debug_response = self.handle_error(code, execution_result['error'])
                print("\nDebugging response:")
                print(debug_response)
                response = debug_response
                self.history.append({"role": "assistant", "content": debug_response})
                self.refresh_payload()
                tries_count += 1

        if tries_count == MAX_TRIES:
            print("Maximum number of retries reached. Task could not be completed successfully.")
            return "Task failed after several retries."

        return "Task completed successfully!"
    

# if __name__ == "__main__":
#     agent = AIAgent()
#     agent.run_task("sort the contacts alphabetically from ./data/contacts.json and save the sorted contacts inside ./data/sorted-contacts-agent.json")
#     # agent.run_task("open a web browser and go to youtube and search for 'hello by adele' and play the video by clicking on it")