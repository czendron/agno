# IMPORTS =========================================
import requests
import json
from pprint import pprint


AGENT_ID = "pdf_agent"
ENDPOINT = f"http://localhost:7777/agents/{AGENT_ID}/runs"


# AGNO SERVER CONNECTION (SERVER)================
def get_response_stream(message: str):
    response = requests.post(
        url=ENDPOINT,
        data={
            "message": message,
            "stream": "true",
        },
        stream=True             # the 2 "stream" serve for us to see the communication with the agent
    )

# STREAMING (processing)======================
    for line in response.iter_lines():
        if line:
            # Parse Server-Sent Events
            if line.startswith(b'data: '):
                data = line[6:]  # removes 'data: ' prefix
                try:
                    event = json.loads(data)
                    yield event
                except json.JSONDecodeError:
                    continue


# STREAMLIT ====================================




# PRINT ANSWER =================================
def print_streaming_response(message: str):
    for event in get_response_stream(message):
        event_type = event.get("event", "")
        
        # Start execution
        if event_type == "RunStarted":
            print("[Run started]")
            print("="*50)
        
        # Answer content
        elif event_type == "RunContent":
            content = event.get("content", "")
            if content:
                print(content, end="", flush=True)

        # Tool call started
        if event_type == "ToolCallStarted":
            tool = event.get("tool", {})
            tool_name = tool.get("tool_name", "Unknown")
            tool_args = tool.get("tool_args", {})
            print(f"TOOL STARTED: {tool_name}")
            print(f"Args: {json.dumps(tool_args, indent=2)}")
            print("="*50)
        elif event_type =="ToolCallCompleted":
            print(f"Tool Completed: {tool_name}")
            print("="*50)

        elif event_type == "RunCompleted":
            print("Execution Completed!!!")
            metrics = event.get("metrics", {})
            if metrics:
                print(f"METRICS: {json.dumps(metrics, indent=2)}")


# RUN ===========================================

if __name__ == "__main__":
    message = input("Insert here your message, Master: ")
    print_streaming_response(message)

    while True:
        message = input("Master, insert your message here: ")
        print_streaming_response(message)
