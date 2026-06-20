#!/usr/bin/env python3
"""Character-level compression for LLM context — zero dependencies.

LLMs understand text with missing characters (Ths cmprssd txt wrks fne).
This strips redundant characters while preserving critical tokens.

Note: Savings are measured in characters. Token-level stats use heuristic
estimation (~4 chars/tok Latin, ~1.5 chars/tok CJK). Install tiktoken for exact counts.

Usage:
  python3 strip_chars.py file.txt -l 2
  cat log.txt | python3 strip_chars.py -l 3 -s
  python3 strip_chars.py file.txt -m -d   # markdown-safe + diff view

Levels:
  1 = Light: remove doubled letters                  (~1-2% savings)
  2 = Medium: + remove interior vowels               (~10% savings)
  3 = Heavy: + truncate long words                   (~13% savings)
  4 = Maximum: + filler removal + dedup              (~15-20% savings)

Auto-preserved: URLs, emails, UUIDs, code blocks (``` fences), phone numbers.
CJK/Non-Latin: automatically skipped at word level.
Use --preserve to protect additional words (case-insensitive).
"""

import argparse
import re
import sys


# --- Preservation patterns ---

PROTECTED = re.compile(
    r'https?://[^\s<>"\']+'
    r'|[\w.+-]+@[\w-]+\.[\w.-]+'
    r'|[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
    r'|[A-Z]{2,}-\d+'           # JIRA-style tickets (ABC-123)
    r'|\+?\d[\d\-(). ]{6,}\d'  # phone numbers
    r'|\b[a-fA-F0-9]{40,}\b'    # hex hashes
)


