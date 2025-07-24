from llms import gemini_with_search
from providers import AwsomeAgentLib, N8nAgentLib, AiAgentsLiveLib, AiAgentsListLib
import asyncio
from supabase import acreate_client, AsyncClient
import random
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")


async def create_supabase():
    supabase: AsyncClient = await acreate_client(supabase_url, supabase_key)
    return supabase


import re


def format_news_summary(text: str) -> str:
    # Replace **bold** with <b> tags
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Convert newlines to <br> or <p>
    paragraphs = text.strip().split("\n\n")
    html_parts = [f"<p>{p.replace('\n', '<br>')}</p>" for p in paragraphs]
    return "\n".join(html_parts)


def get_agent_html(agent):
    has_name = bool(agent.name and agent.name.strip())
    has_short = bool(agent.description_short and agent.description_short.strip())

    if has_name:
        title = f'<a href="{agent.url}" style="color: #005f99; text-decoration: none; font-weight: bold;">{agent.name}</a>'
        if has_short:
            title += (
                f' – <span style="font-weight: bold;">{agent.description_short}</span>'
            )
    elif has_short:
        title = f'<a href="{agent.url}" style="color: #005f99; text-decoration: none;">{agent.description_short}</a>'
    else:
        title = f'<a href="{agent.url}" style="color: #005f99; text-decoration: none;">[No description]</a>'

    html = f"""
    <p style="margin: 0.5em 0; font-size: 14px;">
      {title}
    </p>
    """
    if agent.description_long:
        lines = agent.description_long.strip().splitlines()
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue  # skip empty lines
            if len(line.split()) < 3:
                continue  # skip very short lines
            if "click" in line.lower():
                continue  # skip promotional lines
            cleaned_lines.append(line)
        combined = " ".join(cleaned_lines)
        trimmed = combined[:200].strip()
        if trimmed:
            html += f"""
            <blockquote style="margin: 0.2em 0 1em 1em; font-style: italic; color: #555; font-size: 13px;">
              {trimmed}...
            </blockquote>
            """
    return html


async def main():
    supabase = await create_supabase()
    print("Supabase client created")

    # Fetch existing agent URLs from database
    existing_response = await supabase.table("agents").select("url").execute()
    existing_urls = {row["url"] for row in existing_response.data}
    print(f"Found {len(existing_urls)} existing agents in database")

    html = ""
    async def run_with_lib(lib):
        async with lib:
            return await lib.fetch_new_agents()

    libs = [AwsomeAgentLib(), N8nAgentLib(), AiAgentsLiveLib(), AiAgentsListLib()]
    tasks = [run_with_lib(lib) for lib in libs]
    results = await asyncio.gather(*tasks)

    for i, lib in enumerate(libs):
        results[i]["provider_name"] = lib.name
        results[i]["provider_url"] = lib.url

    all_new_agents = []

    for agents in results:
        provider_name = agents["provider_name"]
        new_trending = [
            agent for agent in agents["trending"] if agent.url not in existing_urls
        ]
        new_recent = [
            agent for agent in agents["recent"] if agent.url not in existing_urls
        ]
        combined_new = new_trending + new_recent
        if len(combined_new) > 20:
            combined_new = random.sample(combined_new, 20)
            print(
                f"Limited {provider_name} to 20 random agents from {len(new_trending + new_recent)} new agents"
            )

        display_trending = [agent for agent in combined_new if agent in new_trending]
        display_recent = [agent for agent in combined_new if agent in new_recent]
        original_count = len(new_trending + new_recent)

        if display_trending:
            if original_count > 20:
                trending_title = f'More than 20 trending new agents appeared on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a> this month'
            else:
                trending_title = f'Trending Agents on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a>'
            html += (
                f'<h3 style="font-size: 16px; margin-top: 2em;">{trending_title}</h3>\n'
            )
            for agent in display_trending:
                html += get_agent_html(agent)

            html += '\n'

        if display_recent:
            if original_count > 20:
                recent_title = f'More than 20 new agents appeared on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a> this month'
            else:
                recent_title = f'Recently added Agents on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a>'
            html += (
                f'<h3 style="font-size: 16px; margin-top: 2em;">{recent_title}</h3>\n'
            )
            for agent in display_recent:
                html += get_agent_html(agent)

            html += '\n'

        # Add provider info to agents
        for agent in combined_new:
            agent.provider_name = provider_name
            agent.provider_url = agents["provider_url"]

        all_new_agents.extend(combined_new)
        print(f"Found {len(combined_new)} new agents from {provider_name}")

    html += """
    </body>
    </html>
    """
    print(f"Total new agents to process: {len(all_new_agents)}")

    # Save only new agents to database
    if all_new_agents:
        agent_data = []
        for agent in all_new_agents:
            agent_data.append(
                {
                    "url": agent.url,
                    "name": agent.name,
                    "desc_short": agent.description_short,
                    "desc_long": agent.description_long,
                    "provider_name": agent.provider_name,
                    "provider_url": agent.provider_url,
                }
            )

        await supabase.table("agents").insert(agent_data).execute()
        print(f"Saved {len(all_new_agents)} new agents to Supabase")
    else:
        print("No new agents found to save")

    # if news fetched today use db
    today = datetime.datetime.now().date()
    news_response = await supabase.table("news").select("*").order("created_at", desc=True).limit(1).execute()
    if news_response.data:
        d = news_response.data[0]["created_at"]
        news_date = datetime.datetime.fromisoformat(d).date()
        if news_date == today:
            print("Using existing news summary from database")
            last_news = news_response.data[0]["text"]
            formatted_news = format_news_summary(last_news)
    else:
        with open("src/prompts/gemini_news.txt", "r", encoding="utf-8") as f:
            prompt = f.read().strip()
        print("Asking Gemini to summarize the news...")
        news_summary = await gemini_with_search(
            prompt=prompt, max_tokens=10000, token=gemini_key
        )
        formatted_news = format_news_summary(news_summary)
        print("Generated news summary with Gemini")
        await supabase.table("news").insert(
            {"text": news_summary}
        ).execute()

    with open("agents.html", "w", encoding="utf-8") as f:
        f.write(
            f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>AI Agent Digest</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #ffffff; color: #333; padding: 20px; font-size: 14px;">
        <h2>📰 What happened last month in the AI Agents world?</h2>
        {formatted_news}
        <hr>
        {html}
        </body>
        </html>
        """
        )

    return len(all_new_agents)


if __name__ == "__main__":
    asyncio.run(main())
