# Build hook: generate long_description from README files,
# stripping language-switcher headers.
# All other metadata lives in pyproject.toml.
import re

from setuptools import setup


def _build_long_description() -> str:
    desc = ""
    for readme in ("README.md", "README.zh.md"):
        if desc:
            desc += "\n***\n\n"
        with open(readme, encoding="utf8") as f:
            desc += "".join(f.readlines()[6:])
    with open("pyproject.toml", encoding="utf8") as f:
        m = re.search(r'''^version\s*=\s*["']([^"']+)''', f.read(), re.M)
        version = m.group(1) if m else ""
    desc = desc.replace("/tree/master/", f"/tree/v{version}/")
    return desc


setup(
    long_description=_build_long_description(),
    long_description_content_type="text/markdown",
)
