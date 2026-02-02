from __future__ import annotations

import argparse
import contextlib
import sys
from typing import IO, Optional

from .canon import CanonicalizationError
from .diagnostics import apply_trace_diagnostics, trace_diagnostics
from .gateway import observe_gateway, render_gateway_event
from .project import read_events, write_events
from .render import diff_lines, explain_lines, summary_lines


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="dbl-observer")
    parser.add_argument(
        "--mode",
        choices=("diagnostic", "explain", "project", "diff", "summary", "gateway"),
        default="diagnostic",
    )
    parser.add_argument("--input", default="-")
    parser.add_argument("--output", default="-")
    parser.add_argument("--reference", default=None)
    parser.add_argument("--gateway-url", default="http://127.0.0.1:8010")
    parser.add_argument("--stream-id", default="default")
    parser.add_argument("--lane", default=None)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--format", choices=("line", "json"), default="line")
    args = parser.parse_args(argv)

    if args.mode == "gateway":
        try:
            with _open_output(args.output) as output_stream:
                try:
                    for event in observe_gateway(
                        base_url=args.gateway_url,
                        stream_id=args.stream_id,
                        lane=args.lane,
                        limit=args.limit,
                        follow=args.follow,
                        poll_interval=args.poll_interval,
                    ):
                        line = render_gateway_event(event, output_format=args.format)
                        output_stream.write(line)
                        output_stream.write("\n")
                except KeyboardInterrupt:
                    return 0
        except Exception:
            return 2
        return 0

    expect_raw = args.mode == "project"

    try:
        with _open_input(args.input) as input_stream:
            events = read_events(input_stream, expect_raw=expect_raw)
        reference_events = None
        if args.reference is not None:
            with _open_input(args.reference) as ref_stream:
                reference_events = read_events(ref_stream, expect_raw=False)
        if args.mode == "diff" and reference_events is None:
            raise ValueError("diff requires --reference")
    except ValueError:
        return 1
    except CanonicalizationError:
        return 2
    except Exception:
        return 2

    events = apply_trace_diagnostics(events, reference_events=reference_events)
    trace_diags = trace_diagnostics(events, reference_events=reference_events)

    try:
        with _open_output(args.output) as output_stream:
            if args.mode == "explain":
                _write_lines(explain_lines(events, trace_diags), output_stream)
            elif args.mode == "diff":
                _write_lines(diff_lines(events, trace_diags), output_stream)
            elif args.mode == "summary":
                _write_lines(summary_lines(events), output_stream)
            else:
                write_events(events, output_stream)
    except Exception:
        return 3

    return 0


def _open_input(path: str):
    if path == "-":
        return contextlib.nullcontext(sys.stdin)
    return open(path, "r", encoding="utf-8")


def _open_output(path: str):
    if path == "-":
        return contextlib.nullcontext(sys.stdout)
    return open(path, "w", encoding="utf-8")


def _write_lines(lines: list[str], stream: IO[str]) -> None:
    for line in lines:
        stream.write(line)
        stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
