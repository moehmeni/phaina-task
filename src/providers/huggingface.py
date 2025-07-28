from .base import Paper, PaperLib
from datetime import datetime
from typing import List, Dict


class HuggingFacePaperProvider(PaperLib):
    def __init__(self):
        super().__init__(name="huggingface-papers")
        self.api_url = "https://huggingface.co/api/papers/search"

    async def fetch_new_papers(self, q: str = "agent", k : int = 4) -> Dict[str, List[Paper]]:
        async with self.session.get(self.api_url, params={"q": q}) as response:
            if not response.ok:
                raise Exception(f"Failed to fetch papers: {response.status}")
            data = await response.json()

        papers: List[Paper] = []

        for item in data:
            paper_data = item.get("paper", {})
            if not paper_data:
                continue

            title = paper_data.get("title", "").replace("\n", " ").strip()
            summary = paper_data.get("summary", "").replace("\n", " ").strip()
            paper_id = paper_data.get("id")
            url = f"https://huggingface.co/papers/{paper_id}"
            provider_url = "https://huggingface.co/papers"
            thumbnail_url = item.get("thumbnail")
            published_at = None

            if "publishedAt" in paper_data:
                try:
                    published_at = datetime.fromisoformat(
                        paper_data["publishedAt"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            authors = [
                author.get("name")
                for author in paper_data.get("authors", [])
                if "name" in author
            ]

            papers.append(
                Paper(
                    title=title,
                    summary=summary,
                    url=url,
                    provider_name="Hugging Face",
                    provider_url=provider_url,
                    published_at=published_at,
                    ai_summary=paper_data.get("ai_summary"),
                    authors=authors,
                    thumbnail_url=thumbnail_url,
                    upvote_count=paper_data.get("upvotes", 0),
                )
            )

        # sort papers by upvote count in descending order
        papers.sort(key=lambda x: x.upvote_count, reverse=True)
        papers = papers[:30]
        papers.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        papers = papers[:k]
        return {"trending": papers}
