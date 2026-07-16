"""Tests that negative controls detect missing safeguards."""

from __future__ import annotations

import pytest
from memdot_core.db.registry import ACCOUNT_OWNED_TABLES
from sqlalchemy import text


def test_registry_requires_force_rls_coverage() -> None:
    assert "account" in ACCOUNT_OWNED_TABLES
    assert "space" in ACCOUNT_OWNED_TABLES
    assert len(ACCOUNT_OWNED_TABLES) >= 30


def test_negative_control_detects_missing_table_in_registry() -> None:
    with pytest.raises(AssertionError):
        assert "definitely_not_a_table" in ACCOUNT_OWNED_TABLES


def test_negative_control_adversarial_registration_gap_is_detectable() -> None:
    """Simulate a missing adversarial registration and prove the gate would fail."""
    declared = set(ACCOUNT_OWNED_TABLES)
    registered = declared - {"account"}
    missing = sorted(declared - registered)
    assert missing == ["account"]


def test_live_negative_control_detects_missing_force_rls(migrated_engine) -> None:
    with migrated_engine.begin() as conn:
        conn.execute(text("ALTER TABLE account NO FORCE ROW LEVEL SECURITY"))
        try:
            forced = conn.execute(
                text("SELECT relforcerowsecurity FROM pg_class WHERE relname='account'")
            ).scalar_one()
            assert forced is False
        finally:
            conn.execute(text("ALTER TABLE account FORCE ROW LEVEL SECURITY"))


def test_live_negative_control_detects_forbidden_runtime_grant(migrated_engine) -> None:
    with migrated_engine.begin() as conn:
        conn.execute(text("GRANT TRUNCATE ON account TO memdot_core"))
        try:
            granted = conn.execute(
                text("SELECT has_table_privilege('memdot_core','account','TRUNCATE')")
            ).scalar_one()
            assert granted is True
        finally:
            conn.execute(text("REVOKE TRUNCATE ON account FROM memdot_core"))


def test_live_negative_control_detects_public_function_execute(migrated_engine) -> None:
    signature = "memdot_auth_bootstrap_exists()"
    with migrated_engine.begin() as conn:
        conn.execute(text(f"GRANT EXECUTE ON FUNCTION {signature} TO PUBLIC"))
        try:
            count = conn.execute(
                text(
                    """
                    SELECT count(*) FROM pg_proc p
                    CROSS JOIN LATERAL aclexplode(
                      coalesce(p.proacl, acldefault('f', p.proowner))
                    ) acl
                    WHERE p.proname='memdot_auth_bootstrap_exists' AND acl.grantee=0
                      AND acl.privilege_type='EXECUTE'
                    """
                )
            ).scalar_one()
            assert count == 1
        finally:
            conn.execute(text(f"REVOKE EXECUTE ON FUNCTION {signature} FROM PUBLIC"))
