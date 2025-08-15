#Author: Sourav Chandra
import os
import subprocess
import argparse
import json
from openai import OpenAI
from github import Github


def collect_repo_context(repo_path):
    """Collects logs, configs, and recent git changes from the repository."""
    context_parts = []

    # Collect CI/CD configs and YAMLs
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.yml', '.yaml', '.json')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    context_parts.append(f"### File: {file}\n{content}")
                except Exception:
                    pass

    # Last 20 commits
    try:
        git_log = subprocess.check_output(
            ["git", "-C", repo_path, "log", "-n", "20", "--pretty=oneline"],
            text=True
        )
        context_parts.append(f"### Recent Commits\n{git_log}")
    except Exception as e:
        context_parts.append(f"[Error collecting git log: {e}]")

    # Diff of last 5 commits
    try:
        git_diff = subprocess.check_output(
            ["git", "-C", repo_path, "diff", "HEAD~5", "HEAD"],
            text=True
        )
        context_parts.append(f"### Recent Changes (diff)\n{git_diff}")
    except Exception as e:
        context_parts.append(f"[Error collecting git diff: {e}]")

    return "\n\n".join(context_parts)


def collect_pr_context(repo_path, base_sha, head_sha):
    """Collects only changed files and diffs from the PR."""
    context_parts = []

    try:
        # Get list of changed files in PR
        changed_files = subprocess.check_output(
            ["git", "-C", repo_path, "diff", "--name-only", base_sha, head_sha],
            text=True
        ).strip().split("\n")

        context_parts.append(f"### Changed Files\n" + "\n".join(changed_files))

        # Add file contents + diff for each changed file
        for file_path in changed_files:
            if not file_path.strip():
                continue

            file_abs_path = os.path.join(repo_path, file_path)

            # Read file content (if exists)
            if os.path.exists(file_abs_path):
                try:
                    with open(file_abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    context_parts.append(f"### File: {file_path}\n{content}")
                except Exception:
                    context_parts.append(f"[Error reading file: {file_path}]")

            # Get file diff
            try:
                file_diff = subprocess.check_output(
                    ["git", "-C", repo_path, "diff", base_sha, head_sha, "--", file_path],
                    text=True
                )
                context_parts.append(f"### Diff for {file_path}\n{file_diff}")
            except Exception:
                context_parts.append(f"[Error getting diff for: {file_path}]")

        # PR commit messages
        git_log = subprocess.check_output(
            ["git", "-C", repo_path, "log", f"{base_sha}..{head_sha}", "--pretty=oneline"],
            text=True
        )
        context_parts.append(f"### PR Commits\n{git_log}")

    except Exception as e:
        context_parts.append(f"[Error collecting PR context: {e}]")

    return "\n\n".join(context_parts)


def post_pr_comment(pr_number, message):
    """Posts AI analysis as a comment on the PR."""
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")

    if not token or not repo_name:
        print("[Warning] Missing GITHUB_TOKEN or GITHUB_REPOSITORY, skipping PR comment.")
        return

    try:
        gh = Github(token)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))
        pr.create_issue_comment(message)
        print(f"✅ Comment posted to PR #{pr_number}")
    except Exception as e:
        print(f"[Error posting PR comment: {e}]")


def run_analysis(mode, repo_path):
    """Runs AI-powered analysis and calculates risk score."""
    api_key = os.getenv("GENOPS_API_KEY")
    if not api_key:
        raise ValueError("GENOPS_API_KEY environment variable is missing!")

    client = OpenAI(api_key=api_key)

    # Select context
    if mode == "demo":
        context = "This is a simulated CI/CD pipeline log with no real data."
    elif mode == "real":
        context = collect_repo_context(repo_path)
    elif mode == "pr":
        base_sha = os.getenv("BASE_SHA")
        head_sha = os.getenv("HEAD_SHA")
        if not base_sha or not head_sha:
            raise ValueError("BASE_SHA and HEAD_SHA environment variables are required for PR mode.")
        context = collect_pr_context(repo_path, base_sha, head_sha)
    else:
        raise ValueError("Mode must be 'real', 'demo', or 'pr'.")

    # Prompt for structured JSON risk analysis
    prompt = f"""
    You are GenOps Guardian — an AI DevOps assistant.
    Analyze the following repository or PR data and output a JSON object with:
    - "risk_score": integer (0-100, where 100 is most risky)
    - "risk_level": Low / Medium / High
    - "issues": list of detected problems
    - "analysis_text": a short human-readable explanation

    Base your score on:
    1. Potential pipeline failures (weight 30%)
    2. Security issues (weight 40%)
    3. Optimization/code quality suggestions (weight 20%)
    4. Size/complexity of changes (weight 10%)

    ---
    {context}
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0
    )

    try:
        ai_output = response.output_text.strip()
        data = json.loads(ai_output)  # Ensure valid JSON
    except Exception:
        data = {
            "risk_score": 50,
            "risk_level": "Medium",
            "issues": ["AI returned unstructured output"],
            "analysis_text": response.output_text
        }

    # Save risk JSON
    os.makedirs("analysis_results", exist_ok=True)
    with open("analysis_results/risk.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Build final summary
    summary = (
        f"**Risk Score:** {data['risk_score']} ({data['risk_level']})\n\n"
        f"**Detected Issues:**\n" + "\n".join(f"- {i}" for i in data.get("issues", [])) +
        f"\n\n**AI Analysis:**\n{data.get('analysis_text', '')}"
    )

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="Mode: real, demo, or pr")
    parser.add_argument("--repo", required=False, default=".", help="Path to repo")
    args = parser.parse_args()

    print("🔍 Running GenOps Guardian...")
    result = run_analysis(args.mode, args.repo)

    print("\n📊 Analysis Result:\n")
    print(result)

    with open("analysis_results/output.txt", "w", encoding="utf-8") as f:
        f.write(result)

    # Post comment if PR mode
    if args.mode == "pr":
        pr_number = os.getenv("PR_NUMBER")
        if pr_number:
            post_pr_comment(pr_number, result)
