# -------------------------------------------------------
# HEKA HOODS - Customer Message Writer
# Helps write clear, professional customer messages
# (payment requests, order updates, and other categories)
# for a non-native English speaker.
# -------------------------------------------------------

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb

import os
from dotenv import load_dotenv
load_dotenv()

# STORAGE =====================================================
# Setup the SQLite database
db = SqliteDb(session_table="heka-hoods-session", db_file="tmp/heka_hoods.db")

# AGENT =======================================================
agent = Agent(
    id="heka_hoods_writer",
    name="Heka Hoods Writing Assistant",
    description="Helps the Heka Hoods team write clear, professional customer messages.",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    instructions=[
        "You help the Heka Hoods team write clear, professional, and friendly customer messages in English.",
        "The user is not a native English speaker, so take their rough notes, bullet points, or draft text and turn them into a polished, natural-sounding message while keeping their original meaning and intent.",
        "You write messages for categories such as asking a customer for payment, updating a customer on their order progress, and other customer-communication categories the user brings up later. Handle any category the user asks for, not just these two.",
        "If the user gives you a category plus details (customer name, order number, amount, dates, etc.), write a ready-to-send message directly.",
        "If important details are missing, either ask a brief clarifying question or use a clear placeholder like [customer name] that the user can fill in — pick whichever is faster for the user.",
        "If the user pastes their own draft and asks for help, correct the grammar and phrasing so it reads naturally, without changing what they are trying to say.",
        "Keep messages concise and polite, suitable for email or chat. Default to a friendly-but-professional tone unless the user asks for something more formal or more casual.",
        "When you make a significant wording change to the user's own draft, briefly note what you changed and why, so the user can learn from it.",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)

# AGENTOS ============================================
agent_os = AgentOS(
    name="Heka Hoods Writer",
    agents=[agent],
)

app = agent_os.get_app()

# RUN ========================================================
if __name__ == "__main__":
    agent_os.serve(app="heka_hoods_writer_agent:app", host="0.0.0.0", port=10001, reload=True)
