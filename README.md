# phaina-task
A curated newsletter about AI agents

### Overview
I came up with five main parts to show:
1. New AI Agents - recent releases or updates
2. What was new this month in the AI agent industry
3. New or trending AI agent papers and research
4. Startups and acquisitions in the AI agent space (mixed with [1])
5. What is hot on social media (X, Reddit, etc.) about AI agents

### Quick Access
[Agents](#agents) - [News](#news) - [Title](#title) - [Social Media](#social-media) -  [Papers](#papers) - [Database](#database)

### Sections
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
The main challenge of the project probably lied here since each website has its own structure and way of presenting the data, I had to write a custom parser for each one of them.

#### News
For fetching the latest news about AI agents I used Google Gemini 2.5 flash model with their builtin search tool as they have explained the API tools and how it works in detail [here](https://ai.google.dev/gemini-api/docs/google-search).

I tried multiple prompts to get a suitable output with least amount of work, so at the end this prompt gave me good results:
> *Gather all the latest news in the last week about AI agents and tools and new workflows, make up to 10 concise one paragraph easy-to-read friendly brief of what happened.
Keep in mind they should be informative yet very short, so each paragraph should be maximum 2 or 3 lines and move to next cluster to cover all agent news specifically new ones and startups.
make sure the paragraphs are not ChatGPT style and like an experienced journalist wrote them!
please include the usecases and ability of each agent exactly if mentioned.
underline great numbers, or achievements, or any other important information with html tag <u>that part</u>.
The company names or products should be **bolded** in the paragraph once mentioned for **first time** not anymore.
The order of news should be priority based on the date of that news or if it is a big company news.
You only return the paragraphs please without anything else not even classifying or another self-made titles.*

#### Social Media
To grab trending posts on social media, I used a custom algorithm for Reddit to find the most upvoted posts in the last week about AI agents in related subreddits such as:
- r/ChatGPT
- r/OpenAI
- r/Automation
- r/AI_Agents

Thanks to an efficient API reverse engineering I did on Reddit, I was able to fetch the posts and all the necessary data with only one search request and scraping the search results page.

For Twitter (X), it was harder as they closed the platform to non-user developers and the API is not free anymore.

##### Tweet Embedding Challenge
Email clients' HTML rendering is old, and you cannot easily use modern CSS features like flexbox or grid.\
I had to build a custom HTML template for the X posts to be displayed nicely in the email.\
I used Twitter's embedding API to catch the posts data and fill the template.\
Another feature I came up was related to tweets with videos as I used Pillow to add an play icon at the center of the video thumbnail to make it look like a video post, since there is no support for absolute elements in emails.

#### Final Title
I had quite bit of challenge to make Gemini generate a good title for the newsletter. After around 10 minutes of different prompt engineering, and few-shot examples, I came up with the prompt located at `src/prompts/make_title.txt` which works well enough.

#### Papers
I believe it's important to keep up with the latest research in the field especially for developers or researchers.
To find the latest papers about AI agents, I used `Hugging Face`. Since there exists a tremendous amount of papers daily in the AI space, there should be some kind of scoring or ranking system to find the most relevant ones. Neverthless, I found that the `Hugging Face` papers have this option and it would be a better resource in compare to other paper aggregators like `arXiv` or `Papers with Code`.
You can explore the page [here](https://huggingface.co/papers/month/2025-07?q=agent).

### Database
For storing the data I used Supabase as it is a good open source alternative to Firebase and has a free tier. It is easy to use and yet very scalable which is powered by `PostgreSQL`.
Based on the period of the newsletter, every month or week I will fetch the data from the providers and store them in the database so that I can detect new agents added.