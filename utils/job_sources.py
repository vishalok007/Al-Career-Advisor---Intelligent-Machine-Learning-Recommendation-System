from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import os
import re
from typing import Iterable
from urllib.parse import urlencode, quote_plus
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; AI-Career-Advisor/3.0; +https://github.com/)"

@dataclass
class JobPosting:
    source: str
    source_key: str
    job_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    tags: list[str]
    employment_type: str = ""
    published_at: str = ""
    salary: str = ""
    # First-class fields so the UI can always show company name + apply link.
    apply_url: str = ""
    company_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class JobProvider:
    name = "Provider"
    key = "provider"

    def is_enabled(self) -> bool:
        return True

    def status_note(self) -> str:
        return "Ready"

    def fetch_jobs(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        raise NotImplementedError


def _http_json(url: str, headers: dict | None = None) -> dict:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            **(headers or {}),
        },
    )
    with urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _query_tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#.]+", (text or "").lower()) if len(t) > 2]


def _relevance_score(query: str, job: JobPosting) -> float:
    tokens = _query_tokens(query)
    if not tokens:
        return 0.0
    haystack = " ".join([
        job.title or "",
        job.company or "",
        job.location or "",
        " ".join(job.tags or []),
        job.description or "",
    ]).lower()
    title_low = (job.title or "").lower()

    score = 0.0
    exact_phrase = (query or "").strip().lower()
    if exact_phrase and exact_phrase in title_low:
        score += 6.0
    elif exact_phrase and exact_phrase in haystack:
        score += 3.5

    for token in tokens:
        if token in title_low:
            score += 2.0
        elif token in haystack:
            score += 0.8

    # Prefer postings whose title reflects the search intent.
    matched_title_tokens = sum(1 for token in tokens if token in title_low)
    if matched_title_tokens:
        score += matched_title_tokens * 1.2
    return score


