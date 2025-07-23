from .base import Agent, AgentLib
import re
from typing import List
from urllib.parse import urlparse

def parse_readme(text: str) -> List[Agent]:
    agents: List[Agent] = []
    # regex to find project headings: ## [Name](URL)
    heading_pattern = re.compile(
        r'^## \[(?P<name>.+?)\]\((?P<url>https?://[^\)]+)\)', 
        re.MULTILINE
    )
    
    for match in heading_pattern.finditer(text):
        name = match.group('name')
        url = match.group('url')
        
        # short description: first non-empty line after the heading
        start_idx = match.end()
        short_desc = ""
        for line in text[start_idx:].splitlines():
            line = line.strip()
            if line and not line.startswith('<') and not line.startswith('#'):
                short_desc = line
                break
        
        # extracting <details>…</details> block if present
        details_start = text.find('<details>', start_idx)
        details_end = text.find('</details>', start_idx)
        details_block = ""
        if 0 <= details_start < details_end:
            details_block = text[details_start:details_end]
        
        # for long desc, bullet points under "### Description"
        long_desc = ""
        desc_section = re.search(
            r'### Description\s*(?:\n|)[\s\S]+?(?=\n### Links)', 
            details_block
        )
        if desc_section:
            bullets = re.findall(r'-\s*(.+)', desc_section.group())
            long_desc = "\n".join(bullets)
        
        hostname = urlparse(url).hostname or ""
        provider_name = hostname.split('.')[-2].capitalize() if hostname else ""
        provider_url = f"https://{hostname}"

        agents.append(Agent(
            name=name,
            url=url,
            description_short=short_desc,
            provider_name=provider_name,
            provider_url=provider_url,
            description_long=long_desc or None,
            created_at=None
        ))
    
    return agents

class AwsomeAgentLib(AgentLib):
    def __init__(self):
        super().__init__("awsome_ai_agents")
        self.url = "https://github.com/e2b-dev/awesome-ai-agents"

    async def fetch_new_agents(self):
        with open("README2.md", "r") as f:
            content = f.read()
        agents = parse_readme(content)
        return {
            "recent": agents, # assuming all agents are recent
        }
