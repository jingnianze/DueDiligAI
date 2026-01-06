import requests
import os
from datetime import datetime, timezone
from dateutil.parser import parse
from requests.exceptions import RequestException, HTTPError

def github_get(url, token, params=None, timeout=10):
    """Wrapper for GitHub API GET requests with timeout and rate limit handling"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"  
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except HTTPError as e:
        if r.status_code == 403 and "rate limit" in r.text.lower():
            raise Exception(f"GitHub API rate limit exceeded! Reset time: {r.headers.get('X-RateLimit-Reset')}") from e
        elif r.status_code == 404:
            raise Exception(f"Resource not found: {url}") from e
        elif r.status_code == 401:
            raise Exception("Token authentication failed. Please check token validity.") from e
        else:
            raise Exception(f"HTTP request failed: {e}") from e
    except RequestException as e:
        raise Exception(f"Network request error: {e}") from e

def parse_github_url(url: str):
    """Parse GitHub repository URL with validity checks"""
    url = url.rstrip("/")
    if not url.startswith(("https://github.com/", "http://github.com/")):
        raise ValueError("Only GitHub repository URLs are supported (e.g. https://github.com/owner/repo)")
    
    parts = url.split("/")
    if len(parts) < 5:
        raise ValueError(f"Invalid GitHub repository URL: {url}")
    
    owner, repo = parts[-2], parts[-1]
    if not owner or not repo:
        raise ValueError(f"Failed to parse owner/repo from: {url}")
    return owner, repo

def fetch_repo_info(owner, repo, token):
    """Retrieve basic repository information"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    return github_get(url, token)

