from __future__ import annotations

ONES = [
"zero","one","two","three","four","five","six","seven","eight","nine",
"ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"
]
TENS = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]

def _chunk(n: int) -> str:
    out = []
    if n >= 100:
        out.append(ONES[n // 100] + " hundred")
        n %= 100
        if n:
            out.append("and")
    if n >= 20:
        t = TENS[n // 10]
        if n % 10:
            t += "-" + ONES[n % 10]
        out.append(t)
    elif n > 0:
        out.append(ONES[n])
    return " ".join(out)

def int_words(n: int) -> str:
    if n == 0:
        return "zero"
    if n < 0:
        return "minus " + int_words(-n)
    scales = ["", "thousand", "million", "billion"]
    parts = []
    scale = 0
    while n:
        chunk = n % 1000
        if chunk:
            text = _chunk(chunk)
            if scales[scale]:
                text += " " + scales[scale]
            parts.append(text)
        n //= 1000
        scale += 1
    return " ".join(reversed(parts))

def number_words(x) -> str:
    s = str(x)
    if "/" in s:
        return s
    if "." in s:
        neg = s.startswith("-")
        if neg:
            s = s[1:]
        a, b = s.split(".", 1)
        left = int_words(int(a or "0"))
        right = " ".join(ONES[int(ch)] for ch in b if ch.isdigit())
        out = left + " point " + right
        return "minus " + out if neg else out
    return int_words(int(s))

