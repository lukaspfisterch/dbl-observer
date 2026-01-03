import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dbl_observer.canon import canonical_json_bytes
from dbl_observer.digest import sha256_hex


def _mk_row(event_id: int, source: str, artifact: str, payload: dict, diagnostics=None) -> dict:
    diagnostics = diagnostics or []
    canon = canonical_json_bytes(payload)
    return {
        "event_id": event_id,
        "source": source,
        "artifact": artifact,
        "payload": payload,
        "canon_len": len(canon),
        "digest": "sha256:" + sha256_hex(canon),
        "diagnostics": diagnostics,
    }


def _env_with_src_path() -> dict[str, str]:
    env = dict(os.environ)
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}{os.pathsep}{existing}"
    return env


@pytest.mark.parametrize(
    "stdin_text,expected_exit",
    [
        ("{", 1),
        ("not-jsonl\n", 1),
    ],
)
def test_cli_exit_code_1_for_unparsable_input(stdin_text: str, expected_exit: int):
    result = subprocess.run(
        [sys.executable, "-m", "dbl_observer.cli", "--input", "-"],
        input=stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result.returncode == expected_exit


def test_cli_exit_code_0_for_valid_trace(tmp_path: Path):
    rows = [
        _mk_row(1, "adapter", "record", {"subject": "user"}),
        _mk_row(2, "adapter", "record", {"resource": "file"}),
    ]
    tfile = tmp_path / "trace.jsonl"
    tfile.write_text(
        "\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(tfile),
            "--mode",
            "diagnostic",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result.returncode == 0


def test_cli_exit_code_3_for_unwritable_output(tmp_path: Path):
    rows = [_mk_row(1, "adapter", "record", {"subject": "user"})]
    tfile = tmp_path / "trace.jsonl"
    tfile.write_text(
        "\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + "\n",
        encoding="utf-8",
    )

    out_path = tmp_path
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(tfile),
            "--output",
            str(out_path),
            "--mode",
            "diagnostic",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result.returncode == 3


def test_cli_exit_code_2_for_float_payload_in_project_mode():
    stdin_text = '{"event_id":1,"source":"adapter","artifact":"record","payload":{"x":1.5}}\n'
    result = subprocess.run(
        [sys.executable, "-m", "dbl_observer.cli", "--input", "-", "--mode", "project"],
        input=stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result.returncode == 2


def test_cli_exit_code_1_for_unknown_fields_in_trace(tmp_path: Path):
    row = _mk_row(1, "adapter", "record", {"subject": "user"})
    row["extra"] = "not-allowed"
    tfile = tmp_path / "trace.jsonl"
    tfile.write_text(
        json.dumps(row, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(tfile),
            "--mode",
            "diagnostic",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result.returncode == 1


def test_cli_exit_code_1_for_unknown_fields_in_raw(tmp_path: Path):
    row = {"event_id": 1, "source": "adapter", "artifact": "record", "payload": {"x": 1}, "extra": True}
    rfile = tmp_path / "raw.jsonl"
    rfile.write_text(
        json.dumps(row, ensure_ascii=True) + "\n",
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
    )
    assert result.returncode == 1


def test_cli_accepts_payload_list_in_project_mode():
    stdin_text = '{"event_id":1,"source":"adapter","artifact":"record","payload":[1,"a",true]}\n'
    result = subprocess.run(
        [sys.executable, "-m", "dbl_observer.cli", "--input", "-", "--mode", "project"],
        input=stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result.returncode == 0


def test_cli_exit_code_is_deterministic_for_invalid_input():
    stdin_text = '{"event_id":1,"source":"adapter","artifact":"record","payload":{"x":1.5}}\n'
    result_1 = subprocess.run(
        [sys.executable, "-m", "dbl_observer.cli", "--input", "-", "--mode", "project"],
        input=stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    result_2 = subprocess.run(
        [sys.executable, "-m", "dbl_observer.cli", "--input", "-", "--mode", "project"],
        input=stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env_with_src_path(),
        check=False,
    )
    assert result_1.returncode == result_2.returncode
