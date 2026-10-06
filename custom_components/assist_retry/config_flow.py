"""Config flow for Assist Retry: pick the agent to wrap and how many times to retry it."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_AGENT, CONF_RETRIES, DEFAULT_RETRIES, DOMAIN


def _schema(agent: str | None = None, retries: int = DEFAULT_RETRIES) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_AGENT, default=agent or vol.UNDEFINED): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="conversation")
            ),
            vol.Required(CONF_RETRIES, default=retries): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=3, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _title(hass, agent: str) -> str:
    state = hass.states.get(agent)
    name = state.name if state else agent
    return f"{name} (with retry)"


class AssistRetryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a retrying wrapper around a conversation agent."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            data = {CONF_AGENT: user_input[CONF_AGENT], CONF_RETRIES: int(user_input[CONF_RETRIES])}
            await self.async_set_unique_id(data[CONF_AGENT])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=_title(self.hass, data[CONF_AGENT]), data=data)
        return self.async_show_form(step_id="user", data_schema=_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AssistRetryOptionsFlow:
        return AssistRetryOptionsFlow()


class AssistRetryOptionsFlow(OptionsFlowWithReload):
    """Change the wrapped agent or the number of retries."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_AGENT: user_input[CONF_AGENT], CONF_RETRIES: int(user_input[CONF_RETRIES])}
            )
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(current[CONF_AGENT], current.get(CONF_RETRIES, DEFAULT_RETRIES))
        )
