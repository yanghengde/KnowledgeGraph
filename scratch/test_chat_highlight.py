import json
import httpx
import asyncio

async def test_chat_highlight():
    url = "http://localhost:5050/api/chat"
    session_id = "test-highlight-session-12345"
    
    # 1. Ask about Workflow
    payload1 = {
        "question": "What is Workflow?",
        "session_id": session_id,
        "product_line": "general",
        "history": []
    }
    
    print("--- TURN 1: Ask about Workflow ---")
    print(f"Payload: {json.dumps(payload1, ensure_ascii=False)}")
    
    full_answer1 = ""
    highlight1 = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload1) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        payload = json.loads(line[6:])
                        if payload["type"] == "chunk":
                            full_answer1 += payload["content"]
                        elif payload["type"] == "done":
                            highlight1 = payload.get("highlight")
                    except Exception:
                        pass
    print(f"Highlight Output 1: {highlight1}")
    if highlight1 and "Workflow" in highlight1.get("nodes", []):
        print("SUCCESS: Correctly highlighted Workflow node!")
    else:
        print("FAILURE: Did not highlight Workflow node.")

    # 2. Ask "What is its relationship with Spec?" (What is its relation to Spec?)
    history = [
        {"role": "user", "content": "What is Workflow?"},
        {"role": "assistant", "content": full_answer1}
    ]
    
    payload2 = {
        "question": "What is its relationship with Spec?",
        "session_id": session_id,
        "product_line": "general",
        "history": history
    }
    
    print("\n--- TURN 2: Ask relationship to Spec ---")
    print(f"Payload: {json.dumps(payload2, ensure_ascii=False)}")
    
    full_answer2 = ""
    highlight2 = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload2) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        payload = json.loads(line[6:])
                        if payload["type"] == "chunk":
                            full_answer2 += payload["content"]
                        elif payload["type"] == "done":
                            highlight2 = payload.get("highlight")
                    except Exception:
                        pass
    print(f"Highlight Output 2: {highlight2}")
    if highlight2 and "Workflow" in highlight2.get("nodes", []) and "Spec" in highlight2.get("nodes", []):
        print("SUCCESS: Correctly highlighted path between Workflow and Spec!")
    else:
        print("FAILURE: Did not highlight path.")

    # 3. Ask "How about Operation?" (No relation keyword, but context has Workflow, Spec, Operation)
    history.append({"role": "user", "content": "What is its relationship with Spec?"})
    history.append({"role": "assistant", "content": full_answer2})

    payload3 = {
        "question": "How about Operation?",
        "session_id": session_id,
        "product_line": "general",
        "history": history
    }
    
    print("\n--- TURN 3: Ask contextually (no relation keyword) about Operation ---")
    print(f"Payload: {json.dumps(payload3, ensure_ascii=False)}")
    
    full_answer3 = ""
    highlight3 = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload3) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        payload = json.loads(line[6:])
                        if payload["type"] == "chunk":
                            full_answer3 += payload["content"]
                        elif payload["type"] == "done":
                            highlight3 = payload.get("highlight")
                    except Exception:
                        pass
    print(f"Highlight Output 3: {highlight3}")
    if highlight3 and len(highlight3.get("edges", [])) > 0:
        print("SUCCESS: Correctly highlighted edges/relationships in multi-turn follow-up!")
    else:
        print("FAILURE: Did not highlight edges in multi-turn follow-up.")

if __name__ == "__main__":
    asyncio.run(test_chat_highlight())
