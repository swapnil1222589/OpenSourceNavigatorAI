import math
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.schemas.issue import IssueItem, IssueLabel, IssueSearchResponse


class GitHubClient:
    """Client for interacting with the GitHub REST API with caching, repository structure discovery, and rate limit handling."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = settings.GITHUB_API_BASE_URL.rstrip("/")
        # In-memory query cache: {query_key: (timestamp, IssueSearchResponse)}
        self._cache: Dict[str, Tuple[float, IssueSearchResponse]] = {}
        # In-memory repo context cache: {repo_name: (timestamp, dict)}
        self._repo_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
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
        repo: Optional[str] = None,
    ) -> str:
        """Construct a valid GitHub issue search query with qualifiers, strictly excluding pull requests."""
        parts = ["is:issue", "state:open"]

        clean_query = query.strip()
        if clean_query:
            parts.append(clean_query)

        if repo and repo.strip():
            # Validate repo format owner/name
            clean_repo = repo.strip().replace("https://github.com/", "").rstrip("/")
            if "/" in clean_repo:
                parts.append(f"repo:{clean_repo}")

        if language and language.strip():
            parts.append(f"language:{language.strip()}")

        if label and label.strip():
            lbl = label.strip()
            if " " in lbl and not lbl.startswith('"'):
                parts.append(f'label:"{lbl}"')
            else:
                parts.append(f"label:{lbl}")

        return " ".join(parts)

    def _parse_issue(self, raw: dict) -> IssueItem:
        """Transform raw GitHub issue dictionary into an IssueItem."""
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
        repo: Optional[str] = None,
        page: int = 1,
        per_page: int = 15,
        sort: str = "updated",
    ) -> IssueSearchResponse:
        """Search issues via GitHub API with rate limit detection, pagination, and caching."""
        page = max(1, page)
        per_page = max(1, min(per_page, 50))
        q = self.build_query(query=query, language=language, label=label, repo=repo)

        cache_key = f"{q}:{page}:{per_page}:{sort}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            ts, cached_resp = self._cache[cache_key]
            if now - ts < self.cache_ttl:
                return cached_resp

        params = {
            "q": q,
            "page": page,
            "per_page": per_page,
            "sort": sort,
            "order": "desc",
        }

        url = f"{self.base_url}/search/issues"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=self._get_headers(), params=params)

                # Check rate limit headers
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
                        page=page,
                        per_page=per_page,
                        total_pages=0,
                        rate_limited=True,
                        rate_limit_reset=rate_limit_reset,
                        message=msg,
                    )

                if res.status_code != 200:
                    error_msg = f"GitHub API error (HTTP {res.status_code}): {res.text}"
                    return IssueSearchResponse(
                        total_count=0,
                        items=[],
                        page=page,
                        per_page=per_page,
                        total_pages=0,
                        rate_limited=False,
                        message=error_msg,
                    )

                data = res.json()
                raw_items = data.get("items", [])

                # Explicitly exclude pull requests
                issues = [
                    self._parse_issue(item)
                    for item in raw_items
                    if "pull_request" not in item
                ]

                total_count = data.get("total_count", len(issues))
                total_pages = max(1, math.ceil(total_count / per_page)) if total_count > 0 else 1

                response = IssueSearchResponse(
                    total_count=total_count,
                    items=issues,
                    page=page,
                    per_page=per_page,
                    total_pages=total_pages,
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
                page=page,
                per_page=per_page,
                total_pages=0,
                rate_limited=False,
                message="GitHub API request timed out. Please check your network connection and try again.",
            )
        except Exception as e:
            return IssueSearchResponse(
                total_count=0,
                items=[],
                page=page,
                per_page=per_page,
                total_pages=0,
                rate_limited=False,
                message=f"Network error communicating with GitHub API: {str(e)}",
            )

    async def get_repo_context(self, repo_name: str) -> Dict[str, Any]:
        """Fetch verified repository layout and contributing guidelines from GitHub API."""
        clean_repo = repo_name.strip().replace("https://github.com/", "").strip("/")
        if "/" not in clean_repo:
            return {"verified_files": [], "contributing_found": False}

        now = time.time()
        if clean_repo in self._repo_cache:
            ts, cached_ctx = self._repo_cache[clean_repo]
            if now - ts < 300:  # 5 min cache
                return cached_ctx

        url = f"{self.base_url}/repos/{clean_repo}/contents"
        context: Dict[str, Any] = {
            "verified_files": [],
            "items": [],
            "first_file": None,
            "contributing_found": False,
            "contributing_url": None,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    contents = res.json()
                    if isinstance(contents, list):
                        names = [item.get("name", "") for item in contents if isinstance(item, dict) and "name" in item]
                        context["verified_files"] = names[:50]

                        items_meta = []
                        first_file_found = None
                        for item in contents:
                            if not isinstance(item, dict):
                                continue
                            name = item.get("name", "")
                            itype = item.get("type", "file")
                            path = item.get("path", name)
                            items_meta.append({
                                "name": name,
                                "type": itype,
                                "path": path,
                                "size": item.get("size", 0),
                            })
                            if itype == "file" and not first_file_found:
                                # Prioritize README or main files
                                if name.lower().startswith("readme") or not first_file_found:
                                    first_file_found = path

                            if "contributing" in name.lower():
                                context["contributing_found"] = True
                                context["contributing_url"] = item.get("html_url")

                        context["items"] = items_meta
                        context["first_file"] = first_file_found

            self._repo_cache[clean_repo] = (now, context)
            return context
        except Exception:
            return context

    async def get_file_content(self, repo_name: str, path: str) -> Dict[str, Any]:
        """Safely fetch and decode content of a specific file or directory listing from GitHub with strict size bounds."""
        import base64

        clean_repo = repo_name.strip().replace("https://github.com/", "").strip("/")
        clean_path = path.strip().lstrip("/")

        url = f"{self.base_url}/repos/{clean_repo}/contents/{clean_path}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 404:
                    return {"found": False, "error": f"Path '{clean_path}' not found in repository."}
                if res.status_code != 200:
                    return {"found": False, "error": f"GitHub returned HTTP {res.status_code}."}

                data = res.json()

                # Handle directory listings
                if isinstance(data, list):
                    entries = [
                        f"- {'📁' if item.get('type') == 'dir' else '📄'} `{item.get('name')}` ({item.get('type')})"
                        for item in data
                        if isinstance(item, dict)
                    ]
                    listing = f"# Directory: `{clean_path}`\n\nContains {len(entries)} items:\n\n" + "\n".join(entries)
                    return {
                        "found": True,
                        "path": clean_path,
                        "is_directory": True,
                        "size": len(data),
                        "size_bytes": len(data),
                        "html_url": f"https://github.com/{clean_repo}/tree/main/{clean_path}",
                        "truncated": False,
                        "is_truncated": False,
                        "content": listing,
                    }

                if data.get("type") != "file":
                    return {"found": False, "error": f"Path '{clean_path}' is not a readable file."}

                size = data.get("size", 0)
                if size > 100 * 1024:  # 100 KB limit
                    return {
                        "found": True,
                        "path": clean_path,
                        "is_directory": False,
                        "size": size,
                        "size_bytes": size,
                        "html_url": data.get("html_url"),
                        "truncated": True,
                        "is_truncated": True,
                        "content": "(File exceeds 100KB safe preview limit. Inspect directly on GitHub.)",
                    }

                raw_b64 = data.get("content", "")
                decoded_bytes = base64.b64decode(raw_b64)
                try:
                    text_content = decoded_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = "(Binary file content cannot be displayed as text.)"

                return {
                    "found": True,
                    "path": clean_path,
                    "is_directory": False,
                    "size": size,
                    "size_bytes": size,
                    "html_url": data.get("html_url"),
                    "truncated": False,
                    "is_truncated": False,
                    "content": text_content[:50000],  # Bound to 50KB text
                }
        except Exception as e:
            return {"found": False, "error": f"Network error reading file: {str(e)}"}
