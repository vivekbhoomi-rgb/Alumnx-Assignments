"""Analyze every .txt file in this folder with Claude, find which one(s) contain the
target email, and submit them to the Text Dashboard API (/api/entries).

For each file Claude extracts the learner email, assignment topic and course, and says
whether the file contains TARGET_EMAIL. By default only files containing TARGET_EMAIL are
submitted (sender = the target email's prefix). Use --all to submit every file instead
(sender = each file's learner email prefix).

Setup:   pip install anthropic requests python-dotenv
         put ANTHROPIC_API_KEY (and optionally DASHBOARD_API_KEY) in .env
Run:     python analyze_and_submit.py --dry-run   # analyze only
         python analyze_and_submit.py             # submit matching file(s)
         python analyze_and_submit.py --all       # submit all files
"""
import json
import os
import sys
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TARGET_EMAIL = "vivek.bhoomi@databeat.io"
MODEL = "claude-sonnet-5-5"
API_URL = "https://trainer-central-assigments-api.onrender.com/api/entries"
MAX_TEXT = 10000  # EntryIn.text maxLength
FOLDER = Path(__file__).parent

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


def analyze(content: str) -> dict:
    """Return {"contains_target", "evidence", "learner_email", "topic", "course"}."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system="You extract fields from notification emails. Reply with JSON only, no prose or code fences.",
        messages=[{
            "role": "user",
            "content": (
                f"Analyze this file. Does it contain the exact email address {TARGET_EMAIL} "
                "(case-insensitive)? Similar addresses with a different name or domain do NOT count. "
                "Also extract the learner's email, the assignment topic and the course name. "
                'Reply as: {"contains_target": true|false, "evidence": "<quoted line or empty>", '
                '"learner_email": "...", "topic": "...", "course": "..."}. '
                "Use an empty string for anything not present.\n\n"
                f"<file>\n{content}\n</file>"
            ),
        }],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return json.loads(raw)


def submit(text: str, sender: str) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    if os.getenv("DASHBOARD_API_KEY"):
        headers["x-api-key"] = os.environ["DASHBOARD_API_KEY"]
    payload = {"text": text[:MAX_TEXT], "sender": sender[:100]}
    return requests.post(API_URL, json=payload, headers=headers, timeout=60)


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    submit_all = "--all" in sys.argv
    files = sorted(FOLDER.glob("*.txt"))
    if not files:
        print("No .txt files found.")
        return 1

    results = []
    for path in files:
        content = path.read_text(encoding="utf-8", errors="replace")
        info = analyze(content)
        results.append((path, content, info))
        print(
            f"{path.name}\n"
            f"  contains {TARGET_EMAIL}: {bool(info.get('contains_target'))}\n"
            f"  learner: {info.get('learner_email')}\n"
            f"  topic:   {info.get('topic')}\n"
            f"  course:  {info.get('course')}"
        )

    to_submit = [r for r in results if submit_all or r[2].get("contains_target")]
    if not to_submit:
        print(f"\nNo .txt file contains {TARGET_EMAIL}; nothing to submit (use --all to submit every file).")
        return 1

    failures = 0
    print()
    for path, content, info in to_submit:
        if info.get("contains_target"):
            sender = TARGET_EMAIL.split("@")[0]
        else:
            email = info.get("learner_email", "")
            sender = email.split("@")[0] if email else path.stem
        if dry_run:
            print(f"[dry-run] would submit {path.name} as sender '{sender}'")
            continue
        r = submit(content, sender)
        print(f"POST {path.name} (sender '{sender}') -> {r.status_code} {r.text[:200]}")
        if r.status_code != 201:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
