from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

import requests
from pydantic import BaseModel
from typing import Optional

load_dotenv()

openai_client = OpenAI()

def get_vector_db():

    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )

    vector_db = QdrantVectorStore.from_existing_collection(
        url="http://vector-db:6333",
        collection_name="learning_rag",
        embedding=embedding_model,
    )

    return vector_db

def get_weather(city: str):

    url = f"https://wttr.in/{city.lower()}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}"

    return "Something went wrong"


def query_expansion(query: str):
    SYSTEM_PROMPT = f"""
    Generate exactly 3 diverse search queries similar to the user query.

    Rules:
    - Same language as the user query
    - Each query on a new line
    - No numbering or explanation
    - Use different wording or synonyms

    User query: {query}
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
    )

    result = response.choices[0].message.content.strip()

    queries = [q.strip() for q in result.split("\n") if q.strip()]

    # deduplicate + keep original
    queries = list(set(queries + [query]))

    return queries

def search_pdf(query: str):

    # 1. expand query
    queries = query_expansion(query)
    vector_db = get_vector_db()

    all_results = []

    # 2. MMR Retrieval
    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 3,
            "fetch_k": 10,
            "lambda_mult": 0.5
        }
    )

    for q in queries:
        results = retriever.invoke(q)
        all_results.extend(results)

    # 3. deduplicate
    unique_docs = {}

    for doc in all_results:
        unique_docs[doc.page_content] = doc

    docs = list(unique_docs.values())

    if not docs:
        return "No relevant content found."

    # 4. top docs
    final_docs = docs[:3]

    # 5. build context
    context = "\n\n\n".join([
        f"""
        Page Content: {doc.page_content}
        Page Number: {doc.metadata['page_label']}
        File Location: {doc.metadata['source']}
        """
        for doc in final_docs
    ])

    return context



class ToolSelection(BaseModel):
    tool: Optional[str] = None
    input: Optional[str] = None


TOOL_PROMPT = """
You are a tool selector AI.

Your job is to decide whether a tool is needed.

Rules:
- If the query is about weather → use get_weather
- If the query is about documents, knowledge, explanation, or PDF about Node.js → use search_pdf
- Otherwise → do not use any tool

Return ONLY JSON.

Format:
{ "tool": "get_weather" | "search_pdf" | null, "input": "string" }

Examples:

User: What is the weather in Bangkok?
{ "tool": "get_weather", "input": "bangkok" }

User: Summerize chapter 3
{ "tool": "search_pdf", "input": "chapter 3" }

User: 2 + 2
{ "tool": null, "input": null }
"""


def select_tool(query: str):

    response = openai_client.chat.completions.parse(
        model="gpt-4o-mini",
        response_format=ToolSelection,
        messages=[
            {"role": "system", "content": TOOL_PROMPT},
            {"role": "user", "content": query}
        ]
    )

    parsed = response.choices[0].message.parsed
    
    print(f"🛠 PARSED RESULT: {parsed}")
    print(f"🛠 SELECTED TOOL: {parsed.tool}")
    
    if parsed.tool not in ["get_weather", "search_pdf"]:
        return None, None

    if not parsed.input:
        parsed.input = query
    return parsed.tool, parsed.input

available_tools = {
    "get_weather": get_weather,
    "search_pdf": search_pdf
}