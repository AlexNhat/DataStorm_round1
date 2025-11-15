from pathlib import Path
text = Path("app/templates/base.html").read_text(encoding="utf-8")
for i,line in enumerate(text.splitlines()):
    if '<a href' in line:
        print(i, repr(line))
