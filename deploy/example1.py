from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

from agno.vectordb.chroma import ChromaDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.semantic import SemanticChunking
from agno.knowledge.embedder.openai import OpenAIEmbedder

from fastapi import FastAPI
import uvicorn
import asyncio

import os
from dotenv import load_dotenv
load_dotenv()

# STORAGE =====================================================
# Setup the SQLite database
db = SqliteDb(session_table="agent-session", db_file="tmp/data.db")

# RAG =========================================================
# Initialise ChromaDB
vector_db = ChromaDb(
    collection="pdf_agent",
    path="tmp/chromadb",
    embedder=OpenAIEmbedder(id="text-embedding-3-small", api_key=os.getenv("OPENAI_API_KEY")),
    persistent_client=True,
)

# Create a knowledge base
knowledge = Knowledge(
    vector_db=vector_db,
)

# knowledge.add_content(
#     path="files/commonwealth/", # the path can be an URL
#     reader=PDFReader(
#         chunking_strategy=SemanticChunking(), # other strategies can be used
#         ignore_encryption=True
#     ),
#     metadata={                          # this is not mandatory, but adding this info helps the model
#         "company": "Commonwealth",
#         "sector": "banking",
#         "country": "Australia", 
#     },
#     skip_if_exists=True # important, so the model dont do the chunking and embedding again, if it has already been done. And this process is costly.
# )




agent = Agent(
    name="PDF Agent",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    instructions="",
    db=db,
    knowledge=knowledge,
    add_history_to_context=True,
    num_history_runs=3,
    enable_user_memories=True, # This enables Memory for the Agent
    add_memories_to_context=True, # This adds the memory to the context
    enable_agentic_memory=True,
    add_knowledge_to_context=True,
    search_knowledge=True,
    debug_mode=True,
)

# FASTAPI ============================================
app = FastAPI(title="PDF Agent", description="API to answer questions about PDFs.")


@app.post("/agent_pdf")
def agent_pdf(question: str):
    response = agent.run(question)
    message = response.messages[-1]
    return {"message": message.content}

# RUN ========================================================
if __name__ == "__main__":
    asyncio.run(knowledge.add_content_async(
        url="https://dealroom.co/uploaded/2025/06/Dealroom-Australia-report-2025.pdf?x95901",
        metadata={"source": "Dealroom", "type": "pdf", "description": "Australia Venture & Startup Record"},
        skip_if_exists=True,
        reader=PDFReader(),
    ))
    uvicorn.run("example1:app", host="0.0.0.0", port=8000, reload=True)
