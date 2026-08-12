with open("web/static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "highlight" in line.lower() or "window." in line:
        # Clean line for print
        clean = "".join(c for c in line if ord(c) < 128)
        if "_highlight" in clean or "highlightGraph" in clean:
            print(f"Line {i+1}: {clean.strip()[:120]}")
