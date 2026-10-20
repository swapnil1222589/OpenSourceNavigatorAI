import time
from typing import Dict, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.schemas.issue import IssueItem, IssueLabel, IssueSearchResponse


class GitHubClient:
    """Client for interacting with the GitHub REST API with caching and rate limit handling."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = settings.GITHUB_API_BASE_URL.rstrip("/")
        # In-memory query cache: {query_key: (timestamp, IssueSearchResponse)}
        self._cache: Dict[str, Tuple[float, IssueSearchResponse]] = {}
        self.cache_ttl = settings.GITHUB_SEARCH_CACHE_TTL_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenSourceNavigatorAI/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def build_query(
        self,
        query: str = "",
        language: Optional[str] = None,
        label: Optional[str] = None,
    ) -> str:
        """Construct a valid GitHub issue search query with qualifiers, strictly excluding pull requests."""
        parts = ["is:issue", "state:open"]

        clean_query = query.strip()
        if clean_query:
            parts.append(clean_query)

        if language and language.strip():
            parts.append(f"language:{language.strip()}")

        if label and label.strip():
            # If label has spaces, quote it
            lbl = label.strip()
            if " " in lbl and not lbl.startswith('"'):
                parts.append(f'label:"{lbl}"')
            else:
                parts.append(f"label:{lbl}")

        return " ".join(parts)

    def _parse_issue(self, raw: dict) -> IssueItem:
        """Transform raw GitHub issue dictionary into an IssueItem."""
        # Extract repository name from repository_url: "https://api.github.com/repos/owner/name"
        repo_url = raw.get("repository_url", "")
        repo_parts = repo_url.rstrip("/").split("/")
        if len(repo_parts) >= 2:
            repo_name = f"{repo_parts[-2]}/{repo_parts[-1]}"
            repo_html = f"https://github.com/{repo_name}"
        else:
            repo_name = "Unknown Repository"
            repo_html = ""

        labels = [
            IssueLabel(
                name=lbl.get("name", ""),
                color=lbl.get("color", "6b7280"),
                description=lbl.get("description"),
            )
            for lbl in raw.get("labels", [])
            if isinstance(lbl, dict) and "name" in lbl
        ]

        return IssueItem(
            id=raw.get("id", 0),
            number=raw.get("number", 0),
            title=raw.get("title", ""),
            body=raw.get("body") or "",
            html_url=raw.get("html_url", ""),
            state=raw.get("state", "open"),
            created_at=raw.get("created_at", ""),
            updated_at=raw.get("updated_at", ""),
            comments_count=raw.get("comments", 0),
            repository_name=repo_name,
            repository_url=repo_html,
            labels=labels,
        )

    async def search_issues(
        self,
        query: str = "",
        language: Optional[str] = None,
        label: Optional[str] = None,
        per_page: int = 15,
        sort: str = "updated",
    ) -> IssueSearchResponse:
        """Search issues via GitHub API with rate limit detection and brief caching."""
        per_page = max(1, min(per_page, 50))
        q = self.build_query(query=query, language=language, label=label)

        cache_key = f"{q}:{per_page}:{sort}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            ts, cached_resp = self._cache[cache_key]
            if now - ts < self.cache_ttl:
                return cached_resp

        params = {
            "q": q,
            "per_page": per_page,
            "sort": sort,
            "order": "desc",
        }

        url = f"{self.base_url}/search/issues"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=self._get_headers(), params=params)

                # Check rate limit headers
                remaining = res.headers.get("x-ratelimit-remaining")
                reset_ts = res.headers.get("x-ratelimit-reset")
                rate_limit_reset = int(reset_ts) if reset_ts and reset_ts.isdigit() else None

                if res.status_code == 403 or res.status_code == 429:
                    msg = (
                        "GitHub API rate limit exceeded. To increase your rate limit from 60 to 5,000 "
                        "requests per hour, configure a personal access token in backend/.env (GITHUB_TOKEN=your_token)."
                    )
                    return IssueSearchResponse(
                        total_count=0,
                        items=[],
                        rate_limited=True,
                        rate_limit_reset=rate_limit_reset,
                        message=msg,
                    )

                if res.status_code != 200:
                    error_msg = f"GitHub API error (HTTP {res.status_code}): {res.text}"
                    return IssueSearchResponse(
                        total_count=0,
                        items=[],
                        rate_limited=False,
                        message=error_msg,
                    )

                data = res.json()
                raw_items = data.get("items", [])

                # Explicitly exclude pull requests (GitHub search API returns PRs unless filtered)
                issues = [
                    self._parse_issue(item)
                    for item in raw_items
                    if "pull_request" not in item
                ]

                total_count = data.get("total_count", len(issues))
                response = IssueSearchResponse(
                    total_count=total_count,
                    items=issues,
                    rate_limited=False,
                    message=None,
                )

                # Store in cache
                self._cache[cache_key] = (now, response)
                return response

        except httpx.TimeoutException:
            return IssueSearchResponse(
                total_count=0,
                items=[],
                rate_limited=False,
                message="GitHub API request timed out. Please check your network connection and try again.",
            )
        except Exception as e:
            return IssueSearchResponse(
                total_count=0,
                items=[],
                rate_limited=False,
                message=f"Network error communicating with GitHub API: {str(e)}",
            )
