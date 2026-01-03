from pathlib import Path


def test_contract_docs_have_status_line() -> None:
    root = Path(__file__).resolve().parents[1]
    contract_dir = root / "docs" / "contracts"
    docs = sorted(contract_dir.glob("*.md"))
    assert docs, "no contract docs found"
    for doc in docs:
        content = doc.read_text(encoding="utf-8")
        assert "Status:" in content, f"missing Status line in {doc}"
