#!/usr/bin/env python3
"""Strip filler phrases — pure regex, zero dependencies.

Usage: cat doc.txt | python3 strip_fillers.py
       python3 strip_fillers.py file.txt
"""

import re
import sys
from typing import Tuple

# Patterns to strip — add more as needed
FILLERS_ZH = [
    r'值得注意的是[,，]?\s*',
    r'需要指出的是[,，]?\s*',
    r'需要强调的是[,，]?\s*',
    r'综上所述[,，]?\s*',
    r'总而言之[,，]?\s*',
    r'总[的而]言之[,，]?\s*',
    r'我们可以看到[,，]?\s*',
    r'可以看出[,，]?\s*',
    r'由此可见[,，]?\s*',
    r'换句话说[,，]?\s*',
    r'也就是说[,，]?\s*',
    r'事实上[,，]?\s*',
    r'实际上[,，]?\s*',
    r'在一定程度上[,，]?\s*',
    r'从某种意义[上来]说[,，]?\s*',
    r'毋庸置疑[,，]?\s*',
    r'众所周知[,，]?\s*',
    r'毫无疑问[,，]?\s*',
    r'不可否认[,，]?\s*',
    r'不难看出[,，]?\s*',
    r'不难发现[,，]?\s*',
    r'显然[,，]?\s*',
    r'很明显[,，]?\s*',
    r'总体来说[,，]?\s*',
    r'整体而言[,，]?\s*',
    r'就目前而言[,，]?\s*',
    r'就现阶段来说[,，]?\s*',
]

FILLERS_EN = [
    r'\bIt is (worth|important|essential|necessary|crucial|vital) '
    r'(noting|to note|mentioning|to mention|to remember|to keep in mind)\b\.?\s*',
    r'\bIt (should|cannot|must) be (noted|mentioned|emphasized|stressed) that\b\.?\s*',
    r'\bIn (conclusion|summary|other words|short|brief|essence|a nutshell)\b[,]?\s*',
    r'\bTo sum up\b[,]?\s*',
    r'\bAs (mentioned|noted|discussed|stated|indicated) '
    r'(above|earlier|previously|before)\b[,]?\s*',
    r'\bNeedless to say\b[,]?\s*',
    r'\bIt goes without saying that\b\s*',
    r'\bThat being said\b[,]?\s*',
    r'\bAt the end of the day\b[,]?\s*',
    r'\bWhen (it comes to|all is said and done)\b[,]?\s*',
    r'\bGenerally speaking\b[,]?\s*',
    r'\bBroadly speaking\b[,]?\s*',
    r"\bFor what it[']s worth\b[,]?\s*",
    r'\bTo a (certain|large|great|some) extent\b[,]?\s*',
    r'\bIt is (clear|obvious|apparent|evident) that\b\.?\s*',
    r'\bI would (like to|argue that|suggest that)\b\.?\s*',
    r'\bIt should be noted that\b\.?\s*',
]


def compress(text: str) -> Tuple[str, int]:
    """Strip fillers, return (compressed_text, removed_count)."""
    removed = 0
    for pattern in FILLERS_ZH + FILLERS_EN:
        count_before = len(re.findall(pattern, text, flags=re.IGNORECASE))
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        removed += count_before

    # Collapse 3+ blank lines → 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing whitespace per line
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    # Collapse 3+ spaces
    text = re.sub(r' {3,}', '  ', text)

    return text.strip(), removed


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result, removed = compress(text)
    print(result)
    if removed:
        print(f'--- Removed {removed} filler phrase(s) ---', file=sys.stderr)
