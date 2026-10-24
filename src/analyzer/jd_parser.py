
"""Split a job description into required vs preferred sections (heuristic v1)."""
from __future__ import annotations

import re

PREFERRED_HEADER = re.compile(
    r"^\W*(preferred(?:\s+skills?)?|nice[\s-]*to[\s-]*have|"
    r"bonus|good to have|a plus|desirable|nice if you|plus(es)?)\b",
    re.IGNORECASE,
)

REQUIRED_HEADER = re.compile(
    r"^\W*(requirements?|required(?:\s+skills?)?|qualifications?|"
    r"must[\s-]*have|"
    r"what you(?:'|â€™)?ll need|what you(?:'|â€™)?ll do|"
    r"what you(?:'|â€™)?ll be doing|what you(?:'|â€™)?re looking for|"
    r"who you are|responsibilities|you have|minimum|"
    r"about the role|about the job|the role|what you will do)\b",
    re.IGNORECASE,
)

PREFERRED_INLINE = re.compile(
    r"\b(preferred|nice to have|a plus|bonus|is a plus|desirable)\b",
    re.IGNORECASE,
)

from .skills import category_of, find_mentions  # noqa: E402

_SEPARATOR = re.compile(r"\s*(?:,\s*or\s+|or\s+|,\s*)", re.IGNORECASE)

# Inline section headings must end in a colon so ordinary sentences that
# mention these words aren't accidentally treated as section boundaries.
_INLINE_SECTION_HEADER = re.compile(
    r"(?i)\b("
    r"required(?:\s+skills?)?|requirements?|qualifications?|must[\s-]*have|"
    r"preferred(?:\s+skills?)?|nice[\s-]*to[\s-]*have|"
    r"bonus|good to have|a plus|desirable"
    r")\s*:"
)


def _heading_mode(heading: str) -> str:
    """Return the section selected by a recognized heading."""
    normalized = " ".join(heading.lower().split())

    if (
        normalized.startswith("preferred")
        or normalized.startswith("nice")
        or normalized in {"bonus", "good to have", "a plus", "desirable"}
    ):
        return "preferred"

    return "required"


def split_jd(text: str) -> tuple[str, str]:
    """Return (required_text, preferred_text).

    Standalone section headings change the current section.
    Inline headings such as 'Required: Python, SQL' preserve their content.
    Multiple inline headings on one line are split into their own sections.
    """
    required: list[str] = []
    preferred: list[str] = []
    mode = "required"

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        matches = list(_INLINE_SECTION_HEADER.finditer(stripped))

        if matches:
            # Preserve text before the first inline heading in the current
            # section, if any.
            prefix = stripped[:matches[0].start()].strip()
            if prefix:
                (preferred if mode == "preferred" else required).append(prefix)

            for index, match in enumerate(matches):
                mode = _heading_mode(match.group(1))

                content_start = match.end()
                content_end = (
                    matches[index + 1].start()
                    if index + 1 < len(matches)
                    else len(stripped)
                )
                content = stripped[content_start:content_end].strip()

                if content:
                    (preferred if mode == "preferred" else required).append(
                        content
                    )

            continue

        preferred_match = PREFERRED_HEADER.match(stripped)
        required_match = REQUIRED_HEADER.match(stripped)

        # A standalone heading changes the current section.
        if preferred_match:
            remainder = stripped[preferred_match.end():].strip()
            if not remainder or remainder == ":":
                mode = "preferred"
                continue
            if remainder.startswith(":"):
                mode = "preferred"
                stripped = remainder[1:].strip()
                if not stripped:
                    continue

        elif required_match:
            remainder = stripped[required_match.end():].strip()
            if not remainder or remainder == ":":
                mode = "required"
                continue
            if remainder.startswith(":"):
                mode = "required"
                stripped = remainder[1:].strip()
                if not stripped:
                    continue

        is_pref = mode == "preferred" or bool(PREFERRED_INLINE.search(stripped))
        (preferred if is_pref else required).append(stripped)

    return "\n".join(required), "\n".join(preferred)


def build_requirements(
    text: str, use_or_groups: bool = True
) -> list[frozenset[str]]:
    """Turn JD text into requirements, supporting same-category alternatives.

    'FastAPI or Flask' -> {fastapi, flask}
    'Python, SQL' -> {python}, {sql}
    Alternatives must share a taxonomy category.
    """
    requirements: list[frozenset[str]] = []

    for line in text.splitlines():
        mentions = find_mentions(line)
        if not mentions:
            continue

        if not use_or_groups:
            requirements.extend(frozenset({m.skill}) for m in mentions)
            continue

        chain = [mentions[0]]
        has_or = False

        def close_chain() -> None:
            skills = list(dict.fromkeys(m.skill for m in chain))
            if has_or and len(skills) > 1:
                requirements.append(frozenset(skills))
            else:
                requirements.extend(frozenset({skill}) for skill in skills)

        for prev, cur in zip(mentions, mentions[1:]):
            between = line[prev.end:cur.start]
            same_category = category_of(cur.skill) == category_of(chain[0].skill)

            if same_category and _SEPARATOR.fullmatch(between):
                chain.append(cur)
                has_or = has_or or "or" in between.lower()
            else:
                close_chain()
                chain, has_or = [cur], False

        close_chain()

    unique = list(dict.fromkeys(requirements))
    singles = {next(iter(req)) for req in unique if len(req) == 1}
    return [
        req for req in unique
        if len(req) == 1 or not (req & singles)
    ]
