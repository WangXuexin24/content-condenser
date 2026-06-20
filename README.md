# Content Condenser

**Three-tier content compression for reducing text length in AI context windows.** Characters saved, token savings may vary.

```bash
# Quick test: compress build logs
$ cat build_log.txt | python3 scripts/strip_chars.py -l 2 -s
Chars: 516 -> 469 (-9.1%) | Tokens (est): 129 -> 117 (-9.3%)
```

⚠️ **Important**: Savings are measured in *characters*. Token-level stats use heuristic estimation. Common short words may compress differently than rare ones in BPE tokenizers. Install `tiktoken` for exact counts.

## The Core Insight

Most text fed to LLMs carries **low information density**. Common patterns:

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

LLMs understand text with missing characters. Removing vowels, doubled letters, and truncating long words reduces text length without losing meaning.

| Level | Operation | Char savings | Readability |
|-------|-----------|:---------:|-------------|
| 1 | Remove doubled letters (letter→leter) | ~1-2% | Perfect |
| 2 | + Remove interior vowels (letter→ltr) | ~10-16% | Legible |
| 3 | + Truncate long words (understanding→undrsg) | ~13-17% | Tough |
| 4 | + Remove filler phrases + dedup lines | ~15-20% | Rough |

**Auto-preserved:** URLs, emails, UUIDs, code blocks, phone numbers.
**CJK/Non-Latin:** Automatically skipped at word level.
**Markdown mode (`-m`):** Protects headings, rules, bold/italic markers, link display text.

```bash
# Basic usage
cat large_log.txt | python3 scripts/strip_chars.py -l 2 -s

# Diff view: see exactly what changed
cat verbose.txt | python3 scripts/strip_chars.py -l 3 -d

# Markdown-safe: preserves formatting
python3 scripts/strip_chars.py meeting_notes.md -l 2 -m -d

# Protect specific words
cat output.txt | python3 scripts/strip_chars.py -l 1 -p "nginx" "kubernetes"
```

**Best for:** Logs, build output, CI/CD results, raw CLI tool output.

### L2: Semantic (crystalize, AI-judged)

The AI reads the document, evaluates each sentence for value contribution, and removes low-value content. Output remains human-readable.

**Process:**
1. Identify the document's core message
2. Ask: "If I remove this sentence, is the core message still intact?"
3. Keep: facts, data, logic, conclusions
4. Remove: transitions, background, repetitions, digressions

**Best for:** Reports, documentation, meeting notes, conversation logs.

### L3: Extreme (compress-for-ai, AI-readable only)

Strip all human-oriented writing patterns. Output is skeletal — almost unreadable to humans, fully parseable by AI.

```
Before (286 chars):
关于这个项目的最新进展情况，我想向大家做一个比较详细的汇报...

After (68 chars, 76% reduction):
项目进度:
- 核心功能: done (dev+test)
- 性能: DB查询 高并发 响应波动 → P0
- UI: 交互体验 待打磨
- ETA: 下月中旬 v1
```

**Best for:** Memory archiving, sub-agent communication, long-running conversation context.

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
└─ Code, config, test failures, diffs ──→ ✗ DO NOT COMPRESS
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
| Archive a document | Raw → L2 crystalize → save to memory |
| Analyze 500 lines of logs | L1 strip_chars → L2 crystalize → feed to AI |
| Sub-agent handoff | Task → L3 compress → send to sub-agent |
| Conversation overflow | Old turns → L3 compress \| Last 2 turns → verbatim |
| Read a large file | `strip_chars.py -l 2 -m -d` → preview compressed version |

---

## Scripts

| File | Purpose | Dependencies |
|------|---------|-------------|
| `scripts/strip_chars.py` | L1 character-level + token estimation + diff | None (stdlib only) |
| `scripts/strip_fillers.py` | Regex-based filler phrase removal | None (stdlib only) |

---

## Limitations

- **Character vs token**: Measures character savings. Token stats use heuristic (~4 chars/tok Latin, ~1.5 chars/tok CJK). Common short words may use *more* tokens when compressed. Use `tiktoken` for exact counts.
- **Markdown mode**: Protects headings, rules, bold/italic markers, and link text. Tables and blockquotes are not yet protected.
- **L2/L3 validation**: Semantic and extreme compression rely on AI judgment. No automatic information-retention verification (planned for v2).
- **Chinese/Japanese/Korean**: L1-L3 is a no-op for CJK text at the word level. Chinese filler phrases are covered by L4.

---

## ⚠️ Vibe Coding Warning

This project was created by an AI assistant (Clio) for a human collaborator (Mini) as a rapid prototyping session. Key context:

- Idea originated from a Xiaohongshu (RED) social media post
- The L1 script was written from scratch in a single session without a production test suite
- L2/L3 modes depend on the AI's own judgment — no separate model or deterministic algorithm
- "Never compress" rules from community experience, not empirical validation
- Improved through community code review (thanks to GLM for detailed bug reports)

**Contributions welcome.** Send PRs for:
- Better preservation logic (markdown tables, blockquotes)
- A proper test suite
- Integration examples for Claude Code, Copilot, Cursor
- Real workload performance benchmarks
- Decompress-and-compare verification for L2/L3

---

## License

MIT — do what you want, no warranty.
