import re
from datetime import datetime
import pytz

CST = pytz.timezone("America/Chicago")

def parse_backstabbr_email(body):
    state = {
        "phase": None,
        "season": None,
        "year": None,
        "next_adj": None,
        "retreats": [],
        "builds": {},
    }

    # Phase line: "Fall 1903 — Orders"
    phase_match = re.search(r"(Spring|Summer|Fall|Winter)\s+(\d{4}).*?(Orders|Retreats|Builds|Adjustments)", body)
    if phase_match:
        state["season"] = phase_match.group(1)
        state["year"] = int(phase_match.group(2))
        state["phase"] = phase_match.group(3)

    # Next adjudication time
    adj_match = re.search(r"Next adjudication[: ]+([A-Za-z]+\s+\d{1,2}.*?CST)", body)
    if adj_match:
        try:
            dt = datetime.strptime(adj_match.group(1), "%B %d at %I:%M %p CST")
            state["next_adj"] = CST.localize(dt)
        except:
            pass

    # Retreats: "France must retreat 1 unit"
    retreat_matches = re.findall(r"([A-Za-z]+)\s+must\s+retreat", body)
    state["retreats"] = retreat_matches

    # Builds: "Germany may build 2 units"
    build_matches = re.findall(r"([A-Za-z]+)\s+may\s+build\s+(\d+)", body)
    for power, num in build_matches:
        state["builds"][power] = int(num)

    return state
