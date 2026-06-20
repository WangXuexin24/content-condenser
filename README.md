# Content Condenser

**Three-tier content compression for AI context windows.** Save tokens on logs, documents, and agent communication — without losing critical information.

```python
# L1: Mechanical character compression — zero AI cost
$ cat build_log.txt | python3 scripts/strip_chars.py -l 2 -s
Chars: 516 -> 469 (-9.1%)
```

## The Core Insight

Most tokens fed to LLMs carry **low information density**. Common patterns:

| Source | Waste | Cause |
|--------|-------|-------|
| CLI output | 60-90% | Progress lines, timestamps, boilerplate |
| Written reports | 40-70% | Filler phrases, transitions, repetitions |
| Conversation history | 50-80% | Greetings, politeness, redundant turns |
| Tool output | 70-90% | Verbose formats the model doesn't need |

This project provides three tiers of compression, each targeting a different kind of waste.

---

## Three Tiers

### L1: Character-level (mechanical, no AI)

**Script:** `scripts/strip_chars.py` — zero dependencies, pure Python 3.

LLMs understand text with missing characters. Removing vowels, doubled letters, and truncating long words cuts token count without losing meaning.

| Level | Operation | Savings | Readability |
|-------|-----------|---------|-------------|
| 1 | Remove doubled letters (letter→leter) | ~1-2% | Perfect |
| 2 | + Remove interior vowels (letter→ltr) | ~10-16% | Legible |
| 3 | + Truncate long words (understanding→undrsg) | ~13-17% | Tough |
| 4 | + Remove filler phrases + dedup lines | ~15-20% | Rough |

**Auto-preserved:** URLs, emails, UUIDs, code blocks, phone numbers.

```bash
# Quick usage
cat large_log.txt | python3 scripts/strip_chars.py -l 2 --stats
python3 scripts/strip_chars.py meeting_notes.md -l 3 --markdown
cat verbose_output.txt | python3 scripts/strip_chars.py -l 1 -p "nginx" "kubernetes"
```

**Best for:** Logs, build output, CI/CD results, raw CLI tool output — anything where cost of AI processing exceeds value of content.

### L2: Semantic (crystalize, AI-judged)

The AI reads the document, evaluates each sentence for value contribution, and removes low-value content. Output remains human-readable.

**Process:**
1. Identify the document's core message
2. Ask: "If I remove this sentence, is the core message still intact?"
3. Keep: facts, data, logic, conclusions
4. Remove: transitions, background, repetitions, digressions

**Best for:** Reports, documentation, meeting notes, conversation logs.

### L3: Extreme (compress-for-ai, AI-readable only)

Strip all human-oriented writing patterns. Output is a skeletal information structure — almost unreadable to humans, fully parseable by AI.

```
Before (286 chars):
关于这个项目的最新进展情况，我想向大家做一个比较详细的汇报。
首先需要指出的是，我们团队在过去的两周时间里...

After (68 chars):
项目进度:
- 核心功能: done (dev+test)
- 性能: DB查询 高并发 响应波动 → P0
- UI: 交互体验 待打磨
- ETA: 下月中旬 v1
```

**Best for:** Memory archiving, sub-agent communication, long-running conversation context, any text meant only for AI consumption.

---

## Decision Guide

```
Input type?
│
├─ Machine output (logs, CLI, build) ────→ L1 character level
│
├─ Human writing (docs, chat history) ──→ L2 semantic (crystalize)
│
├─ Agent/AI-only context ───────────────→ L3 extreme (compress-for-ai)
│
└─ Code, config, test output, diffs ────→ ✗ DO NOT COMPRESS
```

## 🚫 Never Compress

- **Failing test output** — full stack traces needed for debugging
- **Build errors** — error context maps to the fix
- **Security findings** — must not lose signal
- **Diffs** — the diff is the review surface
- **User-quoted original text** — original = accurate answer
- **Source code** — never apply character-level to code
- **Config files** — YAML/JSON/TOML verbatim

---

## Workflows

| Scenario | Steps |
|----------|-------|
| **Archive a document** | Raw → L2 crystalize → save to memory |
| **Analyze 500 lines of logs** | L1 strip_chars → L2 crystalize → feed to AI |
| **Sub-agent handoff** | Task description → L3 compress → send to sub-agent |
| **Conversation overflow** | Old turns → L3 compress | Last 2 turns → keep verbatim |
| **Read a large file** | `strip_chars.py -l 2 -m` → read compressed version |

---

## Scripts

| File | Purpose | Dependencies |
|------|---------|-------------|
| `scripts/strip_chars.py` | L1 character-level compression | None (stdlib only) |
| `scripts/strip_fillers.py` | Regex-based filler phrase removal | None (stdlib only) |

---

## ⚠️ Vibe Coding Warning

This project was created by an AI assistant as part of a rapid prototyping session. Key context:

- The original idea came from a Xiaohongshu (RED) social media post
- The L1 script was written from scratch in a single session without a production test suite
- The L2/L3 modes depend entirely on the AI's own judgment — there is no separate model or deterministic algorithm
- The "never compress" rules come from community experience, not empirical validation

**Contributions welcome.** This is a starting point, not a finished product. Send PRs for:
- Better preservation logic in the character-level compressor
- A proper test suite
- Integration examples for Claude Code, Copilot, or Cursor
- Performance benchmarks on real workloads

---

## License

MIT — do what you want, no warranty.
