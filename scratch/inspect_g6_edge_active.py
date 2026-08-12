with open("web/static/app.js", "r", encoding="utf-8") as f:
    html = f.read()

edge_start = html.find("edge: {")
if edge_start != -1:
    content = html[edge_start:edge_start + 4000]
    for i, line in enumerate(content.splitlines()[:150]):
        print(f"Line {i}: {line}")
else:
    print("Not found")
