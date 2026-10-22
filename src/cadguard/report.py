"""Check report: summary counts plus Markdown / JSON rendering."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from .models import Issue


@dataclass
class CheckReport:
    source: str
    issues: List[Issue] = field(default_factory=list)

    # -- summaries ---------------------------------------------------------
    @property
    def total(self) -> int:
        return len(self.issues)

    def count_by_severity(self) -> dict:
        counts = Counter(i.severity for i in self.issues)
        return {sev: counts.get(sev, 0) for sev in ("error", "warning", "info")}

    def count_by_rule(self) -> dict:
        return dict(sorted(Counter(i.rule_id for i in self.issues).items()))

    @property
    def error_count(self) -> int:
        return self.count_by_severity()["error"]

    # -- rendering ---------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "summary": {
                "total": self.total,
                "by_severity": self.count_by_severity(),
                "by_rule": self.count_by_rule(),
            },
            "issues": [issue.to_dict() for issue in self.issues],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = []
        lines.append("# CADGuard 图纸检查报告 / Drawing Check Report")
        lines.append("")
        lines.append("- 文件 / File: `%s`" % self.source)
        lines.append("- 问题总数 / Total issues: **%d**" % self.total)
        sev = self.count_by_severity()
        lines.append(
            "- 按严重度 / By severity: error %d, warning %d, info %d"
            % (sev["error"], sev["warning"], sev["info"])
        )
        lines.append("")
        lines.append("## 汇总 / Summary by rule")
        lines.append("")
        lines.append("| 规则 Rule | 数量 Count |")
        lines.append("| --- | --- |")
        by_rule = self.count_by_rule()
        if by_rule:
            for rule_id, count in by_rule.items():
                lines.append("| %s | %d |" % (rule_id, count))
        else:
            lines.append("| — | 0 |")
        lines.append("")
        lines.append("## 问题明细 / Issues")
        lines.append("")
        if not self.issues:
            lines.append("未发现问题 / No issues found.")
        else:
            lines.append("| # | 规则 Rule | 严重度 Severity | 实体 Entity | Handle | 位置 Location | 说明 Message |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for idx, issue in enumerate(self.issues, 1):
                location = ""
                if issue.location is not None:
                    location = "%.3f, %.3f" % issue.location
                message = issue.message.replace("|", "\\|")
                lines.append(
                    "| %d | %s | %s | %s | %s | %s | %s |"
                    % (
                        idx,
                        issue.rule_id,
                        issue.severity,
                        issue.entity_type or "",
                        issue.handle or "",
                        location,
                        message,
                    )
                )
        lines.append("")
        return "\n".join(lines)


def infer_format(out_path: Optional[Union[str, Path]], default: str = "md") -> str:
    if out_path is not None:
        suffix = Path(out_path).suffix.lower()
        if suffix == ".json":
            return "json"
        if suffix in (".md", ".markdown"):
            return "md"
    return default


def render(report: CheckReport, fmt: str) -> str:
    if fmt == "json":
        return report.to_json()
    return report.to_markdown()


def write_report(report: CheckReport, out_path: Union[str, Path], fmt: Optional[str] = None) -> str:
    """Write the report to ``out_path``; returns the format used."""
    fmt = fmt or infer_format(out_path)
    Path(out_path).write_text(render(report, fmt), encoding="utf-8")
    return fmt
