from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, PLATFORMS
from .coordinator import JokesCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = JokesCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "queue": list(coordinator.data or []),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def refresh(call: ServiceCall) -> None:
        data = hass.data[DOMAIN].get(entry.entry_id, {})
        coordinator = data.get("coordinator")
        if coordinator:
            await coordinator.async_request_refresh()
            data["queue"] = list(coordinator.data or [])

    async def next_joke(call: ServiceCall) -> None:
        queue = hass.data[DOMAIN].get(entry.entry_id, {}).get("queue", [])
        if queue:
            queue.pop(0)

    hass.services.async_register(DOMAIN, "refresh_jokes", refresh)
    hass.services.async_register(DOMAIN, "next_joke", next_joke)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.services.async_remove(DOMAIN, "refresh_jokes")
        hass.services.async_remove(DOMAIN, "next_joke")
    return unloaded
