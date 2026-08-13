#!/usr/bin/env python3
"""Updates the "Latest Projects" section of the profile README.

Queries the GitHub API for the user's repositories and rewrites the
markdown between the LATEST_PROJECT start/end markers to showcase:
  - the most recently created repository (Latest Added)
  - the most recently updated repository (Latest Updated)
"""

import html
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- LATEST_PROJECT:START -->"
END = "<!-- LATEST_PROJECT:END -->"

USERNAME = os.getenv("GITHUB_USER", "Manojgodavarthii")
TOKEN = os.getenv("GITHUB_TOKEN", "")
API_URL = (
    f"https://api.github.com/users/{USERNAME}/repos"
    "?sort=updated&direction=desc&per_page=100"
)


def fetch_repos():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "github-profile-readme"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(value):
    return html.escape(str(value or ""), quote=False)


def format_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")
    except (TypeError, ValueError):
        return ""


def clean_description(value):
    if not value:
        return "*No description provided yet.*"
    text = " ".join(str(value).split())
    if len(text) > 160:
        text = text[:157].rstrip() + "..."
    return esc(text)


def card(accent, badge_label, badge_color, repo, color, width="50%"):
    name = esc(repo["name"])
    url = repo["html_url"]
    description = clean_description(repo.get("description"))
    language = repo.get("language")
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    updated = format_date(repo.get("pushed_at") or repo.get("updated_at"))
    badge_label_encoded = badge_label.replace(" ", "%20")

    tags = f"<kbd>{esc(language)}</kbd>" if language else ""
    if stars or forks:
        tags += (
            f'&nbsp;&nbsp;<img src="https://img.shields.io/github/stars/{USERNAME}/'
            f'{repo["name"]}?style=flat-square&logo=github&logoColor=white&color={color}" '
            f'alt="Stars" />'
            f'&nbsp;<img src="https://img.shields.io/github/forks/{USERNAME}/'
            f'{repo["name"]}?style=flat-square&logo=github&logoColor=white&color={color}" '
            f'alt="Forks" />'
        )
    updated_line = f'<p align="left"><b>Last updated:</b> {updated}</p>' if updated else ""

    return f"""    <td width="{width}" valign="top" style="background-color: rgba(102, 146, 240, 0.08); border: 1px solid rgba(122, 162, 247, 0.25); border-radius: 10px; padding: 25px;">
      <p align="center">
        <img src="https://img.shields.io/badge/-{badge_label_encoded}-{badge_color}?style=flat-square&logo=github&logoColor=white" alt="{badge_label} Badge" />
      </p>
      <h3 align="center"><font color="#{color}">{accent} {name}</font></h3>
      <p align="left">{description}</p>
      {updated_line}
      <p align="center">{tags}</p>
      <p align="center">
        <a href="{url}">
          <img src="https://img.shields.io/badge/Explore%20Repository-{color}?style=for-the-badge&logo=github&logoColor=white" alt="Explore Repository" />
        </a>
      </p>
    </td>"""


def build_section(latest_added, latest_updated):
    if latest_added is None and latest_updated is None:
        body = "No public repositories found yet."
    elif latest_added["id"] == latest_updated["id"]:
        single = card("🚀", "Latest Project", "7aa2f7", latest_added, "7aa2f7", width="100%")
        body = f"""<table align="center" style="border-collapse: separate; border-spacing: 15px;">
  <tr>
{single}
  </tr>
</table>"""
    else:
        added = card("🚀", "Latest Added", "7aa2f7", latest_added, "7aa2f7")
        updated = card("🔄", "Most Recently Updated", "bb9af7", latest_updated, "bb9af7")
        body = f"""<table align="center" style="border-collapse: separate; border-spacing: 15px;">
  <tr>
{added}
{updated}
  </tr>
</table>"""
    return (
        f"{START}\n"
        f'<h2 align="center"><font color="#7aa2f7">⭐ Latest Projects</font></h2>\n'
        f"\n"
        f"{body}\n"
        f"{END}"
    )


def update_readme(section):
    readme = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(readme):
        new_readme = pattern.sub(section, readme)
    else:
        heading = '<h2 align="center"><font color="#7aa2f7">🛠️ Featured Projects'
        idx = readme.find(heading)
        if idx == -1:
            idx = readme.find("## Featured Projects")
        if idx != -1:
            new_readme = readme[:idx] + section + "\n\n" + readme[idx:]
        else:
            new_readme = readme.rstrip() + "\n\n" + section + "\n"
    README.write_text(new_readme, encoding="utf-8")


def main():
    repos = fetch_repos()
    own = [
        r
        for r in repos
        if not r.get("fork") and r.get("name") != USERNAME
    ]
    fallback = own or [r for r in repos if not r.get("fork")] or repos
    if not fallback:
        section = build_section(None, None)
    else:
        latest_added = max(fallback, key=lambda r: r.get("created_at") or "")
        distinct = [
            r for r in fallback if r.get("id") != latest_added.get("id")
        ]
        if distinct:
            latest_updated = max(
                distinct,
                key=lambda r: r.get("pushed_at") or r.get("updated_at") or "",
            )
        else:
            latest_updated = latest_added
        section = build_section(latest_added, latest_updated)
    update_readme(section)
    print("README latest project section updated.")


if __name__ == "__main__":
    main()
