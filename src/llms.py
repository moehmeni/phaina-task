from google import genai
from google.genai import types
from datetime import datetime, timedelta, timezone

# def add_citations(response):
#     original_text = response.text
#     supports = response.candidates[0].grounding_metadata.grounding_supports
#     chunks   = response.candidates[0].grounding_metadata.grounding_chunks

#     citations_map = {}

#     for support in supports:
#         if not support.grounding_chunk_indices:
#             continue

#         # Build citation HTML
#         links = []
#         for idx in support.grounding_chunk_indices:
#             if idx < len(chunks):
#                 uri = chunks[idx].web.uri
#                 links.append(
#                     f'<a style="font-size:10px;color:#005f99;'
#                     f'text-decoration:none;" href="{uri}" target="_blank">'
#                     f'[{idx+1}]</a>'
#                 )
#         citation_html = "".join(links)

#         # Clamp end-index to the text length
#         end = min(support.segment.end_index, len(original_text))
#         insert_at = end

#         # Move insert_at backwards over any whitespace/newlines
#         while insert_at > 0 and original_text[insert_at-1].isspace():
#             insert_at -= 1

#         citations_map.setdefault(insert_at, []).append(citation_html)

#     # Rebuild text with inline citations
#     result = []
#     for i, ch in enumerate(original_text):
#         result.append(ch)
#         if (i+1) in citations_map:
#             result.extend(citations_map[i+1])

#     text = "".join(result)

#     # “Here” line removal (preserves blank lines)
#     lines = text.splitlines(keepends=True)
#     if len(lines) > 5:
#         for i in range(5):
#             if lines[i].lstrip().startswith("Here"):
#                 lines[i] = "\n"
#                 break

#     return "".join(lines)


def add_citations(response):
    original_text = response.text
    supports = response.candidates[0].grounding_metadata.grounding_supports
    chunks = response.candidates[0].grounding_metadata.grounding_chunks

    # Build a mapping from support end_index → first citation URL
    support_uris = {}
    for s in supports:
        if s.grounding_chunk_indices:
            idx = s.grounding_chunk_indices[0]
            if idx < len(chunks):
                uri = chunks[idx].web.uri
                end_index = min(s.segment.end_index, len(original_text))
                support_uris.setdefault(end_index, uri)

    # Build paragraph map: one "more" per paragraph, from first matching citation
    paragraphs = original_text.splitlines(keepends=True)
    rebuilt_lines = []
    char_cursor = 0
    paragraph_buffer = []
    para_start = 0

    for line in paragraphs + ["\n"]:  # force flush at end
        if line.strip() == "":
            # End of a paragraph
            para_text = "".join(paragraph_buffer)
            para_end = char_cursor

            # Check if any citation falls within this paragraph span
            first_uri = None
            for idx in sorted(support_uris):
                if para_start <= idx <= para_end:
                    first_uri = support_uris[idx]
                    break

            # If we found one, append the "more" link before trailing newlines
            if first_uri:
                more_link = (
                    f'<a style="font-size:10px;color:#005f99" '
                    f'href="{first_uri}" target="_blank">more</a>'
                )
                # Insert before trailing newline(s)
                if para_text.endswith("\n"):
                    stripped = para_text.rstrip("\n")
                    trailing = para_text[len(stripped) :]
                    para_text = stripped + more_link + trailing
                else:
                    para_text += more_link
            rebuilt_lines.append(para_text)
            rebuilt_lines.append(line)  # preserve the blank line
            paragraph_buffer = []
            para_start = char_cursor + len(line)
        else:
            paragraph_buffer.append(line)
        char_cursor += len(line)
    text = "".join(rebuilt_lines)
    # remove "Here's" like lines from the first 5 lines
    lines = text.splitlines(keepends=True)
    for i in range(min(5, len(lines))):
        if lines[i].lstrip().startswith("Here"):
            lines[i] = "\n"  # keep spacing
            break
    return "".join(lines)

def to_utc(d: datetime) -> datetime:
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    else:
        d = d.astimezone(timezone.utc)
    return d.replace(microsecond=0)  # truncate to second precision

async def gemini_with_search(
    prompt: str,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 1000,
    temperature: float = 1,
    start_time: datetime = datetime.now() - timedelta(days=10),
    end_time: datetime = datetime.now(),
    token=None,
    include_citations: bool = True,
):
    start_time = to_utc(start_time)
    end_time = to_utc(end_time)
    client = genai.Client(api_key=token)
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch(
            time_range_filter=types.Interval(start_time=start_time, end_time=end_time)
        )
    )
    config = types.GenerateContentConfig(
        tools=[grounding_tool], max_output_tokens=max_tokens, temperature=temperature
    )
    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    if include_citations:
        return add_citations(response)
    return response.text
