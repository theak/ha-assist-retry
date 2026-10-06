"""The retrying conversation agent.

It runs inside the caller's chat log, so the wrapped agent's streamed text still reaches the
voice pipeline as it arrives. An attempt is retried only if it failed before producing any
text: once text has reached the listener it may already be playing, and can't be taken back.
"""

from __future__ import annotations

import logging
from typing import Literal

from homeassistant.components import conversation
from homeassistant.components.conversation import ChatLog, ConversationEntity, ConversationInput, ConversationResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import chat_session, intent
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_AGENT, CONF_RETRIES, DEFAULT_RETRIES, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([RetryAgent(entry)])


class SimulatedFailure(Exception):
    """Raised in place of an attempt by the simulate_failure service."""


class RetryAgent(ConversationEntity):
    """Pass each request to another agent, and retry it if it fails before saying anything."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supports_streaming = True

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return "*"

    @property
    def _target(self) -> str:
        return self._entry.options.get(CONF_AGENT, self._entry.data[CONF_AGENT])

    @property
    def _retries(self) -> int:
        return int(self._entry.options.get(CONF_RETRIES, self._entry.data.get(CONF_RETRIES, DEFAULT_RETRIES)))

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        # Opening the chat log here makes it the active one, so the target agent works in it too
        # and its deltas go to the pipeline's listener.
        with (
            chat_session.async_get_chat_session(self.hass, user_input.conversation_id) as session,
            conversation.async_get_chat_log(self.hass, session, user_input) as chat_log,
        ):
            for attempt in range(self._retries + 1):
                spoke, result, error = await self._attempt(user_input, session.conversation_id, chat_log)
                failed = error is not None or result.response.response_type == intent.IntentResponseType.ERROR
                if not failed:
                    return result
                last_try = attempt == self._retries
                if spoke or last_try:
                    if error is not None:
                        raise error
                    return result
                _LOGGER.warning(
                    "%s failed before answering (%s), retrying (%d of %d)",
                    self._target,
                    error or result.response.speech.get("plain", {}).get("speech"),
                    attempt + 1,
                    self._retries,
                )
        raise HomeAssistantError("unreachable")

    async def _attempt(
        self, user_input: ConversationInput, conversation_id: str, chat_log: ChatLog
    ) -> tuple[bool, ConversationResult | None, Exception | None]:
        """Run the target agent once. Returns whether it produced any text, and its result or error."""
        spoke = False
        listener = chat_log.delta_listener

        def watch(log: ChatLog, delta: dict) -> None:
            nonlocal spoke
            if delta.get("content"):
                spoke = True
            if listener is not None:
                listener(log, delta)

        chat_log.delta_listener = watch
        try:
            state = self.hass.data[DOMAIN]
            if state["simulated_failures"] > 0:
                state["simulated_failures"] -= 1
                raise SimulatedFailure("simulated failure")
            result = await conversation.async_converse(
                self.hass,
                text=user_input.text,
                conversation_id=conversation_id,
                context=user_input.context,
                language=user_input.language,
                agent_id=self._target,
                device_id=user_input.device_id,
                satellite_id=user_input.satellite_id,
                extra_system_prompt=user_input.extra_system_prompt,
            )
            return spoke, result, None
        except Exception as err:  # noqa: BLE001 - any failure before speaking is worth one more try
            return spoke, None, err
        finally:
            chat_log.delta_listener = listener
