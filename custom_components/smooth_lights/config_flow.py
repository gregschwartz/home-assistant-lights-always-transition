"""Config flow for Smooth Lights."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_EXCLUDE_ENTITIES, CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME, DOMAIN


class SmoothLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smooth Lights."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Create the entry
            return self.async_create_entry(
                title="Smooth Lights",
                data=user_input,
            )

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TRANSITION_TIME, default=DEFAULT_TRANSITION_TIME
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
                vol.Optional(CONF_EXCLUDE_ENTITIES, default=[]): cv.entity_ids,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SmoothLightsOptionsFlow:
        """Get the options flow for this handler."""
        return SmoothLightsOptionsFlow(config_entry)


class SmoothLightsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smooth Lights."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title="", data={})

        # Get current values
        current_transition = self.config_entry.data.get(
            CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME
        )
        current_exclude = self.config_entry.data.get(CONF_EXCLUDE_ENTITIES, [])

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TRANSITION_TIME, default=current_transition
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
                vol.Optional(CONF_EXCLUDE_ENTITIES, default=current_exclude): cv.entity_ids,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
