import asyncio
import logging
import random
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

JSON_URL = "https://www.bdihot.co.il/webmasters-json/"
MAX_MEMORY = 100
FETCH_ATTEMPTS = 8
QUEUE_REFILL_TARGET = 5
LOW_QUEUE_THRESHOLD = 2


async def _fetch_joke(session) -> dict | None:
    try:
        async with asyncio.timeout(10):
            async with session.get(JSON_URL) as response:
                data = await response.json()
        joke = data.get("joke", {})
        text = joke.get("content", "").strip()
        if not text:
            return None
        return {
            "title": joke.get("title", "").strip(),
            "text": text,
            "url": joke.get("url"),
            "image": joke.get("image"),
        }
    except Exception as e:
        _LOGGER.error("Error fetching joke: %s", e)
        return None


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


class JokesCoordinator(DataUpdateCoordinator[list[dict]]):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )
        self._memory: list[str] = []
        self._queue: list[dict] = []

    async def advance(self) -> None:
        """Pop the current joke. Refill from the API if the queue is low."""
        if self._queue:
            self._queue.pop(0)
        if len(self._queue) < LOW_QUEUE_THRESHOLD:
            await self.async_refresh()
        else:
            self.async_set_updated_data(self._queue)

    async def _async_update_data(self) -> list[dict]:
        session = async_get_clientsession(self.hass)
        new_jokes: list[dict] = []
        seen_texts: set[str] = set(self._memory) | {j["text"] for j in self._queue}

        for _ in range(FETCH_ATTEMPTS):
            joke = await _fetch_joke(session)
            if joke is None:
                continue
            if joke["text"] in seen_texts:
                continue
            seen_texts.add(joke["text"])
            if joke.get("url"):
                joke["type"] = await _fetch_category(session, joke["url"])
                joke["safe"] = joke["type"] == "clean"
            else:
                joke["type"] = "unknown"
                joke["safe"] = False
            new_jokes.append(joke)
            if len(new_jokes) >= QUEUE_REFILL_TARGET:
                break

        if not new_jokes and not self._queue:
            raise UpdateFailed("Could not fetch any jokes from bdihot.co.il")

        random.shuffle(new_jokes)
        self._queue.extend(new_jokes)

        self._memory.extend(j["text"] for j in new_jokes)
        if len(self._memory) > MAX_MEMORY:
            self._memory = self._memory[-MAX_MEMORY:]

        return self._queue
