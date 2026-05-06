from graph.agent_graph import app_graph
from dotenv import load_dotenv

load_dotenv()

def process_query(query: str):

    print("🔥 PROCESS START")

    result = app_graph.invoke({
        "query": query
    })

    print("✅ PROCESS DONE")

    return result["answer"]





