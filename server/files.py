"""Loads the gm/ and rulesets/ markdown files from this repository, and the adventures from the PRIVATE adventures repository
(or from a local folder when ADVENTURES_DIR is set), with their front matter."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

import yaml

from . import config

_FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def split_front_matter(text: str):
    m = _FM.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end():]


_TAG = re.compile(r"^<!--\s*(.*?)\s*-->\s*$")
_HEADING = re.compile(r"^(#{1,6}) ")


def _parse_tag(body: str):
    """'for: setup, play; needs: generated' -> ({'setup', 'play'}, {'generated'}). Either part may be missing."""
    use, needs = None, set()
    for part in body.split(";"):
        key, _, val = part.partition(":")
        items = {x.strip() for x in val.split(",") if x.strip()}
        if key.strip() == "for":
            use = items
        elif key.strip() == "needs":
            needs = items
    return use, needs


def select_sections(text: str, profile: str | None = None, flags=()) -> str:
    """TLR-05-007: a document is sectioned by purpose. A heading may be followed (within two lines) by a tag comment such as
    `<!-- for: setup, play; needs: illustrations -->`. The section (the heading and everything under it, sub-sections included, up to the
    next heading of the same or a higher level) is kept only when `profile` is one of the `for` names and every `needs` name is in `flags`.
    An untagged section is always kept. The tag lines themselves are removed. With `profile` None nothing is left out (tags are still removed).
    The profiles are `turn` (the turn closes), `play` (a request in a running game) and `setup` (game setup, characters, joining)."""
    out, lines, i, skip_level, fence = [], text.split("\n"), 0, None, False
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else _HEADING.match(line)
        if m:
            level = len(m.group(1))
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None:
                tag = None
                for j in (i + 1, i + 2):
                    t = _TAG.match(lines[j]) if j < len(lines) else None
                    if t and ("for:" in t.group(1) or "needs:" in t.group(1)):
                        tag = (j, _parse_tag(t.group(1)))
                        break
                if tag:
                    j, (use, needs) = tag
                    del lines[j]
                    if profile is not None and ((use is not None and profile not in use) or not needs <= set(flags)):
                        skip_level = level
        if skip_level is None:
            out.append(line)
        i += 1
    return "\n".join(out)


@lru_cache(maxsize=None)
def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _parse(name: str, text: str, folder: str):
    meta, body = split_front_matter(text)
    if not meta.get("id"):
        return None
    meta = dict(meta)
    meta["file"] = f"{folder}/{name}"
    return meta["id"], {"meta": meta, "body": body, "path": meta["file"]}


def _list(directory: Path):
    out = {}
    if not directory or not directory.exists():
        return out
    for p in sorted(directory.glob("*.md")):
        r = _parse(p.name, read(str(p)), directory.name)
        if r:
            out[r[0]] = r[1]
    return out


def rulesets():
    return _list(config.RULESETS_DIR)


class AdventureSourceError(Exception):
    """The private adventures repository could not be read."""


_cache = {"at": 0.0, "key": None, "data": {}}


_seed_cache = {"at": 0.0, "key": None, "data": {}}


def clear_adventure_cache():
    _cache.update({"at": 0.0, "key": None, "data": {}})
    _seed_cache.update({"at": 0.0, "key": None, "data": {}})


def _github_get(url: str, raw: bool = False) -> bytes:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise AdventureSourceError("GITHUB_TOKEN is not set, so the private adventures repository cannot be read")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}", "User-Agent": "FabulA",
        "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read()
    except Exception as e:  # network, 401, 403, 404
        raise AdventureSourceError(f"could not read the adventures repository ({type(e).__name__})") from None


def _from_github() -> dict:
    repo, ref = config.ADVENTURES_REPO, urllib.parse.quote(config.ADVENTURES_REF)
    base = f"https://api.github.com/repos/{repo}/contents"
    listing = json.loads(_github_get(f"{base}/?ref={ref}"))
    out = {}
    for item in listing:
        name = item.get("name", "")
        if item.get("type") != "file" or not name.endswith(".md") or name.lower() == "readme.md":
            continue
        text = _github_get(f"{base}/{urllib.parse.quote(name)}?ref={ref}", raw=True).decode("utf-8")
        r = _parse(name, text, "rpg_adventures")
        if r:
            out[r[0]] = r[1]
    return out


def adventure_files():
    """Adventure files by id. Cached for ADVENTURES_CACHE_SECONDS; a stale copy is served if the repository is unreachable."""
    if config.ADVENTURES_DIR:
        return _list(config.ADVENTURES_DIR)
    key = (config.ADVENTURES_REPO, config.ADVENTURES_REF)
    now = time.time()
    if _cache["key"] == key and now - _cache["at"] < config.ADVENTURES_CACHE_SECONDS:
        return _cache["data"]
    try:
        data = _from_github()
    except AdventureSourceError:
        if _cache["key"] == key and _cache["data"]:
            return _cache["data"]
        raise
    _cache.update({"at": now, "key": key, "data": data})
    return data


def _seeds_from_github() -> dict:
    repo, ref = config.ADVENTURES_REPO, urllib.parse.quote(config.ADVENTURES_REF)
    base = f"https://api.github.com/repos/{repo}/contents/{config.ADVENTURE_SEEDS_FOLDER}"
    try:
        listing = json.loads(_github_get(f"{base}?ref={ref}"))
    except AdventureSourceError:
        return {}  # no seeds folder (or not readable): there are simply no seeds
    out = {}
    for item in listing if isinstance(listing, list) else []:
        name = item.get("name", "")
        if item.get("type") != "file" or not name.endswith(".md") or name.lower() == "readme.md":
            continue
        text = _github_get(f"{base}/{urllib.parse.quote(name)}?ref={ref}", raw=True).decode("utf-8")
        r = _parse(name, text, f"rpg_adventures/{config.ADVENTURE_SEEDS_FOLDER}")
        if r:
            out[r[0]] = r[1]
    return out


def seed_files():
    """Adventure seeds by id: files in the `seeds/` folder of the adventures repository. A seed's body has spoilers (it is given only to the
    client that writes the adventure); its front matter `summary` is the spoiler-free line players choose from."""
    if config.ADVENTURES_DIR:
        return _list(config.ADVENTURES_DIR / config.ADVENTURE_SEEDS_FOLDER)
    key = (config.ADVENTURES_REPO, config.ADVENTURES_REF)
    now = time.time()
    if _seed_cache["key"] == key and now - _seed_cache["at"] < config.ADVENTURES_CACHE_SECONDS:
        return _seed_cache["data"]
    try:
        data = _seeds_from_github()
    except AdventureSourceError:
        if _seed_cache["key"] == key and _seed_cache["data"]:
            return _seed_cache["data"]
        raise
    _seed_cache.update({"at": now, "key": key, "data": data})
    return data


def gm_file(name: str) -> str:
    return read(str(config.GM_DIR / name))


def adventure_record_from_file(entry: dict) -> dict:
    m = entry["meta"]
    return {
        "id": m["id"], "title": m.get("title", m["id"]), "source": "file",
        "file": m["file"], "content": None, "ruleset_id": m.get("ruleset"),
        "generation": m.get("generation", "supplied"), "era": m.get("era"),
        "players": m.get("players", {"min": 1, "max": 5}),
        "recommended": m.get("recommended", {}),
        "language": m.get("language", "en"),
        "summary": m.get("summary", ""), "seed": None, "owner_player_id": None,
        "pregenerated": m.get("pregenerated", []),
    }


_PART_A = re.compile(r"^# PART A", re.M)
_PART_B = re.compile(r"^# PART B", re.M)


def player_safe_part(body: str) -> str:
    """Only Part A: from the `# PART A` heading up to `# PART B`. The introduction above Part A is NOT shown (it may carry spoilers).
    If either marker is missing, nothing is player-safe."""
    a, b = _PART_A.search(body or ""), _PART_B.search(body or "")
    return body[a.start():b.start()].rstrip() if a and b and a.start() < b.start() else ""


def client_task_sections() -> dict:
    """Splits gm/client_tasks.md into COMMON and one section per task."""
    text = split_front_matter(gm_file("client_tasks.md"))[1]
    parts = re.split(r"^## (COMMON.*|TASK: \w+)\s*$", text, flags=re.M)
    out = {}
    for i in range(1, len(parts) - 1, 2):
        name = parts[i]
        key = "common" if name.startswith("COMMON") else name.split(":")[1].strip()
        out[key] = parts[i + 1].strip()
    return out


def setup_guide_sections() -> dict:
    """gm/setup_guide.md split by '## [key] Title'. Returns {key: {"title", "text"}}; the intro is under 'intro'."""
    text = split_front_matter(gm_file("setup_guide.md"))[1]
    parts = re.split(r"^## \[(\w+)\] (.*)$", text, flags=re.M)
    out = {"intro": {"title": "Player Setup Guide", "text": parts[0].strip()}}
    for i in range(1, len(parts) - 2, 3):
        out[parts[i]] = {"title": parts[i + 1].strip(), "text": parts[i + 2].strip().strip("-").strip()}
    return out


def ruleset_contract_text() -> str:
    return split_front_matter(gm_file("ruleset_contract.md"))[1]


def ruleset_outline(ruleset_id="fear_itself") -> list:
    """The section headings of a reference ruleset, as a model for a conversion."""
    rs = rulesets().get(ruleset_id)
    return re.findall(r"^#{2,3} .+$", rs["body"], flags=re.M) if rs else []


GUIDES = {
    "player-client-guide": ("guide_player_client.md", "How to use the engine (tools, order of calls, work packages, common mistakes)"),
    "players-guide": ("setup_guide.md", "The guide for a new player (topics: start, choose, character, commands, turns, autonomous, death, mechanics)"),
    "import-ruleset": ("guide_import_ruleset.md", "Converting a game system from a document into a ruleset (host approves it)"),
    "create-character": ("guide_create_character.md", "Making a character for a game"),
    "create-game": ("guide_create_game.md", "Starting a game from an adventure"),
    "generate-adventure": ("guide_generate_adventure.md", "Writing or importing an adventure"),
    "mcp-guide": ("mcp_instructions.md", "The short instructions the server sends when a client connects"),
    "narrator": ("player_client_brief.md", "How to narrate, the three artifacts, pictures, what to remember"),
}


def guide_text(name: str) -> str:
    return split_front_matter(gm_file(GUIDES[name][0]))[1]
