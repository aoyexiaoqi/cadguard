"""Command line interface.

Usage:

    cadguard check drawing.dxf [--rules rules.yaml] [--out report.md]
                               [--format md|json] [--png preview.png]
    cadguard --demo [--out report.md] [--dxf-out demo.dxf]

Exit codes for ``check``: 0 = no error-severity issues, 1 = at least one
error-severity issue, 2 = the drawing or rules file could not be read.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .checker import check_file
from .config import load_config
from .report import render, write_report


def _print_summary(report) -> None:
    sev = report.count_by_severity()
    print(
        "%s: %d issue(s) — error %d, warning %d, info %d"
        % (report.source, report.total, sev["error"], sev["warning"], sev["info"])
    )
    for rule_id, count in report.count_by_rule().items():
        print("  %-32s %d" % (rule_id, count))


def _run_check(args) -> int:
    try:
        config = load_config(args.rules)
    except Exception as exc:
        print("cadguard: cannot load rules: %s" % exc, file=sys.stderr)
        return 2
    try:
        report = check_file(args.file, config)
    except Exception as exc:
        print("cadguard: cannot read drawing: %s" % exc, file=sys.stderr)
        return 2
    _print_summary(report)
    if args.out:
        fmt = write_report(report, args.out, args.format)
        print("report written to %s (%s)" % (args.out, fmt))
    else:
        print(render(report, args.format or "md"))
    if args.png:
        from .render import render_png

        if render_png(args.file, args.png):
            print("preview written to %s" % args.png)
        else:
            print(
                "cadguard: PNG rendering unavailable (matplotlib missing or "
                "rendering failed); check results are unaffected",
                file=sys.stderr,
            )
    return 1 if report.error_count else 0


def _run_demo(args) -> int:
    from .demo import build_demo_drawing

    dxf_out = Path(args.dxf_out or "cadguard_demo.dxf")
    out = Path(args.out or "cadguard_demo_report.md")
    build_demo_drawing(dxf_out)
    print("demo drawing written to %s" % dxf_out)
    try:
        config = load_config(args.rules)
        report = check_file(dxf_out, config)
    except Exception as exc:
        print("cadguard: demo check failed: %s" % exc, file=sys.stderr)
        return 2
    report.source = str(dxf_out)
    _print_summary(report)
    fmt = write_report(report, out, args.format)
    print("report written to %s (%s)" % (out, fmt))
    print("note: the demo drawing plants one violation per rule on purpose.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cadguard",
        description="Rule-based checker for DXF engineering drawings.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="generate a sample DXF with planted violations and check it",
    )
    parser.add_argument("--dxf-out", help="where to write the demo DXF (with --demo)")
    sub = parser.add_subparsers(dest="command")

    p_check = sub.add_parser("check", help="check a DXF drawing")
    p_check.add_argument("file", help="path to the .dxf file")
    p_check.add_argument("--rules", help="rules config (.yaml/.yml/.json)")
    p_check.add_argument("--out", help="report output path (.md or .json)")
    p_check.add_argument("--format", choices=["md", "json"], help="report format")
    p_check.add_argument("--png", help="also render a PNG preview (needs matplotlib)")

    p_demo = sub.add_parser("demo", help="same as --demo")
    p_demo.add_argument("--rules", help="rules config (.yaml/.yml/.json)")
    p_demo.add_argument("--out", help="report output path (.md or .json)")
    p_demo.add_argument("--format", choices=["md", "json"], help="report format")
    p_demo.add_argument("--dxf-out", help="where to write the demo DXF")

    parser.add_argument("--rules", help="rules config (.yaml/.yml/.json)")
    parser.add_argument("--out", help="report output path (.md or .json)")
    parser.add_argument("--format", choices=["md", "json"], help="report format")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.demo or args.command == "demo":
        return _run_demo(args)
    if args.command == "check":
        return _run_check(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
