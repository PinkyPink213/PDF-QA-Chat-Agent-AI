import time
import requests
import gradio as gr

API_BASE = "http://api:8000"


def ask_chat(message, history):
    # 1. Queue the job
    response = requests.post(
        f"{API_BASE}/chat",
        params={"query": message},
        timeout=30,
    )
    response.raise_for_status()

    job_id = response.json()["job_id"]

    # 2. Poll for result
    for _ in range(60):
        status_response = requests.get(
            f"{API_BASE}/job-status",
            params={"job_id": job_id},
            timeout=30,
        )
        status_response.raise_for_status()

        data = status_response.json()
        result = data.get("result")

        if result is not None:
            return result

        time.sleep(1)

    return "The job is still processing. Please try again in a moment."


demo = gr.ChatInterface(
    fn=ask_chat,
    title="PDF QA Chat",
    description="Chat UI connected to your FastAPI backend.",
)

demo.launch(
    server_name="0.0.0.0",
    server_port=7860
)
