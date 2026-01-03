import json
import os
import subprocess
import sys
from pathlib import Path

from dbl_observer.canon import canonical_json_bytes
from dbl_observer.digest import sha256_hex


def _env_with_src_path() -> dict[str, str]:
    env = dict(os.environ)
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}{os.pathsep}{existing}"
    return env


def _mk_row(
    event_id: int,
    source: str,
    artifact: str,
    payload: dict,
    *,
    digest_override: str | None = None,
) -> dict:
    canon = canonical_json_bytes(payload)
    digest = "sha256:" + sha256_hex(canon)
    if digest_override is not None:
        digest = digest_override
    return {
        "event_id": event_id,
        "source": source,
        "artifact": artifact,
        "payload": payload,
        "canon_len": len(canon),
        "digest": digest,
        "diagnostics": [],
    }


def test_diff_emits_only_reference_digest_mismatch(tmp_path: Path) -> None:
    bad = _mk_row(1, "adapter", "record", {"x": 1}, digest_override="sha256:" + "0" * 64)
    tfile = tmp_path / "trace.jsonl"
    tfile.write_text(json.dumps(bad, ensure_ascii=True) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbl_observer.cli",
            "--input",
            str(tfile),
            "--reference",
            str(tfile),
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
    assert result.stdout.strip() == ""
