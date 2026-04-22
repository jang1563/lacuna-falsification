# Opus 4.7 API Verification — Extended Thinking

Verified: 2026-04-22

---

## Verified API Shape (as of 2026-04-22)

**CRITICAL BREAKING CHANGE:** `thinking={"type": "enabled", "budget_tokens": N}` returns a **400 error** on
`claude-opus-4-7`. The pseudocode in our current `opus_client.py` will fail immediately. Migration required before
any live API call.

### Minimal working call

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    thinking={"type": "adaptive"},           # only valid thinking mode on Opus 4.7
    messages=[
        {"role": "user", "content": "..."}
    ],
)

for block in response.content:
    if block.type == "thinking":
        print(block.thinking)   # empty string unless display="summarized" is set (see below)
    elif block.type == "text":
        print(block.text)
```

### With effort control and visible thinking (recommended for propose_laws)

```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=32000,
    thinking={
        "type": "adaptive",
        "display": "summarized",  # REQUIRED on 4.7 to get non-empty block.thinking
    },
    output_config={"effort": "high"},        # low | medium | high (default) | xhigh | max
    messages=[
        {"role": "user", "content": "..."}
    ],
)
```

---

## Key Findings

### `budget_tokens`: **REMOVED on Opus 4.7 — returns 400 error**

- `thinking={"type": "enabled", "budget_tokens": N}` is a **breaking change** on `claude-opus-4-7`.
- It still works (but is deprecated) on `claude-opus-4-6` and `claude-sonnet-4-6`.
- The research note "verify before running" was correct and critical.

### Adaptive thinking: **THE ONLY supported mode on Opus 4.7**

- Set `thinking={"type": "adaptive"}` to enable thinking. Without this field, thinking is **off by default**.
- Effort replaces `budget_tokens` as the control knob: use `output_config={"effort": "high"}` (or `"xhigh"`,
  `"max"`).
- Adaptive thinking automatically enables interleaved thinking between tool calls — no beta header needed.

### `max_tokens` constraint

- No `budget_tokens` → no minimum `max_tokens` relative to a budget.
- Set `max_tokens` to cover thinking + response text combined. The docs use `16000` as a baseline; for
  multi-step reasoning like `propose_laws`, use `32000`–`128000`.
- `max_tokens` is a hard per-request cap (the model is not aware of it). Use `output_config.task_budget` if
  you want an advisory agentic-loop cap instead (requires beta header `task-budgets-2026-03-13`).

### Thinking block type in response

| Attribute | Value / Notes |
|-----------|---------------|
| `block.type` | `"thinking"` |
| `block.thinking` | The thinking text — **empty string by default on Opus 4.7** |
| `block.signature` | Encrypted full thinking; always present; used for multi-turn continuity |

**Opus 4.7 defaults `display` to `"omitted"`** (unlike Opus 4.6 which defaulted to `"summarized"`). You must
explicitly pass `"display": "summarized"` in the thinking dict to receive non-empty `block.thinking`.

### Other Opus 4.7 breaking changes that affect `opus_client.py`

- `temperature`, `top_p`, `top_k` — setting any non-default value returns **400 error**. Remove these if present.
- Sampling is no longer user-controllable; use `effort` instead.

---

## Corrected `opus_client.py` Snippet

Replace the three role calls with the following pattern:

```python
import anthropic

client = anthropic.Anthropic()

THINKING_CONFIG = {
    "type": "adaptive",
    "display": "summarized",   # omit to suppress thinking text (faster TTFT when streaming)
}
OUTPUT_CONFIG = {"effort": "high"}   # use "xhigh" for hardest reasoning tasks

# --- Role: Theory Proposer ---
def propose_laws(context: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=32000,
        thinking=THINKING_CONFIG,
        output_config=OUTPUT_CONFIG,
        messages=[
            {
                "role": "user",
                "content": context,
            }
        ],
    )
    thinking_text = ""
    answer_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text = block.thinking      # summarized reasoning trace
        elif block.type == "text":
            answer_text = block.text
    return {"thinking": thinking_text, "answer": answer_text}


# --- Role: Falsifier ---
def falsify_law(law: str, evidence: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=32000,
        thinking=THINKING_CONFIG,
        output_config=OUTPUT_CONFIG,
        messages=[
            {
                "role": "user",
                "content": f"Law: {law}\n\nEvidence: {evidence}\n\nAttempt to falsify this law.",
            }
        ],
    )
    thinking_text = ""
    answer_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text = block.thinking
        elif block.type == "text":
            answer_text = block.text
    return {"thinking": thinking_text, "answer": answer_text}


# --- Role: Synthesizer ---
def synthesize(laws: list[str], falsifications: list[dict]) -> dict:
    summary = "\n".join(
        f"Law {i+1}: {l}\nFalsification: {f['answer']}"
        for i, (l, f) in enumerate(zip(laws, falsifications))
    )
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=32000,
        thinking=THINKING_CONFIG,
        output_config=OUTPUT_CONFIG,
        messages=[
            {
                "role": "user",
                "content": f"Synthesize the following laws and their falsification attempts:\n\n{summary}",
            }
        ],
    )
    thinking_text = ""
    answer_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text = block.thinking
        elif block.type == "text":
            answer_text = block.text
    return {"thinking": thinking_text, "answer": answer_text}
```

### What changed vs. pseudocode

| Before (pseudocode) | After (correct for Opus 4.7) |
|---------------------|------------------------------|
| `thinking={"type": "enabled", "budget_tokens": 8000}` | `thinking={"type": "adaptive", "display": "summarized"}` |
| `budget_tokens` controlling spend | `output_config={"effort": "high"}` |
| `max_tokens` had to exceed `budget_tokens` | `max_tokens` is a free hard cap — set to task size |
| No `output_config` parameter | Add `output_config={"effort": "high"}` |
| `block.thinking` always populated | `block.thinking` empty unless `display="summarized"` |
| `temperature` parameter (if present) | Remove entirely — 400 error on Opus 4.7 |

---

## Sources

| URL | Fetched |
|-----|---------|
| [Building with extended thinking — Claude API Docs](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking) | 2026-04-22 |
| [Adaptive thinking — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking) | 2026-04-22 |
| [What's new in Claude Opus 4.7 — Claude API Docs](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7) | 2026-04-22 |
| Web search: "claude-opus-4-7 extended thinking api budget_tokens adaptive 2026" | 2026-04-22 |
