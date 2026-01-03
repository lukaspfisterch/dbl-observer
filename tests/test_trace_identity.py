import json
import os
import subprocess
import sys
from pathlib import Path


def _env_with_src_path() -> dict[str, str]:
    env = dict(os.environ)
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}{os.pathsep}{existing}"
    return env


def test_trace_identity_event_id_zero_is_accepted(tmp_path: Path) -> None:
    rows = [
        {
            "event_id": 0,
            "source": "dbl-observer",
            "artifact": "trace_identity",
            "payload": {"trace_id": "t-1", "observed_at": "2025-12-30T17:40:17+01:00"},
        },
        {
            "event_id": 1,
            "source": "adapter",
            "artifact": "record",
            "payload": {"x": 1},
        },
    ]
    rfile = tmp_path / "raw.jsonl"
    rfile.write_text(
        "\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(rfile),
            "--mode",
            "project",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    second = json.loads(lines[1])
    assert "ordering_gap_observed" not in second["diagnostics"]
    assert "non_monotonic_event_id_observed" not in second["diagnostics"]
