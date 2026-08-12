with open("web/static/app.js", "r", encoding="utf-8") as f:
    html = f.read()

# Search for stroke or dash arrays or colors used for active vs inactive edges
for i, line in enumerate(html.splitlines()):
    if "stroke" in line or "lineWidth" in line or "dashed" in line or "lineDash" in line:
        clean = "".join(c for c in line if ord(c) < 128)
        if any(k in clean.lower() for k in ["active", "inactive", "edge", "style", "rgba", "0xff"]):
            print(f"Line {i+1}: {clean.strip()[:120]}")
