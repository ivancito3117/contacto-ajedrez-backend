from tactics_detector import analyze_tactics

# Posición inicial
fen_1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"

# Después de 1.e4 c5 2.Nf3
fen_2 = "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"

# Una posición táctica de ejemplo con pin/hanging potencial
fen_3 = "r2qk2r/ppp2ppp/2n2n2/3bp3/3P4/2N1PN2/PPP2PPP/R1BQ1RK1 w kq - 0 1"

for label, fen in [
    ("Inicial", fen_1),
    ("Siciliana 1.e4 c5 2.Nf3", fen_2),
    ("Ejemplo táctico", fen_3),
]:
    print("=" * 70)
    print(label)
    print(fen)
    result = analyze_tactics(fen)
    print(result)
