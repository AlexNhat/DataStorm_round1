from pathlib import Path
text = Path('app/templates/control_center.html').read_text(encoding='utf-8')
start = text.index('<script>')
end = text.rindex('</script>') + 9
print(text[start:end])