def fetch_last_commit_days(owner, repo, token):
    """Get days since last commit, handle empty commit history"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commits = github_get(url, token, params={"per_page": 1})
    
    if not commits:  
        return None
    
    try:
        commit_time_str = commits[0]["commit"]["committer"]["date"]
        commit_time = parse(commit_time_str).astimezone(timezone.utc)  
        now = datetime.now(timezone.utc)
        days_diff = (now - commit_time).days
        return days_diff
    except (KeyError, IndexError) as e:
        raise Exception("Failed to parse commit time. API response format may have changed.") from e
    except Exception as e:
        raise Exception(f"Time parsing error: {e}") from e

def fetch_issue_stats(owner, repo, token):
    """Optimized: Get issue statistics with single search request (reduce API calls)"""
    base = "https://api.github.com/search/issues"
    params = {
        "q": f"repo:{owner}/{repo} is:issue",
        "per_page": 1  # Only need total count, no need for full issue details
    }
    try:
        resp = github_get(base, token, params=params)
        total_issues = resp["total_count"]
        if total_issues == 0:
            return {"open": 0, "closed": 0, "resolution_rate": None}
        open_params = {
            "q": f"repo:{owner}/{repo} is:issue is:open",
            "per_page": 1
        }
        open_resp = github_get(base, token, params=open_params)
        open_issues = open_resp["total_count"]
        closed_issues = total_issues - open_issues
        
        return {
            "open": open_issues,
            "closed": closed_issues,
            "resolution_rate": round(closed_issues / total_issues, 4) if total_issues else None
        }
    except Exception as e:
        raise Exception(f"Failed to retrieve issue statistics: {e}") from e

def analyze_repo(url, token):
    """Main repository analysis function"""
    try:
        owner, repo = parse_github_url(url)
        info = fetch_repo_info(owner, repo, token)
        last_commit_days = fetch_last_commit_days(owner, repo, token)
        issues = fetch_issue_stats(owner, repo, token)
        
        return {
            "repo": f"{owner}/{repo}",
            "stars": info["stargazers_count"],
            "forks": info["forks_count"],
            "last_commit_days_ago": last_commit_days,
            "issues": issues
        }
    except Exception as e:
        raise Exception(f"Repository analysis failed: {e}") from e

def derive_signals(metrics):
    positives = []
    negatives = []

    last_commit_days = metrics.get("last_commit_days_ago", None)
    commit_count = metrics.get("recent_commit_count", None)  
    if last_commit_days is not None:
        if last_commit_days <= 7:
            msg = f"Recent commits within 7 days"
            if commit_count is not None:
                msg += f" ({commit_count} commits)"
            positives.append(msg)
        elif last_commit_days <= 30:
            positives.append(f"Commits within last 30 days")
        else:
            negatives.append(f"No recent commits (last commit {last_commit_days} days ago)")

    issue_rate = metrics.get("issues", {}).get("resolution_rate", None)
    open_issues = metrics.get("issues", {}).get("open", None)
    closed_issues = metrics.get("issues", {}).get("closed", None)

    if issue_rate is not None:
        if issue_rate >= 0.7:
            msg = f"High issue resolution rate ({issue_rate:.0%})"
            if closed_issues is not None and open_issues is not None:
                msg += f" ({closed_issues} closed / {closed_issues + open_issues} total)"
            positives.append(msg)
        else:
            msg = f"Low issue resolution rate ({issue_rate:.0%})"
            if closed_issues is not None and open_issues is not None:
                msg += f" ({closed_issues} closed / {closed_issues + open_issues} total)"
            negatives.append(msg)

    if open_issues is not None:
        if open_issues > 1000:
            negatives.append(f"Large number of open issues ({open_issues})")
        elif open_issues > 500:
            negatives.append(f"Moderate number of open issues ({open_issues})")
        else:
            positives.append(f"Low number of open issues ({open_issues})")

    risk_flags = metrics.get("risk_flags", [])
    for flag in risk_flags:
        negatives.append(f"Risk: {flag}")

    return positives, negatives


def compute_health_score(metrics):

    last_commit_days = metrics.get("last_commit_days_ago", 999)
    if last_commit_days <= 7:
        activity_score = 1.0
    elif last_commit_days <= 30:
        activity_score = 0.7
    elif last_commit_days <= 90:
        activity_score = 0.4
    else:
        activity_score = 0.1


    issue_rate = metrics.get("issues", {}).get("resolution_rate", None)
    if issue_rate is None:
        issue_score = 0.5  
    else:
        issue_score = issue_rate  


    stars = metrics.get("stars", 0)
    forks = metrics.get("forks", 0)
    popularity_score = min(stars / 10000, 1)  


    risk_flags = metrics.get("risk_flags", [])
    risk_score = max(0, 1 - 0.1 * len(risk_flags))  

    total_score = round(
        activity_score * 0.3 +
        issue_score * 0.3 +
        popularity_score * 0.2 +
        risk_score * 0.2, 2
    )

    score_breakdown = {
        "activity": round(activity_score, 2),
        "issue_health": round(issue_score, 2),
        "popularity": round(popularity_score, 2),
        "risk": round(risk_score, 2)
    }

    return total_score, score_breakdown


def verdict_from_score(score):
    if score >= 0.8:
        return "Healthy & Actively Maintained"
    elif score >= 0.5:
        return "Moderate Risk"
    else:
        return "High Maintenance Risk"


def generate_report(metrics):

    positives, negatives = derive_signals(metrics)
    total_score, score_breakdown = compute_health_score(metrics)
    verdict = verdict_from_score(total_score)

    return {
        "score": total_score,
        "score_breakdown": score_breakdown,
        "verdict": verdict,
        "positives": positives,
        "negatives": negatives
    }
def analyze_repo(url, token):
    """主仓库分析函数：对齐代码分析师接口"""
    try:
        owner, repo = parse_github_url(url)
        info = fetch_repo_info(owner, repo, token)
        last_commit_days = fetch_last_commit_days(owner, repo, token)
        issues = fetch_issue_stats(owner, repo, token)
        metrics = {
            "repo": f"{owner}/{repo}",
            "stars": info["stargazers_count"],
            "forks": info["forks_count"],
            "last_commit_days_ago": last_commit_days,
            "issues": issues
        }
        report_data = generate_report(metrics)
        return {
            "metrics": metrics,
            "report": report_data
        }
    except Exception as e:
        raise Exception(f"Repository analysis failed: {e}")

