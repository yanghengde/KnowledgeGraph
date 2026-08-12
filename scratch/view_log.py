import os

log_path = r"C:\Users\yanghe\.gemini\antigravity-ide\brain\be4851d4-53dd-4bcd-b4ed-9253bf4d3c9f\.system_generated\tasks\task-5489.log"

if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    print("--- LOG CONTENT ---")
    # Clean non-ascii for safe console printing
    clean_content = "".join(c for c in content if ord(c) < 128 or c in '\n\r\t')
    print(clean_content)
else:
    print("Log file not found yet.")
