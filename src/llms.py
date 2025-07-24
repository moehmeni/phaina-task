from google import genai
from google.genai import types

async def gemini_with_search(
    prompt: str,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 1000,
    temperature: float = 1,
    token = None
):
    client = genai.Client(api_key=token)
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        max_output_tokens=max_tokens,
        temperature=temperature
    )
    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    return response.text