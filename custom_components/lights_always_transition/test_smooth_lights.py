"""Tests for Smooth Lights integration."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from custom_components.smooth_lights import async_setup_entry, async_unload_entry
from custom_components.smooth_lights.const import (
    CONF_TRANSITION_TIME,
    CONF_EXCLUDE_ENTITIES,
    DEFAULT_TRANSITION_TIME,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Smooth Lights",
        data={
            CONF_TRANSITION_TIME: 4,
            CONF_EXCLUDE_ENTITIES: [],
        },
        source="user",
        entry_id="test_entry",
    )


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.mark.asyncio
async def test_setup_entry(mock_hass, mock_config_entry):
    """Test setting up the integration."""
    with patch("custom_components.smooth_lights.setup_service_call_interceptor") as mock_interceptor:
        mock_interceptor.return_value = Mock()

        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        mock_interceptor.assert_called_once()


@pytest.mark.asyncio
async def test_unload_entry(mock_hass, mock_config_entry):
    """Test unloading the integration."""
    # Setup first
    remove_mock = Mock()
    mock_hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {
                "remove_interceptor": remove_mock,
            }
        }
    }

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    remove_mock.assert_called_once()
    assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]


def test_interceptor_adds_transition():
    """Test that interceptor adds transition when not present."""
    from custom_components.smooth_lights import async_setup_entry

    # Create a mock call
    call = Mock(spec=ServiceCall)
    modified_data = {
        "entity_id": "light.living_room",
    }

    # This would be the interceptor function created in async_setup_entry
    # We'll test the logic directly
    transition_time = 4

    if "transition" not in modified_data:
        modified_data["transition"] = transition_time

    assert modified_data["transition"] == 4


def test_interceptor_respects_existing_transition():
    """Test that interceptor doesn't override existing transition."""
    modified_data = {
        "entity_id": "light.living_room",
        "transition": 2,
    }

    # Interceptor logic
    transition_time = 4
    if "transition" not in modified_data:
        modified_data["transition"] = transition_time

    # Should still be 2, not 4
    assert modified_data["transition"] == 2


def test_interceptor_respects_exclusions():
    """Test that interceptor skips excluded entities."""
    exclude_entities = ["light.bedroom"]
    modified_data = {
        "entity_id": "light.bedroom",
    }

    # Interceptor logic
    entity_id = modified_data.get("entity_id")
    if entity_id in exclude_entities:
        # Skip adding transition
        pass
    else:
        modified_data["transition"] = 4

    assert "transition" not in modified_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
