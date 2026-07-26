# Build hook: generate long_description from README files,
# stripping language-switcher headers.
# All other metadata lives in pyproject.toml.

from setuptools import setup


def _build_long_description() -> str:
    import re
    parts = []
    for readme in ("README.md", "README.zh.md"):
        with open(readme, encoding="utf8") as f:
            parts.append("".join(f.readlines()[6:]))
    desc = "\n***\n\n".join(parts)
    with open("xbot/plugins/ssh/version.py", encoding="utf8") as f:
        m = re.search(r"__version__[^'\"\\]+['\"]([^'\"]+)", f.read())
        version = m.group(1) if m else "0.2.2"
    desc = desc.replace("/tree/master/", f"/tree/v{version}/")
    return desc


setup(
    long_description=_build_long_description(),
    long_description_content_type="text/markdown",
)
