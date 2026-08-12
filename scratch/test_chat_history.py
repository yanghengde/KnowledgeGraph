import json
import httpx
import asyncio

async def test_chat_history():
    url = "http://localhost:5050/api/chat"
    session_id = "test-session-12345"
    
    # 1. First question: Introduce Alice
    payload1 = {
        "question": "你好，我叫Alice。请记住我的名字。",
        "session_id": session_id,
        "product_line": "general",
        "history": []
    }
    
    print("--- FIRST QUESTION ---")
    print(f"Payload: {json.dumps(payload1, ensure_ascii=False)}")
    
    full_answer1 = ""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload1) as response:
            print(f"Status Code: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        payload = json.loads(line[6:])
                        if payload["type"] == "chunk":
                            full_answer1 += payload["content"]
                            print(payload["content"], end="", flush=True)
                    except Exception as e:
                        pass
            print()
    
    # 2. Second question: Ask who I am, passing the history
    history = [
        {"role": "user", "content": "你好，我叫Alice。请记住我的名字。"},
        {"role": "assistant", "content": full_answer1}
    ]
    
    payload2 = {
        "question": "请问我叫什么名字？",
        "session_id": session_id,
        "product_line": "general",
        "history": history
    }
    
    print("\n--- SECOND QUESTION ---")
    print(f"Payload: {json.dumps(payload2, ensure_ascii=False)}")
    
    full_answer2 = ""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload2) as response:
            print(f"Status Code: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        payload = json.loads(line[6:])
                        if payload["type"] == "chunk":
                            full_answer2 += payload["content"]
                            print(payload["content"], end="", flush=True)
                    except Exception as e:
                        pass
            print()
            
    if "Alice" in full_answer2 or "alice" in full_answer2.lower():
        print("\nSUCCESS: The model correctly remembered the name from the history!")
    else:
        print("\nFAILURE: The model did not seem to use the history context.")

if __name__ == "__main__":
    asyncio.run(test_chat_history())
