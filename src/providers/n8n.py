from .base import Agent, AgentLib
import datetime


class N8nAgentLib(AgentLib):
    def __init__(self):
        super().__init__("n8n")
        self.url = "https://n8n.io/workflows/"

    async def _fetch_from_api(self, params):
        agents = []
        url = "https://api.n8n.io/api/templates/search"
        response = await self.session.get(url, params=params)
        if not response.ok:
            raise Exception(f"Failed to fetch agents: {response.status}")
        data = await response.json()
        agents = []
        for item in data.get("workflows", []):
            agent = Agent(
                description_short=item["name"],
                description_long=item["description"],
                url=f"https://n8n.io/workflows/{item['id']}",
                provider_name="n8n",
                provider_url=self.url,
                # Format: 2025-06-10T08:27:01.375Z
                created_at=datetime.datetime.fromisoformat(
                    item["createdAt"].replace("Z", "+00:00")
                ),
            )
            agents.append(agent)
        return agents

    async def fetch_new_agents(self):
        trending_agents = await self._fetch_from_api(
            {"sort": "trendingScore:desc", "category": "AI", "rows": 8}
        )
        new_agents = await self._fetch_from_api({"sort": "createdAt:desc", "rows": 8})
        return {
            "trending": trending_agents,
            "recent": new_agents,
        }