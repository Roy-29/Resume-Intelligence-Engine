"""
GitHub Profile Analyzer Service
================================
Fetches public GitHub profile data with NO API key required.
Free tier: 60 requests/hour per IP.
"""
import urllib.request
import urllib.error
import json

GITHUB_API = "https://api.github.com"

# Map GitHub language names → our internal TECHNICAL_SKILLS keys
LANG_TO_SKILL = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Java": "java",
    "C++": "c++",
    "C#": "c#",
    "C": "c",
    "Go": "golang",
    "Ruby": "ruby",
    "Rust": "rust",
    "Swift": "swift",
    "Kotlin": "kotlin",
    "Scala": "scala",
    "R": "r",
    "PHP": "php",
    "Dart": "dart",
    "Shell": "bash",
    "HTML": "html",
    "CSS": "css",
    "Dockerfile": "docker",
    "HCL": "terraform",
    "Jupyter Notebook": "python",
}


def _get(url: str) -> dict | list | None:
    """Make a simple GET request to GitHub API."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RecruiterPro-ATS/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "User not found. Please check the GitHub username."}
        if e.code == 403:
            return {"error": "GitHub API rate limit reached. Please try again in 1 hour."}
        return {"error": f"GitHub API error: {e.code}"}
    except Exception as e:
        return {"error": f"Could not connect to GitHub: {str(e)}"}


def fetch_github_profile(username: str) -> dict:
    """
    Main entry point. Returns structured profile data for a public GitHub user.
    """
    username = username.strip().lstrip("@")

    # 1. Fetch user profile
    user_data = _get(f"{GITHUB_API}/users/{username}")
    if not user_data or "error" in user_data:
        return user_data or {"error": "Failed to fetch profile."}

    # 2. Fetch repos (sorted by stars, max 100)
    repos_data = _get(f"{GITHUB_API}/users/{username}/repos?sort=stars&per_page=30&type=public")
    if not repos_data or isinstance(repos_data, dict):
        repos_data = []

    # 3. Aggregate languages across top repos
    language_counts = {}
    top_repos = []

    for repo in repos_data:
        # Collect language
        lang = repo.get("language")
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

        # Build top repo list (top 5 by stars)
        top_repos.append({
            "name": repo.get("name", ""),
            "description": repo.get("description") or "No description provided.",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language") or "N/A",
            "url": repo.get("html_url", ""),
            "topics": repo.get("topics", []),
        })

    # Sort repos by stars
    top_repos = sorted(top_repos, key=lambda r: r["stars"], reverse=True)[:5]

    # 4. Calculate language distribution (percentage)
    total_lang_uses = sum(language_counts.values()) or 1
    languages = [
        {
            "name": lang,
            "count": count,
            "percent": round((count / total_lang_uses) * 100, 1),
            "skill_key": LANG_TO_SKILL.get(lang, lang.lower()),
        }
        for lang, count in sorted(language_counts.items(), key=lambda x: -x[1])
    ][:8]  # top 8 languages

    # 5. Extract inferred skills (mapped from languages)
    from candidate.data import TECHNICAL_SKILLS
    extracted_skills = []
    for lang_entry in languages:
        skill = lang_entry["skill_key"]
        if skill in TECHNICAL_SKILLS:
            extracted_skills.append(skill)
    # Also add "git" and "github" since they have a GH profile
    for bonus_skill in ["git", "github"]:
        if bonus_skill not in extracted_skills:
            extracted_skills.append(bonus_skill)

    # 6. Calculate an "Activity Score" (0-100) for ATS boost estimate
    public_repos = user_data.get("public_repos", 0)
    total_stars = sum(r["stars"] for r in top_repos)
    followers = user_data.get("followers", 0)
    activity_score = min(100, (public_repos * 2) + (total_stars * 3) + (followers * 1))
    activity_score = round(activity_score)

    return {
        "username": user_data.get("login", username),
        "name": user_data.get("name") or username,
        "bio": user_data.get("bio") or "No bio provided.",
        "avatar_url": user_data.get("avatar_url", ""),
        "profile_url": user_data.get("html_url", f"https://github.com/{username}"),
        "public_repos": public_repos,
        "followers": followers,
        "following": user_data.get("following", 0),
        "total_stars": total_stars,
        "location": user_data.get("location") or "",
        "blog": user_data.get("blog") or "",
        "company": user_data.get("company") or "",
        "languages": languages,
        "top_repos": top_repos,
        "extracted_skills": extracted_skills,
        "activity_score": activity_score,
    }
