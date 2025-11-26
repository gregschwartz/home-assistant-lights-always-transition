"""Smooth Lights integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_EXCLUDE_ENTITIES,
    CONF_TRANSITION_TIME,
    DEFAULT_TRANSITION_TIME,
    DOMAIN,
)
from .interceptor import setup_service_call_interceptor

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smooth Lights from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    transition_time = entry.data.get(CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME)
    exclude_entities = entry.data.get(CONF_EXCLUDE_ENTITIES, [])

    def interceptor(call: ServiceCall, modified_data: dict) -> None:
        """Intercept light.turn_on calls and add transition."""
        # Skip if transition already specified
        if "transition" in modified_data:
            return

        # Get entity IDs from the call
        entity_ids = modified_data.get("entity_id")
        if entity_ids is None:
            return

        # Normalize to list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        # Check if any entities should be excluded
        for entity_id in entity_ids:
            if entity_id in exclude_entities:
                _LOGGER.debug("Skipping transition for excluded entity: %s", entity_id)
                return

        # Add transition
        modified_data["transition"] = transition_time
        _LOGGER.debug(
            "Added %s second transition to light.turn_on call for %s",
            transition_time,
            entity_ids,
        )

    # Set up the interceptor
    remove_interceptor = setup_service_call_interceptor(
        hass, "light", "turn_on", interceptor
    )

    # Store the remove function
    hass.data[DOMAIN][entry.entry_id] = {
        "remove_interceptor": remove_interceptor,
    }

    _LOGGER.info(
        "Smooth Lights initialized with %s second transition", transition_time
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove the interceptor
    if entry.entry_id in hass.data[DOMAIN]:
        remove_interceptor = hass.data[DOMAIN][entry.entry_id]["remove_interceptor"]
        remove_interceptor()
        hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.info("Smooth Lights unloaded")

    return True
