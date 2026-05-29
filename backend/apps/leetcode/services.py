"""LeetCode integration service layer.

LeetCode does not expose an official public API. We talk to its unofficial
GraphQL endpoint (`leetcode.com/graphql`) which is rate-limited and Cloudflare-
protected. All callers must treat failures as expected and surface them - we
never silently swallow errors here.

Public surface:
    LeetCodeClient          - thin GraphQL client with retries
    fetch_profile_summary   - returns ProfileSummary dataclass
    fetch_recent_solves     - returns a list of RecentSolve dataclasses
    fetch_problem_meta      - returns ProblemMeta dataclass for one slug
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# --- Errors ------------------------------------------------------------


class LeetCodeAPIError(Exception):
    """Raised when LeetCode's API returns a non-recoverable error."""


class LeetCodeRateLimited(LeetCodeAPIError):
    """Raised on 429 / Cloudflare blocks - caller should back off."""


class LeetCodeUserNotFound(LeetCodeAPIError):
    """Raised when the username doesn't resolve to a real LeetCode user."""


# --- DTOs --------------------------------------------------------------


@dataclass(frozen=True)
class ProfileSummary:
    handle: str
    ranking: int | None
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int


@dataclass(frozen=True)
class RecentSolve:
    title_slug: str
    title: str
    solved_at: datetime  # tz-aware UTC


@dataclass(frozen=True)
class ProblemMeta:
    title_slug: str
    title: str
    difficulty: str  # "easy" | "medium" | "hard"
    topic_tags: list[str]
    is_premium: bool
    leetcode_id: int | None


# --- GraphQL queries ---------------------------------------------------

_PROFILE_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile { ranking }
    submitStats {
      acSubmissionNum { difficulty count }
    }
  }
}
"""

_RECENT_SUBMISSIONS_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id title titleSlug timestamp
  }
}
"""

_QUESTION_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId title titleSlug difficulty isPaidOnly
    topicTags { name slug }
  }
}
"""


# --- Client ------------------------------------------------------------


class LeetCodeClient:
    """Thin GraphQL client with exponential-backoff retries.

    Construct one per task / request - it's stateless aside from the session.
    """

    def __init__(self, *, timeout: float = 10.0):
        self.endpoint = settings.LEETCODE_GRAPHQL_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                # LeetCode rejects the default python-requests user-agent.
                "User-Agent": (
                    "Mozilla/5.0 (compatible; GrindMateSync/1.0; " "+https://grindmate.app)"
                ),
                "Referer": "https://leetcode.com",
            }
        )

    @retry(
        retry=retry_if_exception_type(LeetCodeRateLimited),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def query(self, query: str, variables: dict) -> dict:
        try:
            response = self.session.post(
                self.endpoint,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LeetCodeAPIError(f"Network error talking to LeetCode: {exc}") from exc

        if response.status_code in (429, 403):
            raise LeetCodeRateLimited(f"Rate limited (HTTP {response.status_code}).")
        if response.status_code >= 500:
            raise LeetCodeAPIError(f"LeetCode {response.status_code}.")
        if response.status_code != 200:
            raise LeetCodeAPIError(
                f"Unexpected status {response.status_code}: {response.text[:200]}",
            )

        body = response.json()
        if body.get("errors"):
            raise LeetCodeAPIError(f"GraphQL errors: {body['errors']}")
        return body.get("data", {})


# --- High-level helpers ------------------------------------------------


def fetch_profile_summary(handle: str, *, client: LeetCodeClient | None = None) -> ProfileSummary:
    client = client or LeetCodeClient()
    data = client.query(_PROFILE_QUERY, {"username": handle})

    matched = data.get("matchedUser")
    if not matched:
        raise LeetCodeUserNotFound(f"No LeetCode user found for handle {handle!r}.")

    counts = {
        row["difficulty"].lower(): row["count"] for row in matched["submitStats"]["acSubmissionNum"]
    }

    # LeetCode returns an "All" bucket plus easy/medium/hard.
    return ProfileSummary(
        handle=matched["username"],
        ranking=(matched.get("profile") or {}).get("ranking"),
        total_solved=counts.get("all", 0),
        easy_solved=counts.get("easy", 0),
        medium_solved=counts.get("medium", 0),
        hard_solved=counts.get("hard", 0),
    )


def fetch_recent_solves(
    handle: str,
    *,
    limit: int = 50,
    client: LeetCodeClient | None = None,
) -> list[RecentSolve]:
    client = client or LeetCodeClient()
    data = client.query(_RECENT_SUBMISSIONS_QUERY, {"username": handle, "limit": limit})

    rows = data.get("recentAcSubmissionList") or []
    out: list[RecentSolve] = []
    for row in rows:
        # LeetCode returns timestamp as a unix-second string.
        ts = int(row["timestamp"])
        out.append(
            RecentSolve(
                title_slug=row["titleSlug"],
                title=row["title"],
                solved_at=datetime.fromtimestamp(ts, tz=UTC),
            ),
        )
    return out


def fetch_problem_meta(
    title_slug: str,
    *,
    client: LeetCodeClient | None = None,
) -> ProblemMeta:
    client = client or LeetCodeClient()
    data = client.query(_QUESTION_QUERY, {"titleSlug": title_slug})

    q = data.get("question")
    if not q:
        raise LeetCodeAPIError(f"Problem {title_slug!r} not found.")

    leetcode_id = None
    if q.get("questionFrontendId"):
        try:
            leetcode_id = int(q["questionFrontendId"])
        except ValueError:
            leetcode_id = None

    return ProblemMeta(
        title_slug=q["titleSlug"],
        title=q["title"],
        difficulty=(q["difficulty"] or "").lower(),
        topic_tags=[t["slug"] for t in (q.get("topicTags") or [])],
        is_premium=bool(q.get("isPaidOnly")),
        leetcode_id=leetcode_id,
    )