def _protect_spans(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace protected spans with placeholders, return text + mapping."""
    spans = []
    idx = 0

    def _replacer(m):
        nonlocal idx
        key = f"\x00PROT{idx}\x00"
        idx += 1
        spans.append((key, m.group()))
        return key

    text = PROTECTED.sub(_replacer, text)
    return text, spans


def _restore_spans(text: str, spans: list[tuple[str, str]]) -> str:
    for key, original in spans:
        text = text.replace(key, original)
    return text


# --- Code block protection ---

def _protect_code_blocks(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Protect ``` fenced code blocks from compression."""
    blocks = []
    idx = 0

    def _replacer(m):
        nonlocal idx
        key = f"\x00BLOCK{idx}\x00"
        idx += 1
        blocks.append((key, m.group()))
        return key

    text = re.sub(r'```[\s\S]*?```', _replacer, text)
    return text, blocks


# --- Text protections ---

def _protect_markdown(text: str) -> tuple[str, set[str]]:
    """Extract markdown markers to protect.

    Currently protects: heading # prefixes, horizontal rules.
    Does NOT protect: links, bold/italic markers, tables, blockquotes.
    """
    markers = set()
    for m in re.finditer(r'^(#{1,6})\s+', text, re.MULTILINE):
        markers.add(m.group(1))
    for m in re.finditer(r'^(-{3,}|_{3,}|\*{3,})$', text, re.MULTILINE):
        markers.add(m.group())
    return text, markers


# --- Level 1: Remove doubled letters ---

def _level1(word: str, preserve: set[str]) -> str:
    if not _is_latin(word) or len(word) <= 3:
        return word
    if word.lower() in preserve:
        return word
    result = [word[0]]
    for i in range(1, len(word)):
        if word[i].lower() != word[i - 1].lower():
            result.append(word[i])
    return "".join(result)


# --- Level 2: Remove interior vowels ---

VOWELS = set("aeiouAEIOU")

# Only compress Latin-alphabet words; CJK and other scripts pass through unharmed
_LATIN_WORD = re.compile(r'^[a-zA-Z]+$')

def _is_latin(word: str) -> bool:
    return bool(_LATIN_WORD.match(word))


def _level2(word: str, preserve: set[str]) -> str:
    if not _is_latin(word) or len(word) <= 3:
        return word
    if word.lower() in preserve:
        return word
    if len(word) <= 4:
        return word
    chars = list(word)
    for i in range(1, len(word) - 1):
        if chars[i] in VOWELS:
            chars[i] = ""
    return "".join(chars)


# --- Level 3: Truncate long words ---

def _level3(word: str, preserve: set[str]) -> str:
    if not _is_latin(word) or len(word) <= 6:
        return word
    if word.lower() in preserve:
        return word
    keep_front = min(4, len(word) // 3 + 2)
    keep_back = min(2, max(1, len(word) // 5))
    return word[:keep_front] + word[-keep_back:]


# --- Common filler phrases (Level 4) ---

FILLER_RE = re.compile(
    r'\b(?:note that|it should be noted|interestingly|importantly|'
    r'surprisingly|basically|essentially|literally|'
    r'certainly|definitely|actually|generally|typically|'
    r'please|kindly|well\s)\b[.,]?\s*',
    re.IGNORECASE,
)

FILLER_ZH = re.compile(
    r'(?:值得注意的是|需要指出的是|需要强调的是|可以看到|不难看出|'
    r'众所周知|毫无疑问|毋庸置疑|不可否认|'
    r'也就是说|换句话说|总体来说|整体而言|'
    r'当然|显然|很明显|事实上|实际上|'
    r'在一定程度上|就目前而言)[，,\s]*'
)


def _level4(text: str) -> str:
    """Remove filler phrases and deduplicate lines."""
    text = FILLER_RE.sub("", text)
    text = FILLER_ZH.sub("", text)
    lines = text.split("\n")
    dedup = []
    for line in lines:
        stripped = line.strip()
        if not dedup or dedup[-1].strip() != stripped:
            dedup.append(line)
    return "\n".join(dedup)


# --- Main compression ---

def compress(
    text: str,
    level: int = 2,
    markdown: bool = False,
    preserve_words: set[str] = None,
) -> tuple[str, dict]:
    """Compress text at given level. Returns (compressed_text, stats)."""
    stats = {"original_chars": len(text), "level": level}
    preserve = set(w.lower() for w in (preserve_words or set()))

    # Phase 0: protect code blocks and special spans
    text, code_blocks = _protect_code_blocks(text)
    text, spans = _protect_spans(text)

    if markdown:
        text, md_markers = _protect_markdown(text)
        preserve.update(w.lower() for w in md_markers)

    lines = text.split("\n")
    result_lines = []

    for line in lines:
        marker_match = re.match(r'^(\s*(?:[-*+]|\d+[.)])\s+)', line)
        if marker_match:
            marker = marker_match.group()
            rest = line[marker_match.end():]
        else:
            marker = ""
            rest = line

        words = re.split(r'(\s+)', rest)
        compressed_words = []
        for seg in words:
            if seg.isspace() or not seg:
                compressed_words.append(seg)
            elif seg.lower().strip(".,") in preserve:
                compressed_words.append(seg)
            else:
                compressed_words.append(compress_word(seg, level, preserve))

        result_lines.append(marker + "".join(compressed_words))

    text = "\n".join(result_lines)

    if level >= 4:
        text = _level4(text)

    # Restore protected content
    text = _restore_spans(text, spans)
    for key, block in code_blocks:
        text = text.replace(key, block)

    stats["compressed_chars"] = len(text)
    stats["savings_pct"] = round(
        (1 - len(text) / stats["original_chars"]) * 100, 1
    )

    return text, stats


def compress_word(word: str, level: int, preserve: set[str]) -> str:
    """Apply compression levels to a single word."""
    if level >= 1:
        word = _level1(word, preserve)
    if level >= 2:
        word = _level2(word, preserve)
    if level >= 3:
        word = _level3(word, preserve)
    return word


# --- Token estimation ---

def estimate_tokens(text: str) -> dict:
    """Rough token estimate without external dependencies.

    Heuristic: ~4 chars/token for Latin text, ~1.5 chars/token for CJK.
    Install tiktoken for exact counts.
    """
    cjk = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\uac00-\ud7af]', text))
    latin = len(text) - cjk
    return {
        "estimated_tokens": int(latin / 4 + cjk / 1.5),
        "cjk_chars": cjk,
        "latin_chars": latin,
        "method": "heuristic (~4 chars/tok Latin, ~1.5 chars/tok CJK)",
    }


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Character-level text compression for LLM context"
    )
    parser.add_argument(
        "input", nargs="?", help="Input file (stdin if omitted)"
    )
    parser.add_argument(
        "-l", "--level", type=int, default=2,
        choices=[1, 2, 3, 4],
        help="Compression level (default: 2)"
    )
    parser.add_argument(
        "-m", "--markdown", action="store_true",
        help="Preserve # headings and --- rules (does NOT protect links, bold, tables)"
    )
    parser.add_argument(
        "-p", "--preserve", nargs="*", default=[],
        help="Extra words to preserve (case-insensitive)"
    )
    parser.add_argument(
        "-s", "--stats", action="store_true",
        help="Show compression statistics (char + estimated tokens) on stderr"
    )
    parser.add_argument(
        "-d", "--diff", action="store_true",
        help="Show original vs compressed side by side"
    )
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result, stats = compress(
        text,
        level=args.level,
        markdown=args.markdown,
        preserve_words=set(args.preserve),
    )

    if args.diff:
        print(f"{'─'*40} ORIGINAL {'─'*40}")
        print(text.rstrip())
        print(f"\n{'─'*40} COMPRESSED (-{stats['savings_pct']}%) {'─'*40}")
        print(result)
    else:
        print(result)
    if args.stats:
        tok_orig = estimate_tokens(text)
        tok_comp = estimate_tokens(result)
        print(
            f"Chars: {stats['original_chars']} -> {stats['compressed_chars']} "
            f"(-{stats['savings_pct']}%)",
            file=sys.stderr,
        )
        print(
            f"Tokens (est): {tok_orig['estimated_tokens']} -> "
            f"{tok_comp['estimated_tokens']} "
            f"(-{round((1 - tok_comp['estimated_tokens'] / max(1, tok_orig['estimated_tokens'])) * 100, 1)}%)",
            file=sys.stderr,
        )
        print(
            f"Note: heuristic estimate ({tok_orig['method']}). "
            f"Install tiktoken for exact counts.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
