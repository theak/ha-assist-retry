"""Assist Retry: a conversation agent that retries another agent when it fails before speaking."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

PLATFORMS = [Platform.CONVERSATION]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the service that makes the next attempts fail, for testing the retry."""
    hass.data[DOMAIN] = {"simulated_failures": 0}

    async def simulate_failure(call: ServiceCall) -> None:
        hass.data[DOMAIN]["simulated_failures"] = call.data["count"]

    hass.services.async_register(
        DOMAIN,
        "simulate_failure",
        simulate_failure,
        schema=vol.Schema({vol.Optional("count", default=1): vol.All(int, vol.Range(min=0, max=10))}),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the agent."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove the agent."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
