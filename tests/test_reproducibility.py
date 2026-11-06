"""
Tests for Deterministic Pipeline Reproducibility
"""

import pytest
from validation.reproducibility import verify_reproducibility

def test_pipeline_deterministic_reproducibility():
    """Verify that dual pipeline executions with Seed=20261022 produce identical datasets."""
    res = verify_reproducibility(seed=20261022)
    assert res["all_identical"] is True, "Pipeline failed bit-for-bit reproducibility check!"
    for entity, comp in res["comparisons"].items():
        assert comp["is_identical"] is True, f"Entity {entity} mismatch between runs."
        assert comp["run1_sha256"] == comp["run2_sha256"]