from .base import Agent, AgentLib
from urllib.parse import urljoin
import asyncio

class AiAgentsListLib(AgentLib):
    def __init__(self):
        super().__init__("AI Agents List")
        self.url = "https://aiagentslist.com/?sort=createdAt.desc"

    async def _fetch_agent_page(self, agent: Agent) -> Agent:
        soup = await self.get_soup(agent.url)
        desc_long = soup.select_one("div.p-6.pt-0 p").text.strip()
        ul = soup.select_one("article ul")
        if ul:
            desc_long += "\n\nFeatures:\n" + "\n".join(
                li.text.strip() for li in ul.select("li")
            )
        agent.description_long = desc_long
        agent.url = soup.select_one('a[target="_blank"]')["href"].split("?ref=")[0]
        return agent

    async def fetch_new_agents(self):
        soup = await self.get_soup(self.url)
        agents = []
        cards = soup.select("div.grid a .rounded-lg")
        for c in cards:
            recently_added = c.select_one("span.bg-secondary")
            if (h3 := c.select_one('div[role="heading"]')) and recently_added:
                title = h3.text.strip()
                desc = c.select_one("p").text.strip() if c.select_one("p") else ""
                agent = Agent(
                    name=title,
                    description_short=desc,
                    url=urljoin(self.url, c.parent["href"]),
                    description_long=None, # will be set later
                    provider_name=self.name,
                    provider_url=self.url,
                )
                agents.append(agent)

        # get long descriptions for each agent in parallel
        tasks = [self._fetch_agent_page(agent) for agent in agents]
        agents = await asyncio.gather(*tasks)
        return {
            "recent": agents,
            "trending": [],
        }
