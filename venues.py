"""Venue normalization + town extraction (pure functions, no network)."""
import re

STATES = r"(MD|VA|PA|NJ|DC)"
# Name-only venues whose town is stated elsewhere in the same source (noted as such in the book).
TOWN_HINTS = {
    'Venue 6': ('Aldie, VA', 'town stated elsewhere in the same source'),
    'Venue 8': ('Hometown, MD', 'town stated elsewhere in the same source'),
    'Venue 12': ('Hometown, MD', 'town stated elsewhere in the same source'),
    'Venue 15': ('Hometown, MD', 'town stated elsewhere in the same source'),
    'Venue 29': ('Washington, DC', None),
    'Venue 35': ('Ashburn, VA', None),
}
NOT_A_PLACE = {"tbd", "zoom meeting", ""}


def clean(loc):
    return re.sub(r"\s+", " ", (loc or "").replace("\n", ", ")).strip(" ,")


def split_venue(loc):
    """'Name (Field 2) - 123 Rd, Town, ST' -> (name, field, address)."""
    loc = clean(loc)
    name, addr = loc, ""
    m = re.match(r"^(.*?)\s+-\s+(\d.*)$", loc)
    if m:
        name, addr = m.group(1).strip(), m.group(2).strip()
    elif re.match(r"^\d", loc):
        name, addr = "", loc
    field = ""
    fm = re.search(r"\(([^)]*)\)", name)
    if fm:
        field = fm.group(1)
        name = (name[:fm.start()] + name[fm.end():]).strip()
    name = re.sub(r"^Hal and Berni\s+", "", name)
    return name, field, addr


def town_of(loc):
    loc = clean(loc)
    if loc in TOWN_HINTS:
        return TOWN_HINTS[loc]
    if loc.lower() in NOT_A_PLACE:
        return (None, None)
    parts = [p.strip() for p in re.split(r",", loc) if p.strip()]
    for i, p in enumerate(parts):
        m = re.match(rf"^(.*?)\s*\b{STATES}\b(\s+\d{{5}})?$", p)
        if not m:
            continue
        st, city = m.group(2), m.group(1).strip()
        if not city and i > 0:
            city = parts[i - 1]
        city = re.sub(r"\s*-\s*Turf$", "", city)
        if " - " in city:
            city = city.split(" - ")[-1].strip()
        if re.match(r"^\d", city):  # '22831 Hanson Park Drive Aldie' -> 'Aldie'
            words = city.split()
            city = words[-1]
            if words[-2:-1] and words[-2] in ("Upper", "Ellicott", "Fairfax", "Glen", "Bryn"):
                city = " ".join(words[-2:])
        return (f"{city}, {st}", None)
    return (None, None)


def venue_key(loc):
    name, field, addr = split_venue(loc)
    base = addr or name
    base = re.sub(r",?\s*(United States|US)$", "", base)
    base = re.sub(r"\s+\d{5}$", "", base)
    return re.sub(r"[^a-z0-9]+", " ", base.lower()).strip()
