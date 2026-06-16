"""Smoke tests para hermes-sre-toolkit."""
import pytest
from pathlib import Path


def test_skills_dir_exists():
    """skills/ deve existir e ter skills SRE."""
    skills_dir = Path(__file__).parent.parent / "skills"
    assert skills_dir.exists()
    skills = [d for d in skills_dir.iterdir() if d.is_dir()]
    assert len(skills) > 0


def test_scripts_dir():
    """scripts/ SRE devem existir."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    if scripts_dir.exists():
        sh = list(scripts_dir.glob("*.sh"))
        py = list(scripts_dir.glob("*.py"))
        assert len(sh) + len(py) > 0, "scripts/ vazio"
