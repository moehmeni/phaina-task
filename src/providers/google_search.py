from aiohttp import ClientSession
from datetime import datetime, timezone
import json
import spacy
import re
from wordfreq import word_frequency

nlp = spacy.load("en_core_web_sm")


async def fetch_google_search(q: str, token: str):
    cx = "873468c8d29584ba4"
    url = f"https://www.googleapis.com/customsearch/v1?key={token}&cx={cx}&q={q}"
    async with ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an error for bad responses
            data = await response.json()
            with open("google_search_results.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return data.get("items", [])


async def get_related_tweet(q: str, token: str, min_likes : int):
    items = await fetch_google_search(q, token)
    print(f"[get_related_tweet] {len(items)} items found for query: {q}")
    tweets = []
    for item in items:
        # pagemap.interactioncounter[(interactiontype == 'https://schema.org/LikeAction') & (name == 'Likes')]
        if item.get("pagemap", {}).get("interactioncounter", []):
            if not "/status/" in item.get("link", ""):
                continue
            # print len of item["pagemap"]["interactioncounter"]
            print(
                f"[get_related_tweet] Found item with pagemap.interactioncounter: {len(item['pagemap']['interactioncounter'])} interactions"
            )
            for interaction in item["pagemap"]["interactioncounter"]:
                if (
                    interaction.get("interactiontype")
                    == "https://schema.org/LikeAction"
                    and interaction.get("name") == "Likes"
                ):
                    likes = int(interaction.get("userinteractioncount", 0))
                    if likes < min_likes:
                        continue
                    page_title = item["pagemap"]["metatags"][0].get("og:title", "N/A")
                    # the username is in the title e.g '<name> (@username) on X'
                    name, username = page_title.split(" on X")[0].split(" (@")
                    date_str = item["pagemap"]["socialmediaposting"][0].get(
                        "datepublished"
                    )
                    thread = item["pagemap"]["socialmediaposting"][0].get("ispartof")
                    published_at = (
                        datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        if date_str
                        else None
                    )
                    tweets.append(
                        {
                            "title": item.get("title"),
                            "link": item.get("link"),
                            "likes": likes,
                            "username": username,
                            "author_name": name,
                            "published_at": published_at,
                            "part_of_thread": thread,  # link to the thread if available
                        }
                    )
        else:
            print(
                f"[get_related_tweet] Skipping item without pagemap.interactioncounter: {item.get('link')}"
            )
            continue

    if not tweets:
        print("No tweets found for the query.")
        return None
    tweets.sort(key=lambda x: x["likes"], reverse=True)
    tweets.sort(
        key=lambda x: x["published_at"] if x["published_at"] else datetime.min,
        reverse=True,
    )

    picked = None
    for tweet in tweets:
        print(f"Published at: {tweet['published_at']}")
        print(f"Author: {tweet['author_name']} (@{tweet['username']})")
        print(f"Title: {tweet['title']}")
        print(f"Link: {tweet['link']}")
        print(f"Likes: {tweet['likes']}")
        print("-" * 40)

        # better search to just inclusion of the author name
        s = tweet["author_name"].lower()
        # and also the date is within the last 14days
        now = datetime.now(timezone.utc)
        delta_days = (now - tweet["published_at"]).days if tweet["published_at"] else 15
        if s in q.lower() or s.split()[0] in q.lower():
            if delta_days <= 14:
                print("Tweet is within the last 14 days.")
                print("Picked tweet based on user:")
                print(tweet["link"])
                picked = tweet
                break
            else:
                print("Tweet is older than 14 days, skipping.")

    # pick the first one if no tweet matched the user
    if not picked:
        picked = tweets[0]
        print("Picked the first tweet as no user match was found.")
        print(picked["link"])

    if picked.get("part_of_thread"):
        print("=======> This tweet is part of a thread")

    return picked


def get_main_kws(
    model, text: str, freq_threshold: float = 3.5e-05, keep_words: list = []
):
    keywords = []
    t = clean_text_for_nlp(text)
    # print("-" * 40)
    # print(f"Original text: {text}")
    # print(f"Cleaned text for NLP: {t}")
    doc = model(t)
    for token in doc:
        if token.is_stop or token.is_punct:
            continue
        is_relevant_pos = token.pos_ in {"NOUN", "PROPN", "NUM"}
        is_num = token.pos_ == "NUM"
        has_cap = any(c.isupper() for c in token.text)
        f = word_frequency(token.text.lower(), "en")
        is_rare = f < freq_threshold
        allowed = token.text.lower() in keep_words
        # print(f"Word: {token.text}, Frequency: {f}", "is_rare:", is_rare)

        if allowed or has_cap or is_num or (is_relevant_pos and is_rare):
            keywords.append(token.text)

    final = " ".join(keywords)
    # append all the words in between ' or " with length less than 20
    those_inside_quotes = re.findall(r"['\"“](.{1,20}?)['\"”]", text)
    for word in those_inside_quotes:
        if word.lower() not in final.lower() and word[0].isupper():
            final += " " + word

    # remove 'and', 'of', 'the', 'a', 'to', 'in', 'for', 'on'
    final = re.sub(r"\b(and|of|the|a|to|in|for|on)\b", "", final, flags=re.IGNORECASE)

    return final


def clean_text_for_nlp(text: str):
    tokens = text.strip().split()
    months = {
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    }
    start_index = 0
    for i, token in enumerate(tokens):
        word = re.sub(r"[^\w]", "", token).lower()  # remove punctuation and lowercase
        if not word:
            continue
        if word.isalpha() and word not in months:
            start_index = i
            break

    cleaned_text = " ".join(tokens[start_index:])
    chunks = re.split(r"[.,;]", cleaned_text)
    result = []
    total_words = 0
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        result.append(chunk)
        total_words = len(" ".join(result).split())
        if total_words >= 3:
            break
    if total_words < 2:
        print("Text is too short after cleaning.")
        return None
    return " ".join(result)


async def get_related_tweet_from_headline(text: str, google_search_key: str, min_likes: int = 40):
    allowed = [
        "agent",
        "agents",
        "ai",
        "assistant",
    ]
    kws = get_main_kws(nlp, text, keep_words=allowed)
    kws = " ".join(kws.split()[:5])
    print(f"Keywords extracted for tweet search: {kws}")
    print("-" * 40)
    tweet = await get_related_tweet(kws, google_search_key, min_likes)
    return tweet


# async def main():
# import dotenv
# dotenv.load_dotenv()


# text = "Perplexity AI has introduced Comet, a Chromium-based browser with agentic browsing capabilities, allowing users to offload tasks such as trip planning and restaurant bookings to an embedded AI assistant for enhanced efficiency. The company also secured $100 million in funding, tripling its valuation to $18 billion in the past year.more"
# text = "OpenAI has launched its ChatGPT agent, a new tool empowering Pro, Plus, and Team users to automate complex, real-world tasks like competitor analysis and event planning through web browsing, deep research, and terminal access, including integrations with Gmail and GitHub. This marks a significant step towards practical agentic AI.more"
# text = "AWS has unveiled its 'AI Agents and Tools' category within its Marketplace, providing businesses with over 900 deployable AI agents from providers like Anthropic, Salesforce, IBM, and PwC. This platform aims to simplify the procurement and deployment of secure, governed AI agents for enterprise use cases such as procurement and document intelligence.more"
# text = "Google has expanded its AI capabilities, launching AI-powered business calling that allows users to get appointment and pricing information from local businesses without making a direct call. Furthermore, Google Search's AI Mode has been upgraded with Gemini 2.5 Pro for advanced reasoning, and a 'Deep Search' feature to generate cited reports from multiple sources.more"
# text = "Mixus has achieved a historic first with enterprise-grade AI agents that possess organizational context awareness, allowing them to navigate complex organizational structures by cross-referencing tools like Jira for task ownership and overdue assignments, overcoming previous 'shared memory' limitations.more"
# text = "Upstage AI announced that its Solar Pro 2 model has broken into the global frontier AI landscape, with its Document Intelligence now available in the new AWS Marketplace AI Agents and Tools category, showcasing its competitive performance against models like GPT-3.5.more"
# text = "Cursor AI has introduced 'Background Agents' in early 2025, enabling developers to run autonomous AI agents for tasks like code generation, debugging, and refactoring without interrupting their main workflow. These agents can now be initiated directly from Slack and handle multi-file edits with response times under 200ms.more"
# text = "July 26, 2025: Google DeepMind unveiled Aeneas, an AI tool designed"
# text = "July 24, 2025: LegalOn Technologies, an AI-driven software provider for contract review, s"
# text = "July 23, 2025: Berlin-based startup Droidrun raised €2.1 million in pre-seed funding to scale its mobile-native AI agent infrastructure. Droi"
# text = "July 12, 2025: Snowflake launched its Data Science Agent at Snowflake Summit 2025, an agentic AI tool that utilizes An"
# allowed = [
#     "agent",
#     "agents",
#     "ai",
#     "assistant",
# ]
# kws = get_main_kws(nlp, text, keep_words=allowed)
# kws = " ".join(kws.split()[:5])
# print(kws)

# tweet = await get_related_tweet(kws)
# if tweet:
#     print(f"Found related tweet:")
#     print(f"Author: {tweet['author_name']} (@{tweet['username']})")
#     print(f"Title: {tweet['title']}")
#     print(f"Link: {tweet.get('part_of_thread', tweet['link'])}")
#     print(f"Likes: {tweet['likes']}")
#     print(f"Published at: {tweet['published_at']}")
# else:
#     print("No related tweet found.")


# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
