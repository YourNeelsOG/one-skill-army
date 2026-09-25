"""Blank out comments and string contents while keeping every position.

The regex extractors match on scrubbed text, so an `import` inside a comment or
a `//` inside a string can never produce an edge. Comment characters become
spaces; string contents become spaces while the quote characters stay, so an
extractor can read a literal (an import path, say) back from the ORIGINAL
source at the same span. Newlines are never touched, so line numbers and
columns in the scrubbed text match the source exactly.
"""


def scrub(source, line=(), block=(), strings=(), raw=()):
    """Return `source` with comments and string contents replaced by spaces.

    line:    line-comment markers, e.g. ["//"]. A "#" marker only counts at
             the start of a word, so shell `$#` and `${#x}` stay code.
    block:   (open, close) pairs, e.g. [("/*", "*/")].
    strings: quote characters that open and close a string.
    raw:     quote characters whose strings have no backslash escapes (Go
             backticks, shell single quotes).
    """
    out = list(source)
    n = len(source)
    i = 0

    def blank(start, end):
        for k in range(start, min(end, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        ch = source[i]
        if ch in strings:
            j = i + 1
            while j < n and source[j] != ch:
                if source[j] == "\\" and ch not in raw:
                    j += 1
                j += 1
            blank(i + 1, j)
            i = j + 1
            continue
        matched = False
        for marker in line:
            if source.startswith(marker, i):
                if marker == "#" and i > 0 and not source[i - 1].isspace():
                    continue
                end = source.find("\n", i)
                end = n if end < 0 else end
                blank(i, end)
                i = end
                matched = True
                break
        if matched:
            continue
        for opener, closer in block:
            if source.startswith(opener, i):
                end = source.find(closer, i + len(opener))
                end = n if end < 0 else end + len(closer)
                blank(i, end)
                i = end
                matched = True
                break
        if not matched:
            i += 1
    return "".join(out)
