import os
import sys
import json
import argparse
import urllib.request
import urllib.error


def _send(webhook_url: str, payload: dict) -> None:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url, data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} — {e.read().decode('utf-8', errors='replace')[:200]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}")
        sys.exit(1)


def _build_payload(message: str, title: str | None, color: str | None) -> dict:
    COLOR_MAP = {"good": "#2eb886", "warning": "#daa520", "danger": "#cc0000"}
    hex_color = COLOR_MAP.get(color, color) if color else None

    if title or hex_color:
        payload = {
            "attachments": [{
                "color": hex_color or "#0099ff",
                "blocks": []
            }]
        }
        blocks = payload["attachments"][0]["blocks"]
        if title:
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": title}
            })
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": message}
        })
    else:
        payload = {
            "blocks": [{
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            }]
        }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a message to a Slack channel via webhook.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--message", help="Message text (Slack mrkdwn)")
    group.add_argument("--file",    help="Send content of a text/Markdown file")
    parser.add_argument("--title",   default=None, help="Optional bold title block")
    parser.add_argument("--color",   default=None, help="good | warning | danger | #hexcolor")
    parser.add_argument("--webhook", default=None, help="Override $SLACK_WEBHOOK_URL")
    args = parser.parse_args()

    webhook_url = args.webhook or os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("Error: SLACK_WEBHOOK_URL not set.\n"
              "Set it: export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'")
        sys.exit(1)

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: '{args.file}' not found."); sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            message = f.read().strip()
    else:
        message = args.message

    payload = _build_payload(message, args.title, args.color)
    _send(webhook_url, payload)
    print(f"✅  Message sent to Slack.")


if __name__ == "__main__":
    main()
