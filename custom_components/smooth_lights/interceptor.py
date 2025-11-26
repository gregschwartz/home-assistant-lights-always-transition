"""Service call interceptor for Smooth Lights."""
from __future__ import annotations

import logging
from typing import Callable

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.service import async_extract_entity_ids

_LOGGER = logging.getLogger(__name__)


def setup_service_call_interceptor(
    hass: HomeAssistant,
    domain: str,
    service: str,
    interceptor_func: Callable[[ServiceCall, dict], None],
) -> Callable[[], None]:
    """Set up a service call interceptor.

    Returns a function to remove the interceptor.
    """
    # Access the service registry
    if domain not in hass.services._services:
        _LOGGER.error("Domain %s not found in service registry", domain)
        return lambda: None

    if service not in hass.services._services[domain]:
        _LOGGER.error("Service %s.%s not found in service registry", domain, service)
        return lambda: None

    # Get the original service
    service_obj = hass.services._services[domain][service]
    original_handler = service_obj.job.target

    async def proxy_handler(call: ServiceCall) -> None:
        """Proxy handler that intercepts the service call."""
        # Convert read-only data to mutable dict
        modified_data = dict(call.data)

        try:
            # Call the interceptor function to modify the data
            interceptor_func(call, modified_data)
        except Exception as err:
            _LOGGER.exception("Error in service call interceptor: %s", err)

        # Create a new ServiceCall with modified data
        modified_call = ServiceCall(
            domain=call.domain,
            service=call.service,
            data=modified_data,
            context=call.context,
        )

        # Call the original handler
        await original_handler(modified_call)

    # Replace the handler
    service_obj.job.target = proxy_handler

    def remove() -> None:
        """Remove the interceptor and restore original handler."""
        service_obj.job.target = original_handler

    return remove
