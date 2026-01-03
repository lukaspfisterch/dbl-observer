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


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_cli_golden_diagnostic_output() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "tests" / "data" / "trace_input.jsonl"
    expected_path = root / "tests" / "data" / "expected_diagnostic.txt"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(input_path),
            "--mode",
            "diagnostic",
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
    assert result.stdout == _read_text(expected_path)


def test_cli_golden_explain_output() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "tests" / "data" / "trace_input.jsonl"
    expected_path = root / "tests" / "data" / "expected_explain.txt"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(input_path),
            "--mode",
            "explain",
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
    assert result.stdout == _read_text(expected_path)


def test_cli_golden_diff_output() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "tests" / "data" / "trace_input.jsonl"
    expected_path = root / "tests" / "data" / "expected_diff.txt"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(input_path),
            "--reference",
            str(input_path),
            "--mode",
            "diff",
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
    assert result.stdout == _read_text(expected_path)
