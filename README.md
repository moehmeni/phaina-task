# phaina-task
A curated newsletter about AI agents

### Content
I came up with three main parts to show in the emails:
1. New AI Agents - recent releases or updates
2. What was new this month in the AI agent industry


### Resources
#### Agents
I gather newly developed agents that are actively maintained
from multi AI agent libraries.
Using a deep research option of Grok chat bot and also searching myself, I found the following providers:

1. [n8n](https://n8n.io/workflows/):\
Many developers publish their n8n workflows which is a form of node based agent building
2. [Awsome AI Agents](https://github.com/e2b-dev/awesome-ai-agents):\
Popular GitHub repo
3. [AI Agent List](https://aiagentslist.com/?sort=createdAt.desc)
4. [AI Agents Live](https://aiagentslive.com/agents/2)

For each of them, I developed a seperate web crawler built with modular design for easy maitainability.
You can see their implementation in the `src/providers` directory of this repo.

#### News
For fetching the latest news about AI agents I used Google Gemini 2.5 flash model with their builtin search tool as they have explained the API tools and how it works in detail [here](https://ai.google.dev/gemini-api/docs/google-search).

I tried multiple prompts to get a suitable output with least amount of work, so at the end this prompt gave me good results:
> *Gather all the latest news in July about AI agents and new workflows, make up to 10 concise one paragraph easy-to-read friendly brief of what happened. 
Make sure the paragraphs are not ChatGPT style and like a pro human reviewer wrote them! each paragraph starts with a summarised title about the content of that paragraph in bold and next line starts the content. DO NOT make general titles and be specific about it (numbers, company names, anything clickbait)
please include the use and ability of each agent exactly if mentioned.*
