from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional 
from tools.tools import (
    select_tool,
    available_tools,
    get_weather,
    search_pdf
)
from openai import OpenAI

client = OpenAI()

# ===== STATE =====
class AgentState(TypedDict):
    query: str
    tool: Optional[str]
    tool_input: Optional[str]
    context: Optional[str]
    answer: Optional[str]

# ===== ROUTER =====
def router_node(state: AgentState):
    query = state["query"]

    tool, tool_input = select_tool(query)

    return {
        "query": query,
        "tool": tool,
        "tool_input": tool_input
    }

def tool_node(state: AgentState):
    tool = state.get("tool")
    tool_input = state.get("tool_input")

    if not tool:
        return state

    tool_fn = available_tools.get(tool)

    if not tool_fn:
        return state

    try:
        result = tool_fn(tool_input)
    except Exception:
        result = None

    return {
        **state,
        "context": result
    }



def llm_node(state: AgentState):
    query = state["query"]
    tool = state.get("tool")
    context = state.get("context")

    print(f"🛠 CONTEXT : {context}")
    
    if tool == "search_pdf" and context:
        SYSTEM_PROMPT = f"""
        You are a helpfull AI Assistant who answeres user query based on the available context retrieved from a PDF file along with page_contents and page number.

        Your job is to answer the user's question in a detailed, clear, and educational way using the retrieved PDF context below.

        Instructions:
        - Give direct and complete answers.
        - Explain concepts clearly and naturally.
        - Summarize important information from the PDF.
        - Use examples when helpful.
        - Do NOT simply say where the information is located.
        - If the context contains step-by-step information, explain the steps properly.
        - If the answer is not in the context, say you could not find enough information.

        You should mention page numbers as references after explaining the answer for navigate the user to open the right page number to know more.
        
        Context:
        {context}
        """
    elif tool == "get_weather" and context:
        return {"answer": context}

    else:
        SYSTEM_PROMPT = """
        You are a helpful AI assistant.
        Answer the question normally.
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
    )
    print(f"🤖: {response.choices[0].message.content}")
    return {"answer": response.choices[0].message.content}


graph = StateGraph(AgentState)

graph.add_node("router", router_node)
graph.add_node("tool", tool_node)
graph.add_node("llm", llm_node)

graph.set_entry_point("router")

graph.add_edge("router", "tool")
graph.add_edge("tool", "llm")
graph.add_edge("llm", END)

app_graph = graph.compile()