---
name: Infographic Bot Architecture Feedback
description: User wants Claude Code CLI as the orchestrator, NOT an autonomous Python pipeline with Anthropic API — manual approval via iMessage before posting
type: feedback
---

The ai-infographic-bot should be a Claude Code-driven workflow, NOT an autonomous Python pipeline.

**Why:** User wants to run one command, have Claude CLI do the research/curation/image generation/captioning, then get manual approval via iMessage before posting. The Anthropic API should NOT be called from Python code — Claude Code itself IS the LLM doing the thinking.

**How to apply:**
- No `anthropic` SDK calls in the codebase — Claude Code handles all intelligence
- The "pipeline" is a skill/command that Claude executes interactively
- Must include an iMessage approval step: draft post → send preview to approver → wait for approval → post
- User wants to manually test first before any cron/scheduling
- Keep it simple — don't over-engineer with retry decorators, session managers, etc.
- The tool is: user runs Claude → Claude researches news → Claude generates infographic → Claude drafts caption → sends for approval → posts on approval
