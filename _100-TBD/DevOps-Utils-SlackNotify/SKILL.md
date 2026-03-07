---
name: sending-slack-notifications
description: Sends a message to a Slack channel via an Incoming Webhook URL. Use when the user asks to send a Slack message, notify a channel, alert on deploy, or post to Slack.
---

# UTILS-DevOps-SlackNotify Skill

## When to Use This Skill
- User says "send a Slack message", "notify Slack", "post to a channel", or "alert on deploy"
- CI/CD pipeline notifications — build passed/failed, deployment complete
- Agent automation — notify humans of task completion or errors

---

## Prerequisites

**Set up a Slack Incoming Webhook:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create App → Incoming Webhooks
2. Enable and copy the webhook URL
3. Export: `export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."`

---

## Workflow
- [ ] 1. Set `SLACK_WEBHOOK_URL`
- [ ] 2. Run `scripts/slack_notify.py --message "..."`
- [ ] 3. Check Slack for the notification

---

## Commands

```bash
# Send a simple message
python3 scripts/slack_notify.py --message "Deployment complete ✅"

# With emoji and formatting
python3 scripts/slack_notify.py --message "*Build failed* ❌ on branch `main`"

# With title/header block
python3 scripts/slack_notify.py \
  --title "Deploy Status" \
  --message "v2.1.0 deployed to production in 42s" \
  --color good

# From a file
python3 scripts/slack_notify.py --file report.md

# Use a different webhook URL directly
python3 scripts/slack_notify.py --message "Alert!" \
  --webhook "https://hooks.slack.com/services/..."
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--message` | — | Message text (Markdown supported) |
| `--file` | — | Send content of a text/Markdown file |
| `--title` | — | Optional bold title above message |
| `--color` | — | Attachment color: `good` (green), `warning` (yellow), `danger` (red) |
| `--webhook` | `$SLACK_WEBHOOK_URL` | Override webhook URL |

---

## Resources
- `scripts/slack_notify.py` — core notifier (stdlib urllib, no pip required)
