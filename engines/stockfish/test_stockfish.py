import subprocess

engine = subprocess.Popen(
    ["./stockfish-ubuntu-x86-64"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

engine.stdin.write("uci\n")
engine.stdin.flush()

for _ in range(10):
    print(engine.stdout.readline().strip())

engine.stdin.write("quit\n")
engine.stdin.flush()
