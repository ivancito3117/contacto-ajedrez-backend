from pathlib import Path

p = Path("/home/ivancito820a/proyectos/ajedrez_app/chessdb/hhdbvi.pgn")

stack = []
line_num = 0

in_tag = False
in_quote = False

with p.open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line_num += 1
        i = 0
        while i < len(line):
            ch = line[i]

            # inicio de tag PGN
            if not in_quote and ch == '[':
                in_tag = True

            # fin de tag PGN
            elif not in_quote and ch == ']':
                in_tag = False

            # comillas dentro del tag
            elif in_tag and ch == '"':
                in_quote = not in_quote

            # contar llaves SOLO fuera de tags
            elif not in_tag:
                if ch == '{':
                    stack.append(line_num)
                elif ch == '}':
                    if stack:
                        stack.pop()
                    else:
                        print(f"EXTRA_CLOSING_BRACE at line {line_num}")

            i += 1

print("TOTAL_UNCLOSED_OPENING_BRACES =", len(stack))
print("FIRST_50_UNCLOSED_OPENING_LINES =")
for n in stack[:50]:
    print(n)
