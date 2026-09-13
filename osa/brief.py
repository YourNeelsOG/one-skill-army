"""Emit the harness directive that every host adapter injects into the model.

The brief is what keeps One Skill Army active. Adapters print it at session
start and on every user prompt, so the disciplines survive a mid-session model
switch or a context compaction. It is short on purpose: the full rules live in
the orchestrator skill; this is the always-on reminder plus the pointer to the
prebuilt project context.
"""

# How hard to compress internal working/context overhead per level. The actual
# implementation output is never compressed at any level.
_COMPRESSION = {
    "lite": "Trim filler and hedging in your working notes; keep reasoning readable.",
    "full": "Compress internal working and context overhead aggressively: no filler, no restating, no narrating tool calls.",
    "ultra": "Compress internal working and context overhead to the minimum: fragments over sentences, drop every non-load-bearing word from reasoning and status.",
}

_RAILS = (
    "Rails, highest priority first: git-safety (never force push, never open a "
    "PR or enable an AI code reviewer without asking) > anti-hallucination "
    "(no claim about code you have not read this session) > "
    "verification-before-completion (no done without fresh evidence) > "
    "minimal-code (climb the reuse ladder before writing) > disciplined "
    "workflow (classify, get approval, then TDD)."
)


def brief(level="full"):
    "Return the always-on harness directive for the given intensity level."
    compression = _COMPRESSION.get(level, _COMPRESSION["full"])
    return "\n".join([
        "ONE SKILL ARMY ACTIVE (level: " + level + ").",
        "",
        _RAILS,
        "",
        "Overhead compression: " + compression + " NEVER compress the actual "
        "implementation output, code, commands, file paths, numbers, or exact "
        "error strings; compress the overhead, not the answer.",
        "",
        "Project context is prebuilt. Read .osa/context.md first and query it "
        "(osa context <term>) instead of scanning the repository; the graph "
        "already knows where things live.",
        "",
        "This directive is active every response and persists across a model "
        "switch and across context compaction. Re-anchor to it each turn.",
    ])
