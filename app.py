# pip install -r requirements.txt
import time

import gradio as gr
from postmortem import generate_postmortem, SEVERITY_OPTIONS

EXAMPLE_SLACK = """[14:02] alerts-bot: 🔴 P1 - checkout-service error rate 42% (threshold 5%)
[14:03] @priya: looking now
[14:05] @priya: seeing 500s from payment-gateway calls, timing out
[14:06] @dev: deploy went out at 13:58 for checkout-service, rolling back now
[14:09] @dev: rollback complete
[14:11] @priya: error rate back to 0.3%, looks resolved
[14:15] @priya: confirmed stable for 5 min, closing incident"""

EXAMPLE_ALERTS = """14:02:01 [CRITICAL] checkout-service error_rate=42% threshold=5%
14:02:15 [CRITICAL] payment-gateway p99_latency=8200ms threshold=1000ms
14:09:32 [INFO] checkout-service deploy rollback completed
14:11:04 [INFO] checkout-service error_rate=0.3%
14:15:00 [INFO] incident auto-resolved"""

EXAMPLE_COMMITS = """13:58 deploy checkout-service v2.14.0 (commit a1b2c3d: "add retry logic for payment-gateway calls")
14:09 rollback checkout-service to v2.13.2"""


def run_generate(title, severity, incident_datetime, slack_text, alerts_text, commits_text):
    return generate_postmortem(title, severity, incident_datetime, slack_text, alerts_text, commits_text)


def save_to_file(markdown_text):
    if not markdown_text or markdown_text.startswith("_Paste at least one"):
        return None
    path = f"/tmp/postmortem_{int(time.time())}.md"
    with open(path, "w") as f:
        f.write(markdown_text)
    return path


with gr.Blocks(title="📝 Postmortem Generator") as demo:
    gr.Markdown("# 📝 Postmortem Generator")
    gr.Markdown(
        "Paste what you have from an incident — Slack discussion, alerts, "
        "deploys/commits — and get a first-draft blameless postmortem. "
        "**This is a draft for a human to review, not a final document.**"
    )

    with gr.Row():
        title_input = gr.Textbox(label="Incident title", placeholder="Checkout service 5xx spike")
        severity_input = gr.Dropdown(label="Severity", choices=SEVERITY_OPTIONS, value="Unknown")
        datetime_input = gr.Textbox(label="Incident date/time (optional)", placeholder="2026-07-27 14:00 UTC")

    slack_input = gr.Textbox(
        label="Slack / chat discussion during the incident",
        placeholder=EXAMPLE_SLACK,
        lines=8,
    )
    alerts_input = gr.Textbox(
        label="Alerts / monitoring log",
        placeholder=EXAMPLE_ALERTS,
        lines=6,
    )
    commits_input = gr.Textbox(
        label="Deploys / commits / changes around this time",
        placeholder=EXAMPLE_COMMITS,
        lines=4,
    )

    generate_btn = gr.Button("📝 Generate Postmortem Draft", variant="primary")

    gr.Examples(
        examples=[[EXAMPLE_SLACK, EXAMPLE_ALERTS, EXAMPLE_COMMITS]],
        inputs=[slack_input, alerts_input, commits_input],
        label="Load example incident",
    )

    output = gr.Markdown()
    download_btn = gr.Button("⬇️ Download as .md")
    download_file = gr.File(label="Download", visible=True)

    generate_btn.click(
        fn=run_generate,
        inputs=[title_input, severity_input, datetime_input, slack_input, alerts_input, commits_input],
        outputs=output,
    )
    download_btn.click(fn=save_to_file, inputs=output, outputs=download_file)

if __name__ == "__main__":
    demo.launch(share=True)