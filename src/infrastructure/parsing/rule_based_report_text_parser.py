from __future__ import annotations

import re

from domain.exceptions import DomainError
from domain.services.training_text_parsing import ReportDraft, ReportTextParser
from domain.value_objects.garmin_report_url import GarminReportUrl

_GARMIN_URL_RE = re.compile(r"(https://[^\s]+)")
_LOAD_RE = re.compile(r"нагрузка\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


class RuleBasedReportTextParser(ReportTextParser):
    def parse_report_text(self, *, text: str) -> ReportDraft:
        normalized = _normalize_text(text)
        warnings: list[str] = []

        garmin_url: GarminReportUrl | None = None
        urls = _GARMIN_URL_RE.findall(normalized)
        for url in urls:
            if "garmin.com" not in url:
                continue
            try:
                garmin_url = GarminReportUrl(url)
                break
            except DomainError as exc:
                warnings.append(str(exc))

        suggested_difficulty: int | None = None
        match = _LOAD_RE.search(normalized)
        if match:
            low = int(match.group(1))
            high = int(match.group(2)) if match.group(2) else low
            suggested_difficulty = round((low + high) / 2)

        # Remove URL and "нагрузка ..." from comment body if present.
        comment_body = normalized
        if garmin_url is not None:
            comment_body = comment_body.replace(str(garmin_url), "").strip()
        comment_body = _LOAD_RE.sub("", comment_body).strip()
        comment_body = re.sub(r"\n{3,}", "\n\n", comment_body).strip()

        return ReportDraft(
            garmin_url=garmin_url,
            suggested_difficulty_rating=suggested_difficulty,
            comment_body=comment_body or None,
            warnings=tuple(warnings),
        )
