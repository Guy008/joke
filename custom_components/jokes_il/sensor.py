from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JokesCoordinator

STATE_MAX_LENGTH = 255


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JokesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JokesSensor(coordinator)])


class JokesSensor(CoordinatorEntity[JokesCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "jokes"
    _attr_icon = "mdi:emoticon-happy-outline"

    def __init__(self, coordinator: JokesCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_sensor"

    @property
    def _queue(self) -> list[dict]:
        return self.coordinator.data or []

    @property
    def native_value(self) -> str | None:
        queue = self._queue
        if not queue:
            return None
        # The state holds the SHORT title, which is never truncated mid-word.
        # The full joke body lives in the `text` attribute: Home Assistant caps
        # the state at 255 chars, so a long joke placed here would be cut off
        # before its punchline. Consumers should read the `text` attribute.
        title = queue[0].get("title", "") or queue[0].get("text", "")
        if not title:
            return None
        return title[:STATE_MAX_LENGTH]

    @property
    def extra_state_attributes(self) -> dict:
        queue = self._queue
        if not queue:
            return {}
        cur = queue[0]
        attrs: dict = {
            "title": cur.get("title", ""),
            "text": cur.get("text", ""),
            "type": cur.get("type", ""),
            "safe": cur.get("safe", False),
            "url": cur.get("url", ""),
        }
        if len(queue) > 1:
            attrs["joke_2"] = queue[1].get("text", "")
            attrs["title_2"] = queue[1].get("title", "")
        else:
            attrs["joke_2"] = ""
            attrs["title_2"] = ""
        if len(queue) > 2:
            attrs["joke_3"] = queue[2].get("text", "")
            attrs["title_3"] = queue[2].get("title", "")
        else:
            attrs["joke_3"] = ""
            attrs["title_3"] = ""
        return attrs
