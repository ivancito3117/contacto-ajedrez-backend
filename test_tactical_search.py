from pprint import pprint

from tactical_search import analyze_tactical_candidates

ENGINE_PATH = "/home/ivancito820a/proyectos/ajedrez_app/engines/stockfish/stockfish-ubuntu-x86-64"

fen_1 = "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
fen_2 = "r1bqkbnr/pppp1ppp/2n5/4p3/3nP3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 4"

for label, fen in [
    ("Siciliana 1.e4 c5 2.Nf3", fen_1),
    ("Posición táctica de prueba", fen_2),
]:
    print("\n" + "=" * 90)
    print(label)
    print(f"FEN: {fen}\n")
    result = analyze_tactical_candidates(
        fen=fen,
        engine_path=ENGINE_PATH,
        depth=3,
        multipv=5,
    )
    pprint(result, sort_dicts=False)
