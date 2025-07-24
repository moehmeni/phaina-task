from .base import Agent, AgentLib
from urllib.parse import urljoin
import asyncio

class AiAgentsLiveLib(AgentLib):
    def __init__(self):
        super().__init__("AI Agents Live")
        self.url = "https://aiagentslive.com/agents"

    async def _fetch_agent_page(self, agent: Agent) -> Agent:
        soup = await self.get_soup(agent.url)
        # desc long is in div.text-lg.my-8 div (second one)
        divs = soup.select("div.text-lg.my-8 div")
        if len(divs) > 1:
            desc_long = divs[1].text.strip()
            # usecases mentioned in the ul
            ul = soup.select_one("div.text-lg.my-8 ul")
            if ul:
                desc_long += "\n\nFeatures:\n" + "\n".join(
                    li.text.strip() for li in ul.select("li")
                )
            agent.description_long = desc_long
        agent.url = soup.select_one("a.text-blue-600")["href"].split("?ref=")[0]
        return agent

    async def fetch_new_agents(self):
        soup = await self.get_soup(self.url)
        agents = []
        cards = soup.select("div.gap-4")
        for c in cards:
            if h3 := c.select_one("h3"):
                title = h3.text.strip()
                desc = c.select_one("p").text.strip() if c.select_one("p") else ""
                agent = Agent(
                    name=title,
                    description_short=desc,
                    url=urljoin(self.url, c.select_one("a")["href"]),
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
        }
