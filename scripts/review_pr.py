# Author: Sourav Chandra
import os
import subprocess
import argparse
from openai import OpenAI
from github import Github

def collect_pr_diff():
    """Collects changed files & diffs from the PR."""
    repo_name = os.getenv("GITHUB_REPOSITORY")
    ref = os.getenv("GITHUB_REF")
    ref_parts = ref.split("/")
    if len(ref_parts) < 3 or not ref_parts[2].isdigit():
        raise ValueError(f"Unexpected GITHUB_REF format or missing PR number: {ref}")
    pr_number = ref_parts[2]

    gh_token = os.getenv("GITHUB_TOKEN")
    gh = Github(gh_token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    diff_text = ""
    for file in pr.get_files():
        diff_text += f"\n### File: {file.filename}\n{file.patch}\n"
    return pr.title, pr.body, diff_text, pr

def collect_repo_context(repo_path):
    """Existing logic for repo scanning."""
    context_parts = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.yml', '.yaml', '.json')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    context_parts.append(f"### File: {file}\n{content}")
                except Exception:
                    pass

    try:
        git_log = subprocess.check_output(
            ["git", "-C", repo_path, "log", "-n", "20", "--pretty=oneline"],
            text=True
        )
        context_parts.append(f"### Recent Commits\n{git_log}")
    except Exception as e:
        context_parts.append(f"[Error collecting git log: {e}]")

    try:
        git_diff = subprocess.check_output(
            ["git", "-C", repo_path, "diff", "HEAD~5", "HEAD"],
            text=True
        )
        context_parts.append(f"### Recent Changes (diff)\n{git_diff}")
    except Exception as e:
        context_parts.append(f"[Error collecting git diff: {e}]")

    return "\n\n".join(context_parts)

def run_analysis(mode, repo_path):
    api_key = os.getenv("GENOPS_API_KEY")
    if not api_key:
        raise ValueError("GENOPS_API_KEY environment variable is missing!")

    client = OpenAI(api_key=api_key)

    if mode == "demo":
        context = "This is a simulated CI/CD pipeline log with no real data."
    elif mode == "real":
        context = collect_repo_context(repo_path)
    elif mode == "pr-review":
        title, body, diff, pr = collect_pr_diff()
        context = f"PR Title: {title}\nPR Body: {body}\nDiff:\n{diff}"

        prompt = f"""
You are a senior software engineer reviewing a pull request.
Provide:
1. Bug risks
2. Security issues
3. Code quality improvements
4. Maintainability suggestions
---
{context}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        review_comment = response.choices[0].message.content
        pr.create_issue_comment(f"### AI PR Review\n{review_comment}")
        return review_comment
    else:
        raise ValueError("Invalid mode provided.")

    prompt = f"""
You are GenOps Guardian — an AI DevOps assistant.
Analyze the following repo data and provide:
1. Potential pipeline failures
2. Security issues
3. Optimization suggestions
---
{context}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="Mode: real, demo, or pr-review")
    parser.add_argument("--repo", required=False, default=".", help="Path to repo")
    args = parser.parse_args()

    print(f"Running GenOps Guardian in {args.mode} mode...")
    result = run_analysis(args.mode, args.repo)

    if args.mode != "pr-review":
        os.makedirs("analysis_results", exist_ok=True)
        with open("analysis_results/output.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print("\n Analysis Result:\n", result)
