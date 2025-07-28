from llms import gemini_with_search, gemini
from providers import (
    AwsomeAgentLib,
    N8nAgentLib,
    AiAgentsLiveLib,
    AiAgentsListLib,
    HuggingFacePaperProvider,
    get_related_tweet_from_headline,
    get_tweet_html,
    env,
    fetch_top_reddit_posts
)
import asyncio
from supabase import acreate_client, AsyncClient
import random
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")
google_search_key = os.getenv("GOOGLE_SEARCH_KEY")


async def create_supabase():
    supabase: AsyncClient = await acreate_client(supabase_url, supabase_key)
    return supabase

def get_clean_text_for_paragraph(paragraph: str) -> str:
    soup = BeautifulSoup(paragraph, "html.parser")
    text = soup.get_text()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return text

def get_html_for_paragraph(paragraph: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", paragraph)
    text = text.replace("\n", "<br>")
    return f"<p>{text}</p>"

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


# def get_paper_html(paper):
#     title = f'<a href="{paper.url}" style="color: #005f99; text-decoration: none; font-weight: bold;">{paper.title}</a>'
#     s = (paper.ai_summary or paper.summary).strip()
#     html = f"""
#     <p style="margin: 0.5em 0; font-size: 14px;">
#         {title}
#         <blockquote style="margin: 0.2em 0 1em 1em; font-style: italic; color: #555; font-size: 13px;">
#         {s[:200].strip()}...
#         </blockquote>
#     </p>
#     """
#     if paper.thumbnail_url:
#         html += f"""
#         <img src="{paper.thumbnail_url}" style="max-width: 60%; height: auto; margin: 0.5em auto;" />
#         """
#     return html


def render_papers_in_rows(papers):
    rows = []
    for i in range(0, len(papers), 2):
        left = get_paper_cell(papers[i])
        right = get_paper_cell(papers[i + 1]) if i + 1 < len(papers) else ""
        row_html = f"""
        <tr>
            <td style="width: 50%; vertical-align: top; padding: 0 10px 40px 0;">{left}</td>
            <td style="width: 50%; vertical-align: top; padding: 0 0 40px 10px;">{right}</td>
        </tr>
        """
        rows.append(row_html)

    return f"""
    <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse;">
        {''.join(rows)}
    </table>
    """


def get_paper_cell(paper):
    title_html = f'<a href="{paper.url}" style="color: #005f99; text-decoration: none; font-weight: bold;">{paper.title}</a>'
    summary = (paper.ai_summary or paper.summary or "").strip()
    snippet = summary[:200] + "..." if len(summary) > 200 else summary

    image_html = ""
    if paper.thumbnail_url:
        image_html = f"""
        <div style="text-align: center; margin: 0.5em 0;">
            <img src="{paper.thumbnail_url}" style="max-width: 100%; height: auto; border-radius: 4px;" />
        </div>
        """

    return f"""
    <div style="font-size: 14px; line-height: 1.4; color: #333;">
        {title_html}
        <blockquote style="margin: 0.5em 0 1em 0.5em; font-style: italic; color: #555; font-size: 13px;">
            {snippet}
        </blockquote>
        {image_html}
    </div>
    """


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

        new_trending = [agent for agent in agents["trending"] if agent.url not in existing_urls]
        new_recent = [agent for agent in agents["recent"] if agent.url not in existing_urls]

        if len(new_trending) > 10:
            print(f"Limited {provider_name} trending to 10 random agents from {len(new_trending)}")
            new_trending = random.sample(new_trending, 10)

        if len(new_recent) > 10:
            print(f"Limited {provider_name} recent to 10 random agents from {len(new_recent)}")
            new_recent = random.sample(new_recent, 10)

        if new_trending:
            trending_title = (
                f'More than 10 trending new agents appeared on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a> this week'
                if len(agents["trending"]) > 10
                else f'🤸 Trending Agents on <a href="{agents["provider_url"]}" style="color: #005f99;"><b>{provider_name}</b></a>'
            )
            html += f'<h3 style="font-size: 16px; margin-top: 2em;">{trending_title}</h3>\n'
            for agent in new_trending:
                html += get_agent_html(agent)
            html += "\n"

        if new_recent:
            recent_title = (
                f'More than 10 new agents appeared on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a> this week'
                if len(agents["recent"]) > 10
                else f'📅 Recently added Agents on <a href="{agents["provider_url"]}" style="color: #005f99;">{provider_name}</a>'
            )
            html += f'<h3 style="font-size: 16px; margin-top: 2em;">{recent_title}</h3>\n'
            for agent in new_recent:
                html += get_agent_html(agent)
            html += "\n"


        combined_new = new_trending + new_recent
        for agent in combined_new:
            agent.provider_name = provider_name
            agent.provider_url = agents["provider_url"]

        all_new_agents.extend(combined_new)
        print(f"Found {len(combined_new)} new agents from {provider_name}")

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

    trending_papers = []
    async with HuggingFacePaperProvider() as hf:
        results = await hf.fetch_new_papers(q="agent")
        for section, papers in results.items():
            if section == "trending":
                trending_papers.extend(papers)

    print(f"Found {len(trending_papers)} trending papers from Hugging Face")
    existing_paper_response = await supabase.table("papers").select("url").execute()
    existing_paper_urls = {row["url"] for row in existing_paper_response.data}
    print(f"Found {len(existing_paper_urls)} existing papers in database")
    new_papers = [
        paper for paper in trending_papers if paper.url not in existing_paper_urls
    ]
    print(f"Found {len(new_papers)} new papers to save")
    if new_papers:
        paper_data = []
        for paper in new_papers:
            paper_data.append(
                {
                    "title": paper.title,
                    "summary": paper.summary,
                    "url": paper.url,
                    "provider_name": paper.provider_name,
                    "provider_url": paper.provider_url,
                    "ai_summary": paper.ai_summary,
                    "published_at": (
                        paper.published_at.isoformat() if paper.published_at else None
                    ),
                    "thumbnail_url": paper.thumbnail_url,
                    "upvote_count": paper.upvote_count,
                }
            )
        await supabase.table("papers").insert(paper_data).execute()
        print(f"Saved {len(new_papers)} new papers to Supabase")
    else:
        print("No new papers found to save")

    # if news fetched today use db
    today = datetime.now().date()
    news_response = (
        await supabase.table("news")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    news_summary = None
    if news_response.data:
        d = news_response.data[0]["created_at"]
        news_dt = datetime.fromisoformat(d)
        if news_dt.tzinfo is None:
            news_dt = news_dt.replace(tzinfo=timezone.utc)
        news_date_utc = news_dt.astimezone(timezone.utc).date()
        today_utc = datetime.now(timezone.utc).date()
        if news_date_utc == today_utc:
            print("Using existing news summary from database")
            news_summary = news_response.data[0]["text"]
        else:
            # print the timedelta
            delta = today - news_date_utc
            print(f"News summary is {delta.days} days old, generating a new one")

    if not news_summary:
        with open("src/prompts/gemini_news.txt", "r", encoding="utf-8") as f:
            prompt = f.read().strip()
        print("Asking Gemini to summarize the news...")
        news_summary = await gemini_with_search(
            prompt=prompt, max_tokens=10000, token=gemini_key
        )
        print("Generated news summary with Gemini")
        await supabase.table("news").insert({"text": news_summary}).execute()

    paras = [p for p in news_summary.split("\n\n") if p.strip()]
    # intro = paras[0]
    intro = "Dear readers, the past week has seen a surge in AI agent developments. Major launches from OpenAI and DeepMind, a clear shift from chatbots to autonomous systems. The race is heating up...fast"
    paras = paras[1:]  # remove the first paragraph as intro
    paras_html = [get_html_for_paragraph(p) for p in paras]
    paras_clean = [get_clean_text_for_paragraph(p) for p in paras]
    # for p in paras_clean:
    #     print(f"News paragraph: {p[:150]}...")  # print first 50 chars of each paragraph
    # grab first 3
    top_headlines = paras_clean[:3]
    print("Fetching related tweets for top headlines...")
    tasks = [get_related_tweet_from_headline(headline, google_search_key) for headline in top_headlines]
    tweets = await asyncio.gather(*tasks)
    # find whcih failed for which headline
    n = 3
    for i, tweet in enumerate(tweets):
        if tweet is None:
            n -= 1
    print("Fetched related tweets for top headlines")
    tweet_htmls = []
    tasks = [get_tweet_html(tweet["link"].split("/")[-1]) for tweet in tweets if tweet is not None]
    print(f"Found {len(tweets)} tweets, fetching HTML for {len(tasks)} tweets")
    tweet_htmls = await asyncio.gather(*tasks)
    print("Fetched HTML for related tweets")
    top_headlines_html = ""
    for i, tweet_html in enumerate(tweet_htmls):
        if tweet_html:
            top_headlines_html += f"""
            <div style="margin-bottom: 1em;">
                <p>{paras_html[i]}</p>
                <br>
                {tweet_html if tweet_html else ""}
            </div>
            <br>
            """
    formatted_news = ""
    for p in paras_html[n:]:
        formatted_news += f"""
        <div style="margin-bottom: 1em;">
            {p}
        </div>
        """

    # query title
    with open("last_title.txt", "r", encoding="utf-8") as f:
        title = f.read().strip()
    if title:
        print(f"Using existing title from database: {title}")
    else:
        print("No title found in database, generating a new one")
        with open("src/prompts/make_title.txt", "r", encoding="utf-8") as f:
            prompt = f.read().strip()
            prompt = prompt.replace("{{news}}", news_summary)

        print("Generating title for the digest...")
        title = (await gemini(prompt=prompt, max_tokens=None, token=gemini_key)).strip()
        print(f"Generated title: {title}")
        with open("last_title.txt", "w", encoding="utf-8") as f:
            f.write(title)

    # fetching reddit top posts
    print("Fetching top Reddit posts...")
    subreddits = ["chatgpt", "openai", "automation", "ai_agents"]
    q = '"ai agent"'
    reddit_posts = await fetch_top_reddit_posts(subreddits, q)
    print(f"Found {len(reddit_posts)} top Reddit posts")
    subs = ["automation", "openai"]
    ai_index = next((i for i, p in enumerate(reddit_posts) if p.subreddit.lower() == "ai_agents"), None)
    if ai_index is not None:
        for s in subs:
            s_index = next((i for i, p in enumerate(reddit_posts) if p.subreddit.lower() == s), None)
            if s_index is not None and ai_index > s_index:
                reddit_posts[ai_index], reddit_posts[s_index] = reddit_posts[s_index], reddit_posts[ai_index]
                ai_index = s_index
    with open("src/templates/reddit_post.html", "r", encoding="utf-8") as f:
        reddit_template = f.read().strip()
    reddit_htmls = []
    seen_subs = set()
    for post in reddit_posts:
        if post.subreddit in seen_subs:
            continue
        temp = env.from_string(reddit_template)
        reddit_html = temp.render(
            post=post
        )
        reddit_htmls.append(reddit_html)
        seen_subs.add(post.subreddit)
        
    formatted_reddit_posts = "<br>".join(reddit_htmls)
#  <div style="margin: auto; max-width: 700px">
    base = """
     <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>AI Agent Digest</title>
    </head>
    <body style="font-family: 'Helvetica', Arial, sans-serif; background-color: #ffffff; color: #333; padding: 20px; font-size: 16px;">
    <!-- Outer wrapper table -->
    <table role="none" width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
        <td align="center">
            <!-- Inner content table -->
            <table role="none" width="670" border="0" cellspacing="0" cellpadding="0" style="width:670px; table-layout:fixed;">
            <tr>
                <td style="text-align: left;">
                    {html}
                </td>
            </tr>
            </table>
        </td>
        </tr>
    </table>
    </body>
    </html>
"""
    with open("agents.html", "w", encoding="utf-8") as f:
        f.write(
            base.format(html=f"""
        <h1 style="
        text-align: left;
        font-family: 'Helvetica',Arial,sans-serif;
        font-weight: 400;
        font-size: 32px;
        color: #2a2a2a;
        padding: 2px 0;
        line-height: 38px;
        "><span style="font-size: 80px;">{title[0]}</span>{';<br>'.join(title[1:].split(";"))}</h1>
        <p style="font-size: 16px; color: #555;">
        A weekly digest of the latest AI agents and products, curated for you.</p>
        <hr style="border: none; height: 1px; background: linear-gradient(to right, transparent, #999, transparent); margin: 24px 0;" />
    
        {top_headlines_html}
        <h2><i>📡 On the Radar</i></h2>
        <div style="padding: 0px 10px; font-size: 14px">{formatted_news}</div>
        <br>
        <h2 style="font-family: Georgia, serif;"><span style="background-color: #f9f6f1">📃 State of the Art</span></h2>
        {render_papers_in_rows(trending_papers)}
        <br>
        <h2 style="font-weight: 400"><span><i>🦋 People Discussed...</i></span></h2>
        <div style="padding: 20px; border-radius: 20px; background-color: #f7f9fa">
        {formatted_reddit_posts}
        </div>
        <br>
        {html}
        <br>
        <hr />
        <i style="color: #536471">None of the content above is gathered by a human, it is all generated by AI agents and tools. Please always verify the information before acting on it.</i>
        <br><br>
        <i><b>© 2025 - 2025 Mohammad Momeni - All Rights Reserved.</b></i>
        """
        ))
    return len(all_new_agents)


if __name__ == "__main__":
    asyncio.run(main())
