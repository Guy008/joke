from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class JokesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Instant Jokes."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            lang = self.hass.config.language or "en"
            title = "בדיחות מיידיות" if lang.startswith("he") else "Instant Jokes"
            return self.async_create_entry(title=title, data={})

        return self.async_show_form(step_id="user")
