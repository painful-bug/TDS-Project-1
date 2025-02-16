from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
from pprint import pprint
from helpers import request_ai_proxy, get_func_name
import tasks
import json
import os

app = FastAPI()


class TaskRequest(BaseModel):
    task: str


class TaskResponse(BaseModel):
    status: str
    result: Any
    execution_type: str


@app.get("/read")
def read(path: str):
    if os.path.exists(path):
        with open(path, "r") as f:
            return PlainTextResponse(f.read())
    else:
        return "File not found", 404

@app.post("/run")
def run_task(task: str):
    print(f"Received task: {task}")
    answer_json = get_func_name(task)
    print(f"Function name and arguments: {answer_json}")

    # Handle case where no function is found
    if answer_json.get('func_name') is None:
        print("SENDING TO AGENT...")

        # generate_execute()

        return TaskResponse(
            status="success",
            result="No suitable function found for this task",
            execution_type="no_function"
        )

    print(f"Found matching function: {answer_json['func_name']}")
    try:
        func = getattr(tasks, answer_json["func_name"])
        args = answer_json.get("arguments", [])
        if isinstance(args[0], dict):
            args = list(args[0].values())
        print(f"Executing function {answer_json['func_name']} with arguments: {args}")
        result = func(*args)
        try:
            if isinstance(result, str):
                function_info = json.loads(result)
            else:
                function_info = result
            return TaskResponse(
                status="success",
                result=function_info,
                execution_type="function_call"
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=200, detail="Failed to parse AI response")
    except AttributeError:
        raise HTTPException(
            status_code=404,
            detail=f"Function {answer_json['func_name']} not found in tasks module"
        )
    except TypeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid arguments for function {answer_json['func_name']}: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing function {answer_json['func_name']}: {str(e)}"
        )
