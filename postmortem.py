"""
postmortem.py
Takes raw incident inputs (Slack thread, alert/monitoring log, deploy/commit
history — all pasted as text) and asks an LLM to draft a structured,
blameless postmortem document.

Uses the OpenAI-compatible chat.completions API so the same code can hit
any provider that speaks that protocol — Claude, Groq, OpenAI itself,
OpenRouter, local Ollama, etc. Swap providers by changing env vars only,
no code changes:

    LLM_BASE_URL   e.g. https://api.anthropic.com/v1/   (Claude)
                   e.g. https://api.groq.com/openai/v1   (Groq)
                   e.g. https://api.openai.com/v1        (OpenAI)
    LLM_API_KEY    the API key for whichever provider you're pointing at
    LLM_MODEL      a model name valid for that provider, e.g.:
                     claude-sonnet-5            (Claude)
                     llama-3.3-70b-versatile    (Groq)
                     gpt-4o                     (OpenAI)

This produces a DRAFT for a human to review and edit — not a final,
publishable postmortem. It should never be posted verbatim without
someone who was actually involved checking it for accuracy.
"""

import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Defaults to Anthropic's OpenAI-compatible endpoint; override any of these
# in .env to point at a different provider without touching this file.
#LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.anthropic.com/v1/")
#LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
#LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

SEVERITY_OPTIONS = ["SEV1 - Critical", "SEV2 - Major", "SEV3 - Minor", "SEV4 - Low / no impact", "Unknown"]

SYSTEM_PROMPT = (
    "You are an SRE/ops assistant that drafts blameless postmortems. "
    "Blameless means: focus on systems, processes, and contributing "
    "factors — never on individual blame or \"who screwed up.\" Assume "
    "good intent from everyone involved. Never invent facts, names, "
    "timestamps, or root causes that aren't supported by the material "
    "you're given — if something is unclear, say so explicitly rather "
    "than guessing."
)


PROMPT_TEMPLATE = """Incident title: {title}
Severity: {severity}
Incident date/time (if known): {incident_datetime}

--- Slack / chat discussion during the incident ---
{slack_text}

--- Alerts / monitoring log ---
{alerts_text}

--- Deploys / commits / changes around this time ---
{commits_text}

---

Using only the information above, draft a postmortem document in Markdown
with exactly these sections:

## Summary
2-4 sentences: what happened, at a high level, and the overall impact.

## Impact
Who/what was affected, for how long, and how severely. If the material
doesn't specify user-facing impact, say that explicitly rather than
estimating.

## Timeline
A chronological bullet list of key events with timestamps where available
(detection, escalation, key actions taken, mitigation, resolution). Pull
timestamps from the source material; do not fabricate times that weren't
given.

## Root Cause
The most likely root cause(s) based on the evidence given. If the
evidence is inconclusive, say "root cause not fully confirmed" and
describe the leading hypothesis instead of asserting certainty.

## Contributing Factors
Process, tooling, or systemic gaps that made this possible or made it
worse/harder to detect — framed blamelessly (e.g. "the deploy pipeline
lacked a canary stage," not "X deployed without testing").

## What Went Well
1-3 bullets on things that worked (fast detection, good communication,
an effective rollback, etc.) if the material supports any of these.

## Action Items
A bulleted list of concrete, assignable follow-ups (e.g. "Add alerting
for X," "Add a canary stage to the Y pipeline"). Do not assign these to
named individuals — leave owner/due-date as "TBD" for a human to fill in.

Respond with ONLY the Markdown document, no preamble, no commentary
before or after it.
"""


def generate_postmortem(
    title: str,
    severity: str,
    incident_datetime: str,
    slack_text: str,
    alerts_text: str,
    commits_text: str,
) -> str:
    """Call Claude to draft a postmortem from pasted incident material."""
    if not any([slack_text.strip(), alerts_text.strip(), commits_text.strip()]):
        return "_Paste at least one of: Slack discussion, alerts/monitoring log, or deploys/commits._"

    prompt = PROMPT_TEMPLATE.format(
        title=title.strip() or "(untitled incident)",
        severity=severity or "Unknown",
        incident_datetime=incident_datetime.strip() or "(not specified)",
        slack_text=slack_text.strip() or "(none provided)",
        alerts_text=alerts_text.strip() or "(none provided)",
        commits_text=commits_text.strip() or "(none provided)",
    )

    resp = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    draft = resp.choices[0].message.content.strip()
    draft = re.sub(r"^```(?:markdown)?|```$", "", draft, flags=re.MULTILINE).strip()

    disclaimer = (
        "> ⚠️ **AI-generated draft.** Review every fact, timestamp, and "
        "conclusion below with someone who was actually involved before "
        "sharing or publishing this postmortem.\n\n"
    )
    return disclaimer + draft