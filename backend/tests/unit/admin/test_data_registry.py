"""Unit tests for admin.data_registry."""

import types

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_true

from admin.data_registry import ADMIN_TABLES, TableSpec, serialize_row

pytestmark = [pytest.mark.unit]


class TestDataRegistry:
    @autotest.num("1920")
    @autotest.external_id("69a602c7-e43d-4de4-8fa3-134b17a045b6")
    @autotest.name("ADMIN_TABLES contains the expected slugs")
    def test_69a602c7_admin_tables_contains_expected_slugs(self):
        with autotest.step("Assert: key slugs are present"):
            assert_in("mcp_audit", ADMIN_TABLES, "mcp_audit")
            assert_in("consents", ADMIN_TABLES, "consents")
            assert_in("chat_messages", ADMIN_TABLES, "chat_messages")
            assert_in("learning_sessions", ADMIN_TABLES, "learning_sessions")
            assert_in("behavioral_events", ADMIN_TABLES, "behavioral_events")

    @autotest.num("1921")
    @autotest.external_id("13e104de-c20c-47d4-a69d-d998454f73b8")
    @autotest.name("ADMIN_TABLES excludes auth tables")
    def test_13e104de_admin_tables_excludes_auth_tables(self):
        with autotest.step("Assert: auth tables are absent"):
            for slug in ["accounts", "sessions", "verification_tokens", "users"]:
                assert_true(slug not in ADMIN_TABLES, f"{slug} is absent")

    @autotest.num("1922")
    @autotest.external_id("3f847f3e-14c7-49c6-a0df-a14c4c95d2f6")
    @autotest.name("default_sort is included in sortable for every table")
    def test_3f847f3e_default_sort_in_sortable(self):
        with autotest.step("Assert: default_sort ⊆ sortable for all"):
            for slug, spec in ADMIN_TABLES.items():
                assert_in(spec.default_sort, spec.sortable, f"{slug}.default_sort in sortable")

    @autotest.num("1923")
    @autotest.external_id("7e1229e7-9c0a-4197-bbce-78d558831150")
    @autotest.name("sortable/searchable/masked ⊆ columns for every table")
    def test_7e1229e7_column_sets_subset_of_columns(self):
        with autotest.step("Assert: all column sets are subsets of columns"):
            for slug, spec in ADMIN_TABLES.items():
                cols = set(spec.columns)
                assert_true(spec.sortable <= cols, f"{slug}.sortable ⊆ columns")
                assert_true(set(spec.searchable) <= cols, f"{slug}.searchable ⊆ columns")
                assert_true(spec.masked <= cols, f"{slug}.masked ⊆ columns")

    @autotest.num("1924")
    @autotest.external_id("5aa8ab53-5651-4a4d-9eda-980c5859321d")
    @autotest.name("serialize_row masks a field from masked")
    def test_5aa8ab53_serialize_row_masks_masked_col(self):
        with autotest.step("Arrange: a spec with secret_field masked, and a matching row"):
            spec = TableSpec(
                model=object,
                columns=["id", "secret_field"],
                sortable={"id"},
                searchable=["id"],
                masked={"secret_field"},
                default_sort="id",
            )
            row = types.SimpleNamespace(id="x", secret_field="sensitive")
        with autotest.step("Act: serialize_row"):
            result = serialize_row(spec, row)
        with autotest.step("Assert: secret_field is masked, id untouched"):
            assert_equal(result["secret_field"], "***", "masked → ***")
            assert_equal(result["id"], "x", "id untouched")

    @autotest.num("1925")
    @autotest.external_id("b40cc542-75bc-4b0b-8746-8fe0b1858ede")
    @autotest.name("serialize_row masks a field with a secret-regex name (api_token)")
    def test_b40cc542_serialize_row_masks_secret_regex(self):
        with autotest.step("Arrange: a spec with no masked cols, and a row with api_token"):
            spec = TableSpec(
                model=object,
                columns=["id", "api_token"],
                sortable={"id"},
                searchable=["id"],
                masked=set(),
                default_sort="id",
            )
            row = types.SimpleNamespace(id="x", api_token="abc123")
        with autotest.step("Act: serialize_row"):
            result = serialize_row(spec, row)
        with autotest.step("Assert: api_token is masked by regex"):
            assert_equal(result["api_token"], "***", "regex match → ***")

    @autotest.num("1926")
    @autotest.external_id("c7a8b9d0-e1f2-4345-abcd-456789012356")
    @autotest.name("serialize_row truncates a long dict to 200 + '…'")
    def test_c7a8b9d0_serialize_row_truncates_long_dict(self):
        with autotest.step("Arrange: a spec with a data col, and a row with a large dict"):
            spec = TableSpec(
                model=object,
                columns=["id", "data"],
                sortable={"id"},
                searchable=["id"],
                masked=set(),
                default_sort="id",
            )
            big_dict = {str(i): "x" * 10 for i in range(50)}
            row = types.SimpleNamespace(id="x", data=big_dict)
        with autotest.step("Act: serialize_row"):
            result = serialize_row(spec, row)
        with autotest.step("Assert: length ≤ 202, ends with '…'"):
            assert_true(len(result["data"]) <= 202, "length ≤ 202")
            assert_true(result["data"].endswith("…"), "ends with '…'")
