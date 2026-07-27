# 📝 Postmortem Generator

Paste what you have from an incident — a Slack thread, an alerts/monitoring
log, and the deploys/commits around the time it happened — and get back a
first-draft **blameless postmortem** in Markdown.

This is a drafting tool, not an autopilot. Every draft it produces is
explicitly a starting point for a human who was actually involved in the
incident to review, correct, and finish.

## Why

Writing a good postmortem takes time: reconstructing the timeline, teasing
out a root cause from a wall of alerts, and phrasing things blamelessly
instead of "X broke it." This tool does the first pass — stitching together
whatever raw material you paste in — so a human can spend their time
correcting and improving a draft instead of staring at a blank page.

## Features

- Structured output: Summary, Impact, Timeline, Root Cause, Contributing
  Factors, What Went Well, Action Items
- Explicitly instructed not to invent facts, timestamps, or root causes —
  if the pasted material doesn't support a conclusion, the draft says so
  instead of guessing
- Every draft is stamped with a visible "AI-generated, review before
  publishing" disclaimer
- Download the result as a `.md` file
- **Provider-agnostic**: swap between Claude, Groq, OpenAI, or any other
  OpenAI-compatible endpoint by changing three environment variables — no
  code changes

## Screenshot / example

Click **"Load example incident"** in the UI to see a sample checkout-service
outage (Slack thread + alerts + deploy log) and the kind of draft it
produces.

## Setup

```bash
git clone <this-repo-url>
cd postmortem-generator
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your API key. It defaults to Claude via Anthropic's
OpenAI-compatible endpoint — see [Switching LLM providers](#switching-llm-providers)
below to use something else.

Run it:

```bash
python app.py
```

This opens a local Gradio UI (and, since `share=True` is set, also prints a
temporary public URL — remove that flag in `app.py` if you don't want one).

## Usage

1. Fill in an incident title, severity, and (optionally) the date/time
2. Paste in whatever you have:
   - Slack/chat discussion during the incident
   - Alerts / monitoring log lines
   - Deploys, commits, or config changes around that time
3. Click **Generate Postmortem Draft**
4. Review the draft carefully — correct anything wrong, fill in the "TBD"
   owners/due-dates on action items — before sharing it
5. Optionally click **Download as .md** to save it

You don't need all three inputs — one is enough to get a draft, more gives
the model better material to work with.

## Switching LLM providers

`postmortem.py` talks to the LLM through the OpenAI-compatible
`chat.completions` API, so any provider that speaks that protocol works.
Set these in `.env`:

| Variable       | Purpose                                  |
|----------------|-------------------------------------------|
| `LLM_BASE_URL` | API base URL for the provider              |
| `LLM_API_KEY`  | API key for that provider                  |
| `LLM_MODEL`    | Model name valid for that provider         |

Examples:

```bash
# Claude (default)
LLM_BASE_URL=https://api.anthropic.com/v1/
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-5

# Groq (free Llama models)
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile

# OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o
```

See `.env.example` for ready-to-uncomment blocks.

## Project structure

```
.
├── app.py              # Gradio UI
├── postmortem.py        # Prompt + LLM call + draft assembly
├── requirements.txt
├── .env.example
└── README.md
```

## A note on data

Incident data often contains internal hostnames, customer identifiers, or
other sensitive details. Whatever you paste in gets sent to whichever LLM
provider you've configured — review your organization's data-handling
policy before pasting real incident data from production systems.

## Roadmap / ideas

- Pull Slack threads, alerts, and deploy history automatically via API
  instead of copy/paste
- Export to Confluence/Notion in addition to `.md`
- A "diff mode" that compares a human-edited postmortem back against the
  original draft to see what got corrected (useful for improving prompts
  over time)

## License

Add a license of your choice (MIT is a common default for internal tooling
like this) before making the repo public.