# import os
# import sys
# p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# p = os.path.join(p, "providers")
# sys.path.append(p)
# print(p)

from providers.n8n import N8nAgentLib
from providers.awsome_agent import AwsomeAgentLib


import asyncio

async def test():
    async with AwsomeAgentLib() as lib:
        agents = await lib.fetch_new_agents()
    for k, v in agents.items():
        print(f"{k}:")
        for agent in v:
            print(f"{agent.name} - {agent.description_short} ({agent.url})")
            # print(f"{agent.description_long[:100] if agent.description_long else ''}...\n")

asyncio.run(test())