# from providers.n8n import N8nAgentLib
# from providers.awsome_agent import AwsomeAgentLib
# from providers.aiagentslive import AiAgentsLiveLib
# from providers.aiagentlist import AiAgentsListLib

# from llms import gemini_with_search

# import asyncio

# async def test():
#     # async with AwsomeAgentLib() as lib:
#     #     agents = await lib.fetch_new_agents()
#     # for k, v in agents.items():
#     #     print(f"{k}:")
#     #     for agent in v:
#     #         print(f"{agent.name} - {agent.description_short} ({agent.url})")
#     #         # print(f"{agent.description_long[:100] if agent.description_long else ''}...\n")

#     async with AiAgentsListLib() as lib:
#         agents = await lib.fetch_new_agents()
#     for k, v in agents.items():
#         print(f"{k}:")
#         for agent in v:
#             print(f"{agent.name} - {agent.description_short} ({agent.url})")
#             print(f"{agent.description_long}\n")


#     # # read the prompt from prompts/gemini_news.txt
#     # with open("src/prompts/gemini_news.txt", "r") as f:
#     #     prompt = f.read()
#     # response = await gemini_with_search(prompt)
#     # print(response)

# asyncio.run(test())
