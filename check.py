import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

URL = "https://www.lisd.net/our-district/all-departments/extended-school-day/esd-registration/current-program-availability"

STATE_FILE = Path("status.json")


def extract_lists():
    html = requests.get(URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    def get_list(heading_text):
        # Find the heading containing the text
        heading = None
        for tag in soup.find_all(["h2", "h3", "h4", "p", "strong"]):
            if heading_text in tag.get_text(" ", strip=True):
                heading = tag
                break

        if heading is None:
            return []

        # Find the first <ul> after that heading
        ul = heading.find_next("ul")
        if ul is None:
            return []

        return sorted(
            li.get_text(" ", strip=True)
            for li in ul.find_all("li", recursive=False)
        )

    return {
        "open": get_list("Full with an Open Waitlist"),
        "closed": get_list("Full with a Closed Waitlist"),
    }


def diff(old, new):
    return {
        "added_open": sorted(set(new["open"]) - set(old["open"])),
        "removed_open": sorted(set(old["open"]) - set(new["open"])),
        "added_closed": sorted(set(new["closed"]) - set(old["closed"])),
        "removed_closed": sorted(set(old["closed"]) - set(new["closed"])),
    }


new_state = extract_lists()

if STATE_FILE.exists():
    old_state = json.loads(STATE_FILE.read_text())
else:
    old_state = {"open": [], "closed": []}

changes = diff(old_state, new_state)

if any(changes.values()):

    msg = []

    for key, title in [
        ("added_open", "Added to OPEN"),
        ("removed_open", "Removed from OPEN"),
        ("added_closed", "Added to CLOSED"),
        ("removed_closed", "Removed from CLOSED"),
    ]:
        if changes[key]:
            msg.append(title + ":\n" + "\n".join(changes[key]))

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "LISD ESD Waitlist Changed",
            "message": "\n\n".join(msg),
        },
        timeout=30,
    )

STATE_FILE.write_text(json.dumps(new_state, indent=2))

print(json.dumps(new_state, indent=2))