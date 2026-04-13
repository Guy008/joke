import asyncio
import logging
import random
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

JSON_URL = "http://www.bdihot.co.il/webmasters-json/"
MAX_MEMORY = 20


async def _fetch_category(session, url: str) -> str:
    try:
        async with asyncio.timeout(10):
            async with session.get(url) as response:
                html = await response.text()

        if "/ctype/clean/" in html:
            return "clean"
        if "/ctype/sexual/" in html:
            return "adult"
        if "/ctype/ethnic/" in html:
            return "ethnic"
    except Exception:
        pass
    return "unknown"


async def _fetch_joke(session) -> dict | None:
    try:
        async with asyncio.timeout(10):
            async with session.get(JSON_URL) as response:
                data = await response.json()

        joke = data.get("joke", {})

        return {
            "title": joke.get("title", "").strip(),
            "text": joke.get("content", "").strip(),
            "url": joke.get("url"),
            "image": joke.get("image"),
        }
    except Exception as e:
        _LOGGER.error("Error fetching joke: %s", e)
    return None


class JokesCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )
        self._joke_memory: list[str] = []

    async def _async_update_data(self) -> list[dict]:
        session = async_get_clientsession(self.hass)
        jokes = []

        for _ in range(5):
            joke = await _fetch_joke(session)
            if joke:
                jokes.append(joke)

        if not jokes:
            raise UpdateFailed("Could not fetch any jokes from bdihot.co.il")

        unique = [j for j in jokes if j["text"] not in self._joke_memory]
        if len(unique) < 3:
            unique = jokes

        selected = random.sample(unique, min(3, len(unique)))

        for j in selected:
            if j.get("url"):
                j["type"] = await _fetch_category(session, j["url"])
                j["safe"] = j["type"] == "clean"
            else:
                j["type"] = "unknown"
                j["safe"] = False

        self._joke_memory.extend(j["text"] for j in selected)
        del self._joke_memory[:-MAX_MEMORY]

        return selected
