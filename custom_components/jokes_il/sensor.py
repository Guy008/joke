from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JokesCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: JokesCoordinator = data["coordinator"]
    async_add_entities([JokesSensor(hass, entry, coordinator)])


class JokesSensor(CoordinatorEntity[JokesCoordinator], SensorEntity):
    _attr_name = "Instant Jokes"
    _attr_icon = "mdi:emoticon-happy-outline"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: JokesCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.hass = hass
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_sensor"

    def _get_queue(self) -> list[dict]:
        data = self.hass.data[DOMAIN].get(self._entry_id, {})
        queue: list[dict] = data.get("queue", [])
        if not queue and self.coordinator.data:
            queue.extend(self.coordinator.data)
            data["queue"] = queue
        return queue

    @property
    def state(self) -> str:
        queue = self._get_queue()
        return queue[0]["text"] if queue else "אין בדיחה"

    @property
    def extra_state_attributes(self) -> dict:
        queue = self._get_queue()
        return {
            "title": queue[0].get("title", "") if queue else "",
            "joke_2": queue[1]["text"] if len(queue) > 1 else "",
            "title_2": queue[1].get("title", "") if len(queue) > 1 else "",
            "joke_3": queue[2]["text"] if len(queue) > 2 else "",
            "title_3": queue[2].get("title", "") if len(queue) > 2 else "",
            "type": queue[0].get("type", "") if queue else "",
            "safe": queue[0].get("safe", False) if queue else False,
            "url": queue[0].get("url", "") if queue else "",
        }
