import os,requests
from bs4 import BeautifulSoup
from pathlib import Path

URL="https://www.lisd.net/our-district/all-departments/extended-school-day/esd-registration/current-program-availability"
html=requests.get(URL,timeout=30).text
soup=BeautifulSoup(html,"html.parser")
text=soup.get_text("\n",strip=True)
status="NOT_LISTED"
if "Closed Waitlist" in text and "Castle Hills" in text[text.find("Closed Waitlist"):]:
    # crude section parsing
    sec=text[text.find("Closed Waitlist"):]
    end=sec.find("Open Waitlist")
    if end!=-1: sec=sec[:end]
    if "Castle Hills" in sec: status="CLOSED"
if status=="NOT_LISTED" and "Open Waitlist" in text:
    sec=text[text.find("Open Waitlist"):]
    end=sec.find("Closed Waitlist")
    if end!=-1: sec=sec[:end]
    if "Castle Hills" in sec: status="OPEN"
p=Path("status.txt")
old=p.read_text().strip() if p.exists() else "UNKNOWN"
if status!=old:
    requests.post("https://api.pushover.net/1/messages.json",data={
      "token":os.environ["PUSHOVER_TOKEN"],
      "user":os.environ["PUSHOVER_USER"],
      "title":"Castle Hills ESD Status Changed",
      "message":f"Previous: {old}\nCurrent: {status}"
    },timeout=30)
    p.write_text(status)
print(status)
