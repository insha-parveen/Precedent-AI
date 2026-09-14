"""No database, no API key, no network needed to run these — that's deliberate.
This is the first thing to run after cloning, and the first thing Claude Code should
run before writing any new code against the scaffold. See CLAUDE.md.
"""
from pathlib import Path

import pytest

from src.precedent.skills_loader import SkillParseError, load_skills

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"

EXPECTED_SKILLS = {"find-precedent", "negotiation-check", "risk-flag"}


def test_all_expected_skills_are_present():
    names = {s.name for s in load_skills(SKILLS_DIR)}
    assert names == EXPECTED_SKILLS, (
        f"expected {EXPECTED_SKILLS}, found {names} — did a SKILL.md get renamed or "
        "moved without updating this test?"
    )


def test_every_skill_has_a_nonempty_description():
    for skill in load_skills(SKILLS_DIR):
        assert len(skill.description) > 20, (
            f"{skill.name}: description too short to be useful for routing — the "
            "description is literally what the agent matches the user's query against."
        )


def test_every_skill_has_step_by_step_instructions():
    for skill in load_skills(SKILLS_DIR):
        assert "## Steps" in skill.instructions or "## Output format" in skill.instructions, (
            f"{skill.name}: instructions should have a clear steps/output-format "
            "structure, not free-form prose — see any existing skill for the pattern."
        )


def test_malformed_skill_md_raises_not_silently_skips(tmp_path):
    bad_skill = tmp_path / "broken-skill"
    bad_skill.mkdir()
    (bad_skill / "SKILL.md").write_text("no frontmatter here, just text")

    with pytest.raises(SkillParseError):
        load_skills(tmp_path)
