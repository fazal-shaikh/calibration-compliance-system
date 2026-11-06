"""
Tests for Relational Database Integrity and Schema Constraints
"""

import pytest
from database.connection import get_db
from validation.integrity import validate_integrity
from validation.lifecycle import validate_lifecycle_transitions

def test_database_relational_integrity():
    """Verify zero duplicate PKs, zero orphan FKs, and valid enums."""
    with get_db() as db:
        res = validate_integrity(db)
        assert res["duplicate_records"] == 0, f"Found duplicate records: {res['details']}"
        assert res["orphan_records"] == 0, f"Found orphan records: {res['details']}"
        assert res["invalid_relationships"] == 0
        assert res["failed_checks"] == 0

def test_lifecycle_transitions():
    """Verify operational status and maintenance lifecycles."""
    with get_db() as db:
        res = validate_lifecycle_transitions(db)
        assert res["violations_count"] == 0, f"Lifecycle violations: {res['violations']}"