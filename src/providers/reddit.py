from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin


@dataclass
class RedditPost:
    url: str
    subreddit: str
    subreddit_image: str
    title: str
    created_at: datetime
    score: int
    num_comments: int


async def get_soup(url: str, session: ClientSession) -> BeautifulSoup:
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "text/PLAIN",
        "origin": "https://www.reddit.com",
        "priority": "u=1, i",
        "referer": "https://www.reddit.com/search/?q=%28subreddit%3Achatgpt+OR+subreddit%3Aopenai+OR+subreddit%3Aautomation%29%22ai+agent%22&type=posts&sort=top&t=week",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-sh-microapp-route": "search",
        # 'cookie': 'loid=0000000011m0ahhee8.2.1717285787523.Z0FBQUFBQm1XN09iUHV3WkZCbElndWRpcEQ5UzlGQ3FsM2Ntc3RsdFQtZGxxVUFncTJsb3BDd0ZrSE5XeGljcDJoWHJaWjNLZlZ0b2pNb192eXJEaG5GendGQTdobW1FNlFtVndsLTlaeXVvMV9QdVlaZlg4UUZUYU9UbHQtc0k3aDNhTW5xSlNpalU; __stripe_mid=9de6327a-119a-4153-99f8-d2b18ca9e8b7493962; csrf_token=a5f1521c29d9b0324e5ec8f236ca358a; token_v2=eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJsb2lkIiwiZXhwIjoxNzUzNjIyODg0Ljc0NzQ3NSwiaWF0IjoxNzUzNTM2NDg0Ljc0NzQ3NSwianRpIjoiejJUUGNDdURFNWp0TGdoMGUyTzRZQjdVNGhyZnRBIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xMW0wYWhoZWU4IiwibGNhIjoxNzE3Mjg1Nzg3NTIzLCJzY3AiOiJlSnhra2RHT3REQUloZC1GYTVfZ2Y1VV9tMDF0Y1lhc0xRYW9rM243RFZvY2s3MDdjRDRwSFA5REtvcUZEQ1pYZ3FuQUJGZ1RyVERCUnVUOW5MbTNnMmlOZTh0WXNabkNCRm13RkRya21MR3NpUVFtZUpJYXl4c21vSUxOeUZ5dXRHTk5MVDBRSnFoY01yZUZIcGMyb2JrYmk1NmRHRlc1ckR5b3NWZmwwdGpHRkxZbnhqY2JxdzJwdUM2bk1rbkxRdmtzWHZUak45VzM5dm16X1NhMEo4T0txdW1CM2hsSkNHNHNmcGltM2Q5VGs1NnRDeGExOTNxUTJ1ZDYzSzU5MWl3ME83ZWY2X2xySXhtWFkyaC1KdnQzMXktaEE0ODhMelBxQUVhczRVY1pkbVFkX2xVSFVMbWdKR01KNHRNSTVNcmwyMzhKdG12VHY4YnRFejk4TS1LbU5feldETlJ6Q2VMUXBfSDFHd0FBX184UTFlVFIiLCJmbG8iOjF9.LeWqTK6-uTpw6MNFrWGUAU_9IkvR4EzcKa5NkoZm-lhH8WKyaafkcV3NvXLjjYBCktheeEOkY1zeBsuuYZZR6Pk3t2fPsPJzNqPgjOrqIO2_s9kxgqyk_1qHS48Ny1q53dpVeNOYZcXxpVk2j-_6pcK-jpI4_NmLSVvUkkN6GbvC86lAod44USjI0TjPyqoVZ-QbHRElA3SlEMlhKBYGDNjewJ0GOJhDBlonqlYtiRbuU8DjdwqD9rAaROBkrcXiXWXsjT7Hp5s1hex9w9dKl6u-UkKWbGYc-ymDf2uOxD4nl0bqmxsBX0LVmvyuQ8MxTFs6-LufJBeKlPjEQZstkA; csv=2; edgebucket=JguzI8slziKAAt6Gsr; session_tracker=hfaofdpdachqklialg.0.1753536492863.Z0FBQUFBQm9oTmZzdmdKX3dGdDFGQWRvdm9Ib3pYLUZ3NncxZ0hGWDJxZDVILTVmZHZsOENsUmxWMzZUWmE3Vlc2TV9UanVFNWQ5OEdPd0pvZGEtVkNmRHQzYnFrbWRGZ1RPaV9EVS1lYnJUTHoyc1gtUXRhLVhEZTc1eWdLTVBfZHBWTHBQSWZqeVg',
    }
    async with session.get(url, headers=headers) as response:
        if response.ok:
            print(response.url)
            html = await response.text()
            return BeautifulSoup(html, "html.parser")
        else:
            raise Exception(f"Failed to fetch {url}: {response.status}")


async def fetch_top_reddit_posts(subreddits: List[str], q: str, period: str = "week"):
    async with ClientSession() as session:
        url = f"https://www.reddit.com/search/?q=(subreddit%3A{'%20OR%20subreddit%3A'.join(subreddits)})+{q}&type=posts&sort=top&t={period}"
        soup = await get_soup(url, session)
        # save to html
        with open("reddit_search_results.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        posts = []
        for post in soup.select('main *[data-testid="search-post-unit"]'):
            title = post.select_one("a").get_text(strip=True)
            url = urljoin("https://www.reddit.com", post.select_one("a").get("href"))
            nums = post.select('[data-testid="search-counter-row"] faceplate-number')
            votes = int(nums[0].get("number"))
            comments = int(nums[1].get("number"))
            # time format is 2025-07-25T21:44:51.654Z
            date_raw = post.select_one("faceplate-timeago").get("ts")
            created_at = datetime.strptime(
                date_raw, "%Y-%m-%dT%H:%M:%S.%f%z"
            ).astimezone(timezone.utc)
            subreddit = (
                post.select_one("faceplate-hovercard").get("aria-label").split("r/")[-1]
            )
            image_url = post.select_one("faceplate-hovercard a.flex img")
            # print(
            #     f"{created_at}\nr/{subreddit}\nTitle: {title}\nVotes: {votes}\nComments: {comments}\n{url}\n"
            # )
            posts.append(
                RedditPost(
                    url=url,
                    subreddit=subreddit,
                    subreddit_image=image_url["src"],
                    title=title,
                    created_at=created_at,
                    score=votes,
                    num_comments=comments,
                )
            )
        return posts


if __name__ == "__main__":
    import asyncio

    subreddits = ["chatgpt", "openai", "automation", "ai_agents"]
    q = '"ai agent"'
    period = "week"

    asyncio.run(fetch_top_reddit_posts(subreddits, q, period))
