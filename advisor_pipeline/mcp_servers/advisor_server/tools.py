"""MCP tools for the Advisor server.

Wraps paper loading, database operations, and citation-checking utilities
as MCP-compatible tool functions.
"""

import json
import re
from pathlib import Path

import httpx
from mcp.types import TextContent, Tool



def _success(result: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


def _error(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}))]


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    Tool(
        name="load_paper",
        description="Load paper text and figure images from a folder on disk.",
        inputSchema={
            "type": "object",
            "properties": {
                "paper_folder": {
                    "type": "string",
                    "description": "Path to folder containing main_text.tex and images/ subfolder",
                },
            },
            "required": ["paper_folder"],
        },
    ),
    Tool(
        name="search_semantic_scholar",
        description="Search for a paper using the Semantic Scholar API.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_paper_abstract",
        description="Retrieve abstract of a paper via Semantic Scholar (by DOI or paper ID).",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "DOI (starting with 10.) or Semantic Scholar paper ID",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="check_paper_accessibility",
        description="Check if a paper is publicly accessible via Semantic Scholar.",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "DOI or Semantic Scholar paper ID"},
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="extract_doi",
        description="Extract a DOI from a citation string.",
        inputSchema={
            "type": "object",
            "properties": {
                "citation": {"type": "string", "description": "Citation text to search for DOI"},
            },
            "required": ["citation"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def handle_load_paper(arguments: dict) -> list[TextContent]:
    paper_folder = Path(arguments["paper_folder"])
    paper_path = paper_folder / "main_text.tex"
    if not paper_path.exists():
        return _error(f"Paper file not found: {paper_path}")

    with open(paper_path) as f:
        paper_text = f.read()

    figures: dict[str, dict[str, str]] = {}
    image_folder = paper_folder / "images"
    if image_folder.exists():
        for img_path in image_folder.iterdir():
            if img_path.is_file():
                img_data, media_type = _encode_image(img_path)
                figures[img_path.name] = {"data": img_data, "media_type": media_type}

    return _success({"paper_text": paper_text, "figures": figures})


async def handle_search_semantic_scholar(arguments: dict) -> list[TextContent]:
    query = arguments["query"]
    limit = arguments.get("limit", 5)
    try:
        response = httpx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,abstract,externalIds",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("data", [])
        if not results:
            return _success({"results": [], "message": f"No results for '{query}'"})

        papers = []
        for paper in results:
            external_ids = paper.get("externalIds", {}) or {}
            authors_list = paper.get("authors", [])
            author_names = ", ".join(a.get("name", "Unknown") for a in authors_list[:3])
            if len(authors_list) > 3:
                author_names += " et al."
            papers.append(
                {
                    "title": paper.get("title", "Unknown"),
                    "authors": author_names,
                    "year": paper.get("year"),
                    "doi": external_ids.get("DOI", "N/A"),
                    "paper_id": paper.get("paperId", "N/A"),
                }
            )
        return _success({"results": papers})
    except Exception as e:
        return _error(f"Search error: {e}")


async def handle_get_paper_abstract(arguments: dict) -> list[TextContent]:
    identifier = arguments["identifier"].strip()
    try:
        if identifier.startswith("10."):
            api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{identifier}"
        else:
            api_url = f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"

        response = httpx.get(
            api_url,
            params={"fields": "abstract,title,authors,year"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        authors_list = data.get("authors", [])
        author_names = ", ".join(a.get("name", "Unknown") for a in authors_list[:5])
        if len(authors_list) > 5:
            author_names += " et al."

        return _success(
            {
                "title": data.get("title", "Unknown"),
                "authors": author_names,
                "year": data.get("year"),
                "abstract": data.get("abstract", "No abstract available."),
            }
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _error(f"Paper not found: '{identifier}'")
        return _error(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        return _error(f"Error: {e}")


async def handle_check_paper_accessibility(arguments: dict) -> list[TextContent]:
    identifier = arguments["identifier"].strip()
    try:
        if identifier.startswith("10."):
            api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{identifier}"
        else:
            api_url = f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"

        response = httpx.get(
            api_url,
            params={"fields": "isOpenAccess,openAccessPdf,url"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        open_access_pdf = data.get("openAccessPdf")
        return _success(
            {
                "url": data.get("url", "N/A"),
                "is_open_access": data.get("isOpenAccess", False),
                "pdf_url": open_access_pdf.get("url") if open_access_pdf else None,
            }
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _error(f"Paper not found: '{identifier}'")
        return _error(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        return _error(f"Error: {e}")


async def handle_extract_doi(arguments: dict) -> list[TextContent]:
    citation = arguments["citation"]
    doi_pattern = r"10\.\d{4,}/[^\s]+"
    match = re.search(doi_pattern, citation)
    if match:
        return _success({"doi": match.group(0)})
    return _success({"doi": None, "message": "No DOI found in citation"})


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

_HANDLERS = {
    "load_paper": handle_load_paper,
    "search_semantic_scholar": handle_search_semantic_scholar,
    "get_paper_abstract": handle_get_paper_abstract,
    "check_paper_accessibility": handle_check_paper_accessibility,
    "extract_doi": handle_extract_doi,
}


def get_all_tools() -> list[Tool]:
    return TOOLS


async def handle_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = _HANDLERS.get(name)
    if handler is None:
        return _error(f"Unknown tool: '{name}'")
    return await handler(arguments)
