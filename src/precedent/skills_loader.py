"""Loads Agent Skills from skills/<name>/SKILL.md.

This follows Anthropic's open Agent Skills format (the same SKILL.md convention Claude
Code itself uses) — frontmatter with `name` + `description`, body is the instructions.
Skills are content, not code: this module only parses and lists them. What a skill does
lives entirely in its SKILL.md body, executed by agent.py's generic loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    instructions: str
    path: Path


class SkillParseError(ValueError):
    pass


def _parse_skill_md(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SkillParseError(f"{path}: missing frontmatter delimiter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SkillParseError(f"{path}: malformed frontmatter — need two '---' delimiters")

    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()

    for field_name in ("name", "description"):
        if not frontmatter.get(field_name):
            raise SkillParseError(f"{path}: frontmatter missing required field '{field_name}'")

    if not body:
        raise SkillParseError(f"{path}: body (instructions) is empty")

    return Skill(
        name=frontmatter["name"],
        description=frontmatter["description"],
        instructions=body,
        path=path,
    )


def load_skills(skills_dir: Path = SKILLS_DIR) -> list[Skill]:
    """Load every skill under skills_dir. Raises on the first malformed SKILL.md rather
    than silently skipping it — a broken skill file should fail loudly at startup, not
    disappear silently and leave the agent quietly worse at routing.
    """
    skills: list[Skill] = []
    for entry in sorted(skills_dir.iterdir()):
        skill_md = entry / "SKILL.md"
        if entry.is_dir() and skill_md.exists():
            skills.append(_parse_skill_md(skill_md))
    return skills


def get_skill(name: str, skills_dir: Path = SKILLS_DIR) -> Skill | None:
    for skill in load_skills(skills_dir):
        if skill.name == name:
            return skill
    return None
