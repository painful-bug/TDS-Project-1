import json
from openai import OpenAI
import os
import requests
from prompts import system_prompt
from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import pytesseract
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


BASE_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['AIPROXY_TOKEN']}",
}


def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
    text = int(text.split("\n")[0].replace(' ',''))
    return text


def cosine_sim(embedding1, embedding2):
    return cosine_similarity([embedding1], [embedding2])[0][0]


def request_ai_proxy(payload, debug=False, embedding=False):
    print("REQUESTING AI PROXY...")
    if embedding:
        print("USING EMBEDDINGS")
        BASE_URL = "http://aiproxy.sanand.workers.dev/openai/v1/embeddings"
    else:
        BASE_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    BASE_URL_DEBUG = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['AIPROXY_TOKEN']}",
    }
    if debug == False:
        response = requests.post(BASE_URL, headers=headers, json=payload)
    else:
        response = requests.post(BASE_URL_DEBUG, json=payload)

    if response.status_code == 200:
        result = response.json()
        if debug == True:
            print("USING OLLAMA")
            # For Ollama, directly return the response text
            if isinstance(result, dict) and 'response' in result:
                return result['response']
            return result
        print("USING OPENAI")
        if embedding:
            return result
        return result["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return 500


# def get_func_name(task_descr: str):
#     data = {
#         "model": "gpt-4o-mini",
#         "messages": [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": task_descr},
#         ],
#     }

#     response = json.loads(requests.post(
#         url=BASE_URL, headers=headers, json=data).text)
#     answer = response["choices"][0]["message"]["content"]
#     answer = json.loads(answer)
#     func_name = answer["func_name"]
#     args = answer["arguments"]
#     if args:
#         answer_json = {"func_name": func_name, "arguments": args}
#     else:
#         answer_json = {"func_name": func_name}
#     return answer_json


def get_func_name(task_descr: str):
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_descr},
        ],
    }

    # Make the API call and decode the response as JSON.
    response = requests.post(url=BASE_URL, headers=headers, json=data)
    response_data = response.json()
    answer_str = response_data["choices"][0]["message"]["content"]

    # Remove markdown formatting if present.
    if "```" in answer_str:
        answer_str = answer_str.replace("```json", "")
        answer_str = answer_str.replace("```", "")
    answer_str = answer_str.strip()

    # If the response indicates no function found, return the standard None response
    if "None" in answer_str or answer_str == "{ \"func_name\" : None, \"arguments\" : [] }":
        return {"func_name": None, "arguments": []}

    # Try to parse the JSON response
    try:
        answer = json.loads(answer_str)
        func_name = answer.get("func_name")
        args = answer.get("arguments", [])
        return {"func_name": func_name, "arguments": args}
    except json.JSONDecodeError as e:
        # If JSON parsing fails, check if it's a None response
        if "None" in answer_str:
            return {"func_name": None, "arguments": []}
        # Otherwise, raise the error
        raise ValueError(
            f"Invalid JSON response: {answer_str}\nError: {str(e)}")

# def code_generation_loop_back_cot(task_descr: str):
#     # Initialize variables to track the conversation and code state
#     conversation_history = []
#     max_iterations = 3
#     iteration = 0

#     # Initial system prompt for code generation
#     system_message = {
#         "role": "system",
#         "content": """You are an AI coding assistant that writes robust Python code. Follow these steps:

#     1. Analyze the task requirements carefully
#     2. List any required dependencies/packages needed
#     3. Write clear, well-structured code to accomplish the task
#     4. Include proper error handling and input validation
#     5. If there are errors, debug systematically and suggest fixes

#     Important:
#     - Always specify required pip packages at the start of your response
#     - Use try/except blocks for error handling
#     - Validate inputs and handle edge cases
#     - Follow Python best practices and PEP 8 style

#     Format your response as:
#     DEPENDENCIES:
#     <list required pip packages>

#     CODE:
#     <your Python code>
#     """
#     }

#     conversation_history.append(system_message)
#     conversation_history.append({"role": "user", "content": task_descr})

#     while iteration < max_iterations:
#         # Get code generation response
#         response = request_ai_proxy(
#             payload={
#                 "model": "smallthinker:latest",
#                 "messages": conversation_history
#             },
#             debug=True
#         )

#         if not response:
#             return "Error getting AI response"

#         try:
#             # Parse dependencies and code sections
#             sections = response.split("CODE:")
#             if len(sections) != 2 or "DEPENDENCIES:" not in sections[0]:
#                 raise ValueError("Invalid response format")

#             # Extract dependencies
#             deps = sections[0].replace("DEPENDENCIES:", "").strip().split("\n")
#             deps = [d.strip() for d in deps if d.strip()]

#             # Install dependencies
#             if deps:
#                 print(f"Installing dependencies: {', '.join(deps)}")
#                 for dep in deps:
#                     try:
#                         subprocess.check_call(["pip", "install", dep])
#                     except subprocess.CalledProcessError as e:
#                         return f"Failed to install dependency {dep}: {str(e)}"

#             # Extract and execute code
#             code = sections[1].strip()
#             print("\nGenerated code:")
#             print(code)
#             print("\nExecute code? (y/n)")
#             if input().lower() != "y":
#                 return "Code execution skipped"

#             # Execute in isolated namespace
#             exec_globals = {}
#             exec(code, exec_globals)

#             result = exec_globals.get("output", "Code executed successfully")
#             return {"result": "Success", "output": result}

#         except Exception as e:
#             # error_message = {
#     #                 "role": "user",
#     #                 "content": f"""The code failed with error:
#     # Type: {type(e).__name__}
#     # Message: {str(e)}

#     # Please debug and provide a corrected version that:
#     # 1. Handles this error case
#     # 2. Includes proper error handling
#     # 3. Validates inputs/parameters
#     # """
#     #             }
#     #             conversation_history.append(error_message)
#     #             print(f"Error occurred: {str(e)}")
#     #             print("Retrying with debugging information...")


#         iteration += 1

#     return "Max iterations reached without successful execution"

# # def handle_error():
# #     debug_prompt = {
# #             "role": "user",
# #             "content": f"""Code failed with error:
# #         {error}

# #     Original code:
# #     ```python
# #     {code}

# #     Please:

# #     Analyze the error

# #     Explain the fix

# #     Provide corrected code

# #     Output format:
# #     Analysis: [analysis]
# #     Fix: [explanation]
# #     Code:
# #     [corrected code]


# #     NOTE : Always prefer to perform an action using bash commands if possible. If not, then use Python code.
# #     ```"""
# #         }
# #     history.append(debug_prompt)
# #     return request_ai(history)

# # code_generation_loop_back_cot("Clone the git repo : https://github.com/painful-bug/testing.git and make a commit to it")
