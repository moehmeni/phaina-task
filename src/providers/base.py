
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from aiohttp import ClientSession
from bs4 import BeautifulSoup

@dataclass
class Agent:
    description_short: str
    url: str
    provider_name: str
    provider_url: str
    name: Optional[str] = None
    description_long: Optional[str] = None
    created_at: Optional[datetime] = None


class AgentLib:
    def __init__(self, name: str):
        self.name = name
        self.session = None

    async def __aenter__(self):
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def get_soup(self, url: str):
        async with self.session.get(url) as response:
            if response.ok:
                html = await response.text()
                return BeautifulSoup(html, 'html.parser')
            else:
                raise Exception(f"Failed to fetch {url}: {response.status}")

    async def fetch_new_agents(self) -> Dict[str, List[Agent]]:
        """Fetch new agents from the provider.
        Returns each agent list by section name.
        e.g. {"trending": [Agent1, Agent2], "recent": [Agent3, Agent4]}
        """
        raise NotImplementedError("This method should be overridden by subclasses")