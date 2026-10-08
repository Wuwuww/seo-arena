"""Character bigrams for Chinese, whole words for Latin. No external tokenizer."""

from __future__ import annotations

import re


_LATIN = re.compile(r"[a-z0-9]+")
_CJK = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = _LATIN.findall(lowered)
    for span in _CJK.findall(lowered):
        if len(span) == 1:
            tokens.append(span)
        else:
            tokens.extend(span[i : i + 2] for i in range(len(span) - 1))
    return tokens