def _normalize_url(url: str, base_domain: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return base_domain.rstrip("/") + url
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url


def _slug(value: str) -> str:
    """Provider-level URL fallback builder. Returns a search-by-company URL on
    the provider's site so the Company link is never a dead ``#``."""
    value = (value or "").strip().lower()
    if not value:
        return ""
    safe = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return safe


def _firma_company_page(provider_key: str, company: str) -> str:
    """Return a reliable Google search link for the company to avoid 404 errors."""
    company = (company or "").strip()
    if not company:
        return ""
    q = quote_plus(f"{company} company")
    return f"https://www.google.com/search?q={q}"

class RemotiveProvider(JobProvider):
    name = "Remotive"
    key = "remotive"

    def status_note(self) -> str:
        return "Live public API — no key required"

    def fetch_jobs(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        params = {"search": query}
        url = f"https://remotive.com/api/remote-jobs?{urlencode(params)}"
        payload = _http_json(url)
        jobs: list[JobPosting] = []
        raw_jobs = payload.get("jobs", [])[: max(limit * 8, 40)]
        for item in raw_jobs:
            apply_url = (item.get("url") or "").strip()
            company = (item.get("company_name") or "").strip()
            slug = _slug(company)
            company_url = f"https://remotive.com/companies/{slug}" if slug else ""
            jobs.append(
                JobPosting(
                    source=self.name,
                    source_key=self.key,
                    job_id=str(item.get("id", "")),
                    title=(item.get("title") or "").strip(),
                    company=company,
                    location=(item.get("candidate_required_location") or "Remote").strip(),
                    url=apply_url,
                    description=item.get("description") or "",
                    tags=[str(t).strip() for t in (item.get("tags") or []) if str(t).strip()],
                    employment_type=(item.get("job_type") or "").strip(),
                    published_at=(item.get("publication_date") or "").strip(),
                    salary=(item.get("salary") or "").strip(),
                    apply_url=apply_url,
                    company_url=company_url,
                )
            )
        jobs.sort(key=lambda job: _relevance_score(query, job), reverse=True)
        filtered = [job for job in jobs if _relevance_score(query, job) > 0]
        return (filtered or jobs)[:limit]


class ArbeitnowProvider(JobProvider):
    """Arbeitnow free public board — no key, instant signup not required.

    Docs: https://www.arbeitnow.com/api/job-board-api
    """
    name = "Arbeitnow"
    key = "arbeitnow"

    def status_note(self) -> str:
        return "Live public API — no key required"

    def fetch_jobs(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        url = "https://www.arbeitnow.com/api/job-board-api"
        payload = _http_json(url)
        jobs: list[JobPosting] = []
        # Each posting URL already contains /jobs/companies/<slug>/... so we
        # can split out the company landing page as the Company → link.
        for item in (payload.get("data") or [])[: max(limit * 6, 60)]:
            title = (item.get("title") or "").strip()
            company = (item.get("company_name") or "").strip()
            apply_url = (item.get("url") or "").strip()
            slug = _slug(company)
            company_url = f"https://www.arbeitnow.com/jobs/companies/{slug}" if slug else ""
            haystack = f"{title} {' '.join(item.get('tags') or [])}".lower()
            if query and query.lower() not in haystack and _slug(query) not in _slug(haystack):
                continue
            if location and location.lower() not in (item.get("location") or "").lower():
                continue
            jobs.append(
                JobPosting(
                    source=self.name,
                    source_key=self.key,
                    job_id=str(item.get("slug") or item.get("id") or ""),
                    title=title,
                    company=company,
                    location=(item.get("location") or "Europe / Remote").strip(),
                    url=apply_url,
                    description=item.get("description") or "",
                    tags=[str(t).strip() for t in (item.get("tags") or []) if str(t).strip()],
                    employment_type="",
                    published_at="",
                    salary="",
                    apply_url=apply_url,
                    company_url=company_url,
                )
            )
        jobs.sort(key=lambda job: _relevance_score(query, job), reverse=True)
        return jobs[:limit]


class RemoteOKProvider(JobProvider):
    """RemoteOK public feed — no key, instant access.

    Docs: https://remoteok.com/api
    """
    name = "RemoteOK"
    key = "remoteok"

    def status_note(self) -> str:
        return "Live public API — no key required"

    def fetch_jobs(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        url = "https://remoteok.com/api"
        try:
            payload = _http_json(url)
        except Exception:
            return []
        if not isinstance(payload, list):
            return []
        jobs: list[JobPosting] = []
        # RemoteOK's first record is a legal/disclaimer object — skip it.
        for item in payload[1:][: max(limit * 6, 60)]:
            title = (item.get("position") or "").strip()
            company = (item.get("company") or "").strip()
            apply_url = (item.get("apply_url") or item.get("url") or "").strip()
            slug = item.get("slug") or _slug(title)
            work_url = f"https://remoteok.com/remote-jobs/{slug}" if slug else ""
            company_url = f"https://remoteok.com/remote-companies/{_slug(company)}" if company else ""
            haystack = f"{title} {' '.join(item.get('tags') or [])}".lower()
            if query and query.lower() not in haystack and _slug(query) not in _slug(haystack):
                continue
            if location and location.lower() not in (item.get("location") or "").lower():
                continue
            jobs.append(
                JobPosting(
                    source=self.name,
                    source_key=self.key,
                    job_id=str(item.get("id") or slug or ""),
                    title=title,
                    company=company,
                    location=(item.get("location") or "Worldwide").strip(),
                    url=work_url or apply_url,
                    description=item.get("description") or "",
                    tags=[str(t).strip() for t in (item.get("tags") or []) if str(t).strip()],
                    employment_type="",
                    published_at=(item.get("date") or "").strip(),
                    salary=_r_ok_salary(item),
                    apply_url=apply_url or work_url,
                    company_url=company_url,
                )
            )
        jobs.sort(key=lambda job: _relevance_score(query, job), reverse=True)
        return jobs[:limit]


class TheMuseProvider(JobProvider):
    """The Muse public jobs API — no key required for a reasonable number of
    lookups, signup-free.

    Docs: https://www.themuse.com/developers/api/v2
    """
    name = "The Muse"
    key = "themuse"

    def status_note(self) -> str:
        return "Live public API — no key required"

    def fetch_jobs(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        params = {"page": 1, "category": "Software Engineering"}
        if query:
            params["keyword"] = query
        url = f"https://www.themuse.com/api/public/jobs?{urlencode(params)}"
        try:
            payload = _http_json(url)
        except Exception:
            return []
        jobs: list[JobPosting] = []
        for item in (payload.get("results") or [])[: max(limit * 4, 40)]:
            refs = item.get("refs") or {}
            apply_url = (refs.get("landing_page") or "").strip()
            company_block = item.get("company") or {}
            company = (company_block.get("name") or "").strip()
            locations = item.get("locations") or []
            loc = ", ".join(locations) if isinstance(locations, list) else str(locations)
            categories = item.get("categories") or []
            tags = [c.get("name") or "" for c in categories if isinstance(c, dict)]
            short = company_block.get("short_name") or ""
            company_url = f"https://www.themuse.com/companies/{short}" if short else _firma_company_page(self.key, company)
            short_name = company_block.get("short_name") or _slug(company)
            company_url = (
                f"https://www.themuse.com/jobs/{short_name}"
                if short_name and "jobs" not in company_url
                else company_url
            )
            jobs.append(
                JobPosting(
                    source=self.name,
                    source_key=self.key,
                    job_id=str(item.get("id") or ""),
                    title=(item.get("name") or "").strip(),
                    company=company,
                    location=loc.strip(", ") or "United States",
                    url=apply_url,
                    description=item.get("contents") or "",
                    tags=[t.strip() for t in tags if t.strip()],
                    employment_type=(item.get("type") or "").strip(),
                    published_at=(item.get("publication_date") or "").strip(),
                    salary="",
                    apply_url=apply_url,
                    company_url=company_url,
                )
            )
        jobs.sort(key=lambda job: _relevance_score(query, job), reverse=True)
        return jobs[:limit]


class USAJobsProvider(JobProvider):
    """USAJOBS — the official U.S. federal-government job board.

    Free, **no paid review queue**. Sign-up takes ~2 min and the API key is
    emailed to you instantly:

        https://developer.usajobs.gov/APIRequest/Access  ← *exact signup URL*

    Set the environment variable::

        export USAJOBS_API_KEY="<the key they email you>"

    … and restart the Streamlit app — the USAJOBS feed then shows up in the
    provider strip with status *Live*.
    """
    name = "USAJOBS"
    key = "usajobs"

    def __init__(self):
        self.api_key = os.getenv("USAJOBS_API_KEY", "")

    def is_enabled(self) -> bool:
        return bool(self.api_key.strip())

    def status_note(self) -> str:
        if self.is_enabled():
            return "Live API configured (federal roles)"
        return "Free key from https://developer.usajobs.gov/APIRequest/Access"

    def fetch_jobs(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if not self.is_enabled():
            return []
        params = {"Keyword": query or "technology", "ResultsPerPage": str(min(limit, 25))}
        if location:
            params["LocationName"] = location
        url = f"https://data.usajobs.gov/api/search?{urlencode(params)}"
        try:
            payload = _http_json(url, headers={"Authorization-Key": self.api_key})
        except Exception:
            return []
        items = (payload.get("SearchResult") or {}).get("SearchResultItems") or []
        jobs: list[JobPosting] = []
        for wrap in items[:limit]:
            item = wrap.get("MatchedObjectDescriptor") or {}
            apply_url = (item.get("ApplyURI") or item.get("PositionURI") or "").strip()
            org_block = item.get("OrganizationName") or ""
            company = (org_block if isinstance(org_block, str) and org_block.strip()
                       else (item.get("DepartmentName") or item.get("Agency") or "U.S. Government"))
            company = str(company).strip()
            locations = item.get("PositionLocation") or []
            loc_parts = []
            for li in locations:
                if not isinstance(li, dict):
                    continue
                city = li.get("CityName") or ""
                state = li.get("StateCode") or ""
                country = li.get("CountryCode") or ""
                seg = ", ".join(p for p in [city, state, country] if p)
                if seg:
                    loc_parts.append(seg)
            loc_line = " · ".join(loc_parts) or (item.get("Country") or "United States")
            summaries = (item.get("UserArea") or {}).get("Details") or {}
            jd = summaries.get("JobSummary") or ""
            salary_min = item.get("PositionRemuneration") or []
            salary = ""
            if salary_min and isinstance(salary_min, list) and salary_min:
                first = salary_min[0] or {}
                lo = first.get("MinimumRange") or ""
                hi = first.get("MaximumRange") or ""
                if lo and hi:
                    salary = f"${lo} - ${hi}"
            jobs.append(
                JobPosting(
                    source=self.name,
                    source_key=self.key,
                    job_id=str(item.get("PositionID") or ""),
                    title=(item.get("PositionTitle") or "").strip(),
                    company=company,
                    location=loc_line,
                    url=apply_url,
                    description=jd,
                    tags=[str(t).strip() for t in (summaries.get("Requirements") or []) if str(t).strip()][:5],
                    employment_type=(item.get("PositionSchedule") or [{}])[0].get("Name", "") if item.get("PositionSchedule") else "",
                    published_at=(item.get("PublicationStartDate") or "").strip(),
                    salary=salary,
                    apply_url=apply_url,
                    company_url=_firma_company_page(self.key, company),
                )
            )
        return jobs


def _r_ok_salary(item: dict) -> str:
    lo = item.get("salary_min") or ""
    hi = item.get("salary_max") or ""
    if lo and hi:
        return f"${lo} - ${hi}"
    if lo:
        return f"from ${lo}"
    if hi:
        return f"up to ${hi}"
    return ""


def get_provider_registry() -> list[JobProvider]:
    return [
        RemotiveProvider(),
        ArbeitnowProvider(),
        RemoteOKProvider(),
        TheMuseProvider(),
        USAJobsProvider(),
    ]


def provider_status_rows() -> list[dict]:
    rows = []
    for provider in get_provider_registry():
        live_when = provider.key in {"remotive", "arbeitnow", "remoteok", "themuse"}
        rows.append(
            {
                "Provider": provider.name,
                "Status": "Live" if (provider.is_enabled() or live_when) else "Standby",
                "Notes": provider.status_note(),
            }
        )
    return rows


def fetch_live_jobs(
    role: str,
    skills: Iterable[str],
    location: str = "",
    limit_per_provider: int = 15,
    providers: Iterable[str] | None = None,
) -> list[dict]:
    """Fetch live jobs from every enabled provider and return deduplicated dicts.

    Retrieval strategy:
    - query 1: predicted role only
    - query 2: role + strongest skill
    - query 3: role + first two skills

    This improves recall for providers whose search API is sensitive to long
    keyword strings.
    """
    providers = {p.lower() for p in (providers or [])}
    query_skills = [s.strip() for s in (skills or []) if s and s.strip()][:3]

    query_variants = []
    if role:
        query_variants.append(role.strip())
        query_variants.append(" ".join(role.strip().split()[:2]))
    if role and query_skills:
        query_variants.append(f"{role} {query_skills[0]}")
    if role and len(query_skills) >= 2:
        query_variants.append(f"{role} {' '.join(query_skills[:2])}")
    if query_skills:
        query_variants.append(" ".join(query_skills[:2]))
    if not query_variants:
        query_variants.append("software engineer")

    seen_queries = set()
    query_variants = [q for q in query_variants if q and not (q.lower() in seen_queries or seen_queries.add(q.lower()))]

    out: list[dict] = []
    seen: set[str] = set()
    provider_buckets: dict[str, list[dict]] = {}

    for provider in get_provider_registry():
        if providers and provider.key not in providers:
            continue
        # Four providers are zero-key so they always stay enabled regardless
        # of env-var state. USAJOBS stays off until USAJOBS_API_KEY is set.
        zero_key = provider.key in {"remotive", "arbeitnow", "remoteok", "themuse"}
        if not provider.is_enabled() and not zero_key:
            continue
        base_domain = "https://remotive.com"
        if provider.key == "arbeitnow": base_domain = "https://www.arbeitnow.com"
        elif provider.key == "remoteok": base_domain = "https://remoteok.com"
        elif provider.key == "themuse": base_domain = "https://www.themuse.com"
        elif provider.key == "usajobs": base_domain = "https://www.usajobs.gov"

        for query in query_variants:
            try:
                jobs = provider.fetch_jobs(query=query, location=location, limit=max(6, limit_per_provider))
            except Exception:
                jobs = []
            for job in jobs:
                job.url = _normalize_url(job.url, base_domain)
                job.apply_url = _normalize_url(job.apply_url or job.url, base_domain)
                job.company_url = _normalize_url(job.company_url, base_domain)

                if not job.company_url or "remotive.com/companies" in job.company_url:
                    job.company_url = _firma_company_page(provider.key, job.company)
                if not job.apply_url and job.url:
                    job.apply_url = job.url
                if not job.url and job.apply_url:
                    job.url = job.apply_url

                key = (job.apply_url or job.url or f"{job.title}|{job.company}|{job.source}").strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                provider_buckets.setdefault(provider.key, []).append(job.to_dict())

    # Round-robin interleave results from all active providers
    max_len = max((len(b) for b in provider_buckets.values()), default=0)
    for i in range(max_len):
        for p_key, bucket in provider_buckets.items():
            if i < len(bucket):
                out.append(bucket[i])
    return out
