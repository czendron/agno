# 1. IMPORTS =========================================
import requests
import json
import streamlit as st

AGENT_ID = "pdf_agent"
ENDPOINT = f"https://agno-jvrm.onrender.com/agents/{AGENT_ID}/runs"


# 2. AGNO SERVER CONNECTION (SERVER)================
def get_response_stream(message: str):
    response = requests.post(
        url=ENDPOINT,
        data={
            "message": message,
            "stream": "true",
        },
        stream=True             # the 2 "stream" serve for us to see the communication with the agent
    )

# 2.1 STREAMING (processing)======================
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


# 3. STREAMLIT ====================================

st.set_page_config(page_title="Agent Chat <---> PDF")
st.title("Agent-Chat-PDF")

# 3.1 HISTORY ====================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3.2 SHOW HISTORY ====================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("process"):
            with st.expander(label="Process", expanded=False):
                st.json(msg["process"])
        st.markdown(msg["content"])

# 3.3 USER INPUT

# Add user input box for chat
if prompt := st.chat_input("Ask the PDF Agent..."):
    # Append user message to session state (streamlit memory)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display the user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant response and display as streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # streaming processing
        for event in get_response_stream(prompt):
            event_type = event.get("event", "")

            # Tool Call Started            
            if event_type == "ToolCallStarted":
                tool_name = event.get("tool", {}).get("tool_name")
                with st.status(f"Executing {tool_name}...", expanded=True):
                    st.json(event.get("tool", {})).get("tool_args", {})

            # Answer content
            elif event_type == "RunContent":
                content = event.get("content", "")
                if content:
                    full_response += content
                    response_placeholder.markdown(full_response + "| ")

                    
    response_placeholder.markdown(full_response)

    # Saving the session state
    st.session_state.messages.append(
        {
            "role": "assistant", 
            "content": full_response
        }
    )
