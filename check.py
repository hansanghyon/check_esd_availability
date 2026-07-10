import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import requests

URL = "https://www.lisd.net/our-district/all-departments/extended-school-day/esd-registration/current-program-availability"
STATE_FILE = Path("status.json")


def extract_lists():
    html = requests.get(URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    def get_list(heading_text):
        heading = None

        for tag in soup.find_all(["h2", "h3", "h4", "strong", "p"]):
            if heading_text in tag.get_text(" ", strip=True):
                heading = tag
                break

        if heading is None:
            return []

        ul = heading.find_next("ul")

        if ul is None:
            return []

        return sorted([
            li.get_text(" ", strip=True)
            for li in ul.find_all("li", recursive=False)
        ])

    return {
        "open": get_list("Full with an Open Waitlist"),
        "closed": get_list("Full with a Closed Waitlist"),
    }


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())

    return {
        "open": [],
        "closed": []
    }


def build_changes(old, new):

    changes = []

    added = sorted(set(new["open"]) - set(old["open"]))
    removed = sorted(set(old["open"]) - set(new["open"]))

    if added:
        changes.append(
            "Added to OPEN:\n" + "\n".join(added)
        )

    if removed:
        changes.append(
            "Removed from OPEN:\n" + "\n".join(removed)
        )

    added = sorted(set(new["closed"]) - set(old["closed"]))
    removed = sorted(set(old["closed"]) - set(new["closed"]))

    if added:
        changes.append(
            "Added to CLOSED:\n" + "\n".join(added)
        )

    if removed:
        changes.append(
            "Removed from CLOSED:\n" + "\n".join(removed)
        )

    return changes


def send_email(lines):

    msg = EmailMessage()

    msg["Subject"] = "LISD ESD Waitlist Changed"
    msg["From"] = os.environ["EMAIL_USER"]
    msg["To"] = os.environ["EMAIL_TO"]

    msg.set_content("\n\n".join(lines))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            os.environ["EMAIL_USER"],
            os.environ["EMAIL_PASSWORD"]
        )

        smtp.send_message(msg)


def main():

    new_state = extract_lists()
    old_state = load_state()

    changes = build_changes(old_state, new_state)

    if changes:
        send_email(changes)

    STATE_FILE.write_text(
        json.dumps(new_state, indent=2)
    )

    print(json.dumps(new_state, indent=2))


if __name__ == "__main__":
    main()
