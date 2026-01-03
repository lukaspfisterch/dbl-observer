from dbl_observer import diagnostics


def test_diagnostics_vocabulary_frozen_v1() -> None:
    expected = {
        "duplicate_event_id_observed",
        "non_monotonic_event_id_observed",
        "ordering_gap_observed",
        "canon_len_mismatch_observed",
        "digest_mismatch_observed",
        "reference_length_mismatch_observed",
        "reference_event_id_set_mismatch_observed",
        "reference_order_mismatch_observed",
        "reference_digest_mismatch_observed",
    }
    assert set(diagnostics.DIAGNOSTICS_V1) == expected
