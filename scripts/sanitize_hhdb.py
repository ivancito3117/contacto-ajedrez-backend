from pathlib import Path

src = Path("/home/ivancito820a/proyectos/ajedrez_app/chessdb/hhdbvi.pgn")
dst = Path("/home/ivancito820a/proyectos/ajedrez_app/chessdb/hhdbvi_clean.pgn")

text = src.read_text(encoding="utf-8", errors="replace")

out = []
in_tag = False
in_quote = False
in_comment = False

i = 0
while i < len(text):
    ch = text[i]

    # Manejo de tags PGN [ ... " ... " ... ]
    if not in_comment:
        if not in_quote and ch == '[':
            in_tag = True
            out.append(ch)
            i += 1
            continue
        if in_tag and ch == '"':
            in_quote = not in_quote
            out.append(ch)
            i += 1
            continue
        if in_tag and not in_quote and ch == ']':
            in_tag = False
            out.append(ch)
            i += 1
            continue

    # Fuera de tags: manejo de comentarios
    if not in_tag:
        if ch == '{':
            if in_comment:
                # llave anidada dentro de comentario -> convertir a paréntesis
                out.append('(')
            else:
                in_comment = True
                out.append('{')
            i += 1
            continue

        if ch == '}':
            if in_comment:
                in_comment = False
                out.append('}')
            else:
                # cierre suelto fuera de comentario -> convertir a paréntesis
                out.append(')')
            i += 1
            continue

    # Si aparece un nuevo juego y seguimos dentro de comentario, ciérralo
    if in_comment and text.startswith('\n[Event ', i):
        out.append('}')
        in_comment = False

    out.append(ch)
    i += 1

# Si el archivo termina con comentario abierto, ciérralo
if in_comment:
    out.append('}')

dst.write_text(''.join(out), encoding="utf-8")
print(f"Archivo saneado creado en: {dst}")
