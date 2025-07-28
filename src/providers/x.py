from dataclasses import dataclass
from typing import Optional, List
from jinja2 import Environment
from datetime import datetime
import re
import base64
from PIL import Image
from io import BytesIO
from aiohttp import ClientSession

@dataclass
class MediaDetail:
    type: str
    thumbnail_url: str
    thumbnail_uri: Optional[str] = None
    best_video_url: Optional[str] = None


@dataclass
class TweetInfo:
    url: str
    author_name: str
    username: str
    tweet_text: str
    created_at: datetime
    likes: int
    replies: int
    media: List[MediaDetail]
    author_profile: str
    author_id: str
    author_blue_verified: bool = False
    author_verified_type: str = "N/A"
    author_profile_shape: str = "circle"


def intword_abbr(value):
    # Based on jinja2-humanize logic
    units = [
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "k"),
    ]
    try:
        value = float(value)
        for factor, suffix in units:
            if abs(value) >= factor:
                return f"{value / factor:.1f}".rstrip("0").rstrip(".") + suffix
        return str(int(value)) if value == int(value) else str(value)
    except (ValueError, TypeError):
        return value


async def open_image(path_or_url):
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        async with ClientSession() as session:
            async with session.get(path_or_url) as response:
                response.raise_for_status()
                content = await response.read()
                return Image.open(BytesIO(content))
    else:
        return Image.open(path_or_url)


async def overlay_center_and_get_data_uri(bg_path, ov_path, out_path="out.png", max_size=320):
    b = (await open_image(bg_path)).convert("RGBA")
    o = (await open_image(ov_path)).convert("RGBA")
    p = ((b.size[0] - o.size[0]) // 2, (b.size[1] - o.size[1]) // 2)
    b.paste(o, p, o)
    b.thumbnail((max_size, max_size), Image.LANCZOS)
    b = b.convert("RGB").convert("P", palette=Image.ADAPTIVE)
    b.save(out_path, optimize=True)
    buf = BytesIO()
    b.save(buf, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


env = Environment()
env.filters["human_count"] = intword_abbr


async def fetch_tweet_info(tweet_id: str, lang: str = "en") -> Optional[TweetInfo]:
    if not tweet_id.isdigit():
        return None
    url = "https://cdn.syndication.twimg.com/tweet-result"
    params = {
        "id": tweet_id,
        "lang": lang,
        "features": "tfw_timeline_list:,tfw_follower_count_sunset:true,tfw_tweet_edit_backend:on,tfw_refsrc_session:on,tfw_show_business_verified_badge:on,tfw_duplicate_scribes_to_settings:on,tfw_use_profile_image_shape_enabled:on,tfw_show_blue_verified_badge:on,tfw_legacy_timeline_sunset:true,tfw_show_gov_affiliate_badge:on,tfw_show_business_affiliate_badge:on,tfw_tweet_edit_frontend:on",
        "token": "4",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    async with ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as r:
            r.raise_for_status()
            d = await r.json()
            with open("tweet.json", "w", encoding="utf-8") as f:
                import json
                json.dump(d, f, ensure_ascii=False, indent=4)
            user = d.get("user", {})
            media_list = []
            for i, m in enumerate(d.get("mediaDetails", [])):
                uri = None
                t = m.get("type", "N/A")
                thumb = m.get("media_url_https", "N/A")
                vurl = None
                if t == "video" and "video_info" in m:
                    variants = [
                        v
                        for v in m["video_info"].get("variants", [])
                        if v.get("content_type") == "video/mp4" and "bitrate" in v
                    ]
                    if variants:
                        vurl = sorted(
                            variants, key=lambda v: v["bitrate"], reverse=True
                        )[0].get("url")
                    if i == 0:
                        uri = await overlay_center_and_get_data_uri(
                            thumb, "play.png", f"output_{tweet_id}.png"
                        )

                media_list.append(
                    MediaDetail(
                        type=t,
                        thumbnail_url=thumb,
                        best_video_url=vurl,
                        thumbnail_uri=uri,
                    )
                )
    t = d.get("text", "N/A")
    # remove the last word since it is usually a link to the tweet itself
    t = re.sub(r"https://t\.co/\S+\s*$", "", t)
    return TweetInfo(
        url=f"https://x.com/{user.get('screen_name')}/status/{tweet_id}",
        author_name=user.get("name", "N/A"),
        username=user.get("screen_name", "N/A"),
        tweet_text=t,
        created_at=datetime.strptime(
            d.get("created_at", "1970-01-01T00:00:00.000Z"), "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        likes=d.get("favorite_count", 0),
        replies=d.get("conversation_count", 0),
        media=media_list,
        author_profile=user.get("profile_image_url_https", "N/A"),
        author_id=user.get("id_str", "N/A"),
        author_blue_verified=user.get("is_blue_verified", False),
        author_verified_type=user.get("verified_type", "N/A"),
        author_profile_shape=user.get("profile_image_shape", "circle").lower(),
    )


async def get_tweet_html(tweet_id : str):
    # tweet_id_with_image = "1948101877486452897"
    # # tweet_id_with_image = "1948842670949904541"
    # tweet_id_with_image = "1894068197936304296"
    tweet_info = await fetch_tweet_info(tweet_id)
    # if tweet_info:
    #     print(f"Author: {tweet_info.author_name} (@{tweet_info.username})")
    #     print(f"Tweet: {tweet_info.tweet_text}")
    #     print(f"Created at: {tweet_info.created_at}")
    #     print(f"Likes: {tweet_info.likes}, Replies: {tweet_info.replies}")
    #     print(f"Author Blue Verified: {tweet_info.author_blue_verified}")
    #     print(f"Author Verified Type: {tweet_info.author_verified_type}")
    #     for media in tweet_info.media:
    #         print(
    #             f"Media Type: {media.type}, Thumbnail: {media.thumbnail_url}, Video URL: {media.best_video_url}"
    #         )
    # else:
    #     print("Failed to fetch tweet info.")

    with open("src/templates/tweet.html", "r") as f:
        template_content = f.read()
    template = env.from_string(template_content)
    html_email = template.render(tweet_info=tweet_info)
    return html_email
    # with open("output_email.html", "w") as f:
    #     f.write(html_email)

# # --- Example Usage ---
# if __name__ == "__main__":
#     # # Example Tweet with an image
#     # # ID for https://twitter.com/NASA/status/1547649588632604675
#     # # https://x.com/satyanadella/status/1948101877486452897
#     # # tweet_id_with_image = "1948037924882133390"
    
#     import asyncio
#     asyncio.run(test())
