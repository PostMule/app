"""Tests for postmule.providers.registry (PROVIDER_REGISTRY catalog and get_provider lookup)."""

from postmule.providers.registry import (
    CATEGORY_DISPLAY_NAMES,
    PROVIDER_REGISTRY,
    get_provider,
)


class TestProviderRegistry:
    def test_all_categories_have_display_names(self):
        for category in PROVIDER_REGISTRY:
            assert category in CATEGORY_DISPLAY_NAMES

    def test_all_entries_have_required_fields(self):
        for entries in PROVIDER_REGISTRY.values():
            for entry in entries:
                assert entry["service"]
                assert entry["display_name"]
                assert entry["status"] in {"implemented", "stub"}
                assert entry["auth_type"] in {
                    "oauth2", "api_key", "password", "bridge", "local", "none",
                }


class TestGetProvider:
    def test_returns_entry_for_known_service(self):
        entry = get_provider("mailbox", "vpm")
        assert entry is not None
        assert entry["display_name"] == "Virtual Post Mail"
        assert entry["status"] == "implemented"

    def test_returns_none_for_unknown_service(self):
        assert get_provider("mailbox", "nonexistent") is None

    def test_returns_none_for_unknown_category(self):
        assert get_provider("nonexistent", "vpm") is None
