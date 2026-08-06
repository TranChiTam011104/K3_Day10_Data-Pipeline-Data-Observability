from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re

import requests
from tenacity import retry, retry_if_exception_type, retry_if_result, stop_after_attempt, wait_exponential

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records = []
    items = payload.get("message", {}).get("items", [])
    for item in items:
        # 1. paper_id (DOI)
        doi = item.get("DOI")
        if not doi:
            continue
        
        # 2. title
        title_list = item.get("title", [])
        title = title_list[0].strip() if title_list else ""
        
        # 3. abstract/summary
        abstract = item.get("abstract", "")
        summary = clean_html(abstract)
        
        # 4. authors
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)
                
        # 5. categories
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""
        
        # 6. dates
        def extract_date(date_obj):
            if not date_obj:
                return ""
            if "date-time" in date_obj:
                return date_obj["date-time"]
            if "date-parts" in date_obj and date_obj["date-parts"]:
                parts = date_obj["date-parts"][0]
                if len(parts) >= 3:
                    return f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
                elif len(parts) >= 2:
                    return f"{parts[0]:04d}-{parts[1]:02d}-01"
                elif len(parts) >= 1:
                    return f"{parts[0]:04d}-01-01"
            return ""

        published = extract_date(item.get("created") or item.get("issued"))
        updated = extract_date(item.get("deposited"))
        
        # 7. urls
        abs_url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break
                
        # 8. comment
        comment = item.get("publisher", "") or item.get("container-title", [""])[0]
        if isinstance(comment, list):
            comment = comment[0] if comment else ""
        
        record = PaperRecord(
            paper_id=doi,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=str(comment)
        )
        records.append(record)
        
    return records


def should_retry_status(res):
    if isinstance(res, requests.Response):
        return res.status_code in [429, 502, 503, 504]
    return False

@retry(
    retry=(retry_if_exception_type(requests.exceptions.RequestException) | retry_if_result(should_retry_status)),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5)
)
def _do_fetch_crossref(url: str, params: dict) -> requests.Response:
    res = requests.get(url, params=params, timeout=10)
    if res.status_code not in [200, 429, 502, 503, 504]:
        res.raise_for_status()
    return res

def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results
    }
    
    response = _do_fetch_crossref(url, params)
    response.raise_for_status()
    payload = response.json()
    
    # Save raw API response
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    # Parse payload
    records = parse_crossref_payload(payload)
    
    # Save parsed records
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)
        
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**d) for d in data]
