[**中文**](#中文版) | [**English**](#english)

---

# 中文版

# Content Condenser

**三级内容压缩，为 AI 上下文窗口瘦身。** 节省的是字符数，token 节省视内容而定。

```bash
# 压缩一条构建日志，立竿见影
$ cat build_log.txt | python3 scripts/strip_chars.py -l 2 -s
Chars: 516 -> 469 (-9.1%) | Tokens (est): 129 -> 117 (-9.3%)
```

⚠️ **说明**：节省的数值以字符计。不同 BPE tokenizer 下，短高频词可能不降反升（"understanding" 压缩后可能从 1 token 变 2 token）。安装 `tiktoken` 可获得精确 token 统计。

---

## 核心理念

喂给 LLM 的大多数内容，**信息密度很低**：

| 来源 | 浪费比例 | 原因 |
|------|:--------:|------|
| CLI 输出、日志 | 60-90% | 时间戳、进度条、模板输出 |
| 书面报告、文档 | 40-70% | 填充词、过渡句、重复表述 |
| 对话历史 | 50-80% | 问候语、客套话、冗余轮次 |
| 工具返回值 | 70-90% | 冗长的格式，AI 不需要 |

本项目提供三种压缩方式，针对不同的浪费来源。

---

## 三种模式

### L1：字符级压缩（机械，无 AI 调用，零依赖）

**脚本：** `scripts/strip_chars.py` — 纯 Python 3，零依赖。

LLM 能理解残缺文本——"Ths fnctn tks intgrs" 人类需要猜，AI 直接懂。

| 级别 | 操作 | 字符节省 | 可读性 |
|:----:|------|:--------:|:------:|
| 1 | 去重字母 (letter→leter) | ~1-2% | 完美 |
| 2 | + 去元音 (letter→ltr) | ~10-16% | 能懂 |
| 3 | + 截断长词 (understanding→undrsg) | ~13-17% | 勉强 |
| 4 | + 去填充词 + 去重行 | ~15-20% | 粗糙 |

```bash
# 快速上手指南
cat verbose_log.txt | python3 scripts/strip_chars.py -l 2 -s     # 压缩 + 统计
cat output.txt | python3 scripts/strip_chars.py -l 3 -d          # 压缩 + 对比
python3 scripts/strip_chars.py meeting_notes.md -l 2 -m -d       # markdown 保护模式
cat data.txt | python3 scripts/strip_chars.py -l 1 -p "nginx"    # 保护特定词
```

**自动保护：** URL、邮箱、UUID、代码块（```````）、电话号码
**中文安全：** 中文/日文/韩文自动跳过，不会被碰
**Markdown 模式（`-m`）：** 保护标题 `#`、分割线 `---`、加粗 `**`、斜体 `*`、链接文字 `[text](url)`

**适用：** 日志、CI/CD 输出、构建结果——这些内容量大但价值低，不值得花 token 传给 AI。

### L2：语义压缩（crystalize，AI 做价值判断）

AI 逐句评估内容价值，只保留核心信息。输出仍然**人类可读**。

**流程：**
1. 明确文档要表达的核心信息
2. 逐句问自己：删掉这句，核心信息还完整吗？
3. 保留：事实、数据、逻辑、结论
4. 删除：铺垫、过渡、重复、补充

**一句话 prompt（给 AI 用）：** "逐句评估这段文字中每句话对核心信息的贡献。删除无效句子，只保留事实、数据和逻辑链。输出精简版。"

**适用：** 报告、文档、会议记录、对话历史。

### L3：极限压缩（compress-for-ai，仅 AI 可读）

去掉所有人类表达习惯，只留信息骨架——人类几乎不可读，LLM 直接理解。

```
压缩前 (286 字):
关于这个项目的最新进展情况，我想向大家做一个比较详细的汇报。
首先需要指出的是，我们团队在过去的两周时间里，可以说是付出了
非常大的努力。值得注意的是，项目的核心功能模块已经...

压缩后 (68 字，节省 76%):
项目进度:
- 核心功能: done (dev+test)
- 性能: DB查询 高并发 响应波动 → P0
- UI: 交互体验 待打磨
- ETA: 下月中旬 v1
```

**适用：** 子代理通讯、对话历史归档、任何只给 AI 看不上人类的文本。

---

## 选型决策

```
输入是什么？
│
├─ 机器输出（日志、CLI、构建） ──→ L1 字符级
│
├─ 人类写的内容（文档、聊天） ──→ L2 语义级
│
├─ 仅 AI 使用（子代理、存档） ──→ L3 极限级
│
└─ 代码、配置、测试报错、diff ──→ ✗ 不要压缩
```

## 🚫 永远不要压缩

- **测试失败输出** — 需要完整 stack trace 才能定位问题
- **构建错误** — 错误上下文映射到修复方案
- **安全发现** — 不可丢失信号
- **Diff** — diff 本身就是审查面
- **用户引用的原文** — 原文 = 准确答案
- **源代码文件** — 不要用字符级碰代码
- **配置文件** — YAML/JSON/TOML 保持原样

---

## 实用工作流

| 场景 | 步骤 |
|------|------|
| 存档一份文档 | 原文 → L2 crystalize → 存入 memory/ |
| 分析 500 行日志 | L1 字符级去壳 → L2 crystalize 去废话 → 喂 AI |
| 子代理传信 | 任务描述 → L3 极限压缩 → 发给子代理 |
| 对话历史溢出 | 老轮次 → L3 压缩 | 最新 2 轮 → 保持原样 |
| 读一个超大文件 | `strip_chars.py -l 2 -m -d` → 预览压缩版 |

---

## 辅助脚本

| 文件 | 功能 | 依赖 |
|------|------|------|
| `scripts/strip_chars.py` | L1 字符级 + token 估算 + 对比 | 零依赖 |
| `scripts/strip_fillers.py` | 纯正则剥离中英文填充词 | 零依赖 |

---

## 已知局限

- **字符 ≠ token**：统计以字符为准。token 估算用启发式方法（拉丁语 ~4 字/ token，中文 ~1.5 字/ token）。精确计数需安装 `tiktoken`。
- **Markdown 模式**：保护标题、分割线、加粗/斜体标记、链接文字。表格和引用块尚未保护。
- **L2/L3 验证**：语义和极限压缩依赖 AI 判断，没有自动的信息保留率验证（计划 v2）。
- **中日韩文本**：L1-L3 在词级别对中日韩文不做处理。中文填充词由 L4 覆盖。

---

## ⚠️ Vibe Coding 警告

这个项目由 AI 助手（Clio）在快速原型开发中完成。关键背景：

- 原始创意来自小红书帖子
- L1 脚本在一次会话中手写完成，没有生产级测试套件
- L2/L3 模式完全依赖 AI 自身的判断——没有单独的确定性算法
- "不要压缩"规则来自社区经验，未经验证
- 经过社区代码审查改进（感谢智谱 GLM 提供详细 bug 报告）

**欢迎贡献。** 这是一个起点，不是成品。可以提交 PR 的内容：
- 更好的保护逻辑（markdown 表格、引用块）
- 正式的测试套件
- Claude Code / Copilot / Cursor 集成示例
- 真实工作负载的性能基准
- L2/L3 的信息保留率验证（解压+对比）

---

## 许可协议

MIT — 可用但不提供任何担保。

---

# English

# Content Condenser

**Three-tier content compression for reducing text length in AI context windows.** Characters saved, token savings may vary.

```bash
# L1: Mechanical character compression — zero AI cost, zero dependencies
$ cat build_log.txt | python3 scripts/strip_chars.py -l 2 -s
Chars: 516 -> 469 (-9.1%) | Tokens (est): 129 -> 117 (-9.3%)
```

⚠️ **Important**: Savings are measured in *characters*. Token-level stats use heuristic estimation (~4 chars/tok Latin, ~1.5 chars/tok CJK). Common short words may compress differently than rare ones in BPE tokenizers. Install `tiktoken` for exact counts.

## The Core Insight

Most text fed to LLMs carries **low information density**. Common patterns:

| Source | Waste | Cause |
|--------|:-----:|-------|
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
|:-----:|-----------|:------------:|:-----------:|
| 1 | Remove doubled letters (letter→leter) | ~1-2% | Perfect |
| 2 | + Remove interior vowels (letter→ltr) | ~10-16% | Legible |
| 3 | + Truncate long words (understanding→undrsg) | ~13-17% | Tough |
| 4 | + Remove filler phrases + dedup lines | ~15-20% | Rough |

**Auto-preserved:** URLs, emails, UUIDs, code blocks, phone numbers.
**CJK/Non-Latin:** Automatically skipped at word level.
**Markdown mode (`-m`):** Protects headings, rules, bold/italic markers, link display text.

```bash
# Usage
cat large_log.txt | python3 scripts/strip_chars.py -l 2 --stats
python3 scripts/strip_chars.py meeting_notes.md -l 2 --markdown --diff
cat output.txt | python3 scripts/strip_chars.py -l 1 -p "nginx" "kubernetes"
```

**Best for:** Logs, build output, CI/CD results, raw CLI tool output.

### L2: Semantic (crystalize, AI-judged)

The AI evaluates each sentence for value, removes low-value content. Output remains human-readable.

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
| Read a large file | `strip_chars.py -l 2 -m --diff` → preview compressed |

---

## Scripts

| File | Purpose | Dependencies |
|------|---------|:------------:|
| `scripts/strip_chars.py` | L1 compression + token estimation + diff | None (stdlib) |
| `scripts/strip_fillers.py` | Regex-based filler phrase removal | None (stdlib) |

---

## Limitations

- **Character vs token**: Measures character savings. Token stats use heuristic (~4 chars/tok Latin, ~1.5 chars/tok CJK). Use `tiktoken` for exact counts.
- **Markdown mode**: Protects headings, rules, bold/italic markers, link text. Tables and blockquotes not yet protected.
- **L2/L3 validation**: Relies on AI judgment. No automatic information-retention verification (planned for v2).
- **CJK text**: L1-L3 is a no-op for CJK at word level. Chinese filler phrases covered by L4.

---

## ⚠️ Vibe Coding Warning

This project was created by an AI assistant (Clio) for a human collaborator (Mini) as a rapid prototyping session. Key context:

- Idea originated from a Xiaohongshu (RED) social media post
- L1 script written from scratch in one session without a production test suite
- L2/L3 modes depend entirely on AI's own judgment
- "Never compress" rules from community experience, not empirical validation
- Improved through community code review (thanks to GLM for detailed bug reports)

**Contributions welcome.** Send PRs for markdown preservation improvements, test suite, integration examples, benchmarks, or information retention validation.

---

## License

MIT — do what you want, no warranty.
