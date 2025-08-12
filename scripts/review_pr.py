import os
import subprocess
import argparse
import yaml
import json
from openai import OpenAI

def collect_repo_context(repo_path):
    """Collects logs, configs, and recent git changes from the repository."""
    context_parts = []

    # 1. Collect CI/CD configs and YAMLs
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.yml', '.yaml', '.json')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    context_parts.append(f"### File: {file}\n{content}")
                except Exception:
                    pass

    # 2. Collect last 20 commits
    try:
        git_log = subprocess.check_output(
            ["git", "-C", repo_path, "log", "-n", "20", "--pretty=oneline"],
            text=True
        )
        context_parts.append(f"### Recent Commits\n{git_log}")
    except Exception as e:
        context_parts.append(f"[Error collecting git log: {e}]")

    # 3. Collect git diff for recent commits
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
    """Runs AI-powered analysis based on mode."""
    api_key = os.getenv("GENOPS_API_KEY")
    if not api_key:
        raise ValueError("GENOPS_API_KEY environment variable is missing!")

    client = OpenAI(api_key=api_key)

    if mode == "demo":
        context = "This is a simulated CI/CD pipeline log with no real data."
    elif mode == "real":
        context = collect_repo_context(repo_path)
    else:
        raise ValueError("Mode must be 'real' or 'demo'.")

    prompt = f"""
    You are GenOps Guardian — an AI DevOps assistant.
    Analyze the following repo data and provide:
    1. Potential pipeline failures
    2. Security issues
    3. Optimization suggestions
    ---
    {context}
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="Mode: real or demo")
    parser.add_argument("--repo", required=False, default=".", help="Path to repo")
    args = parser.parse_args()

    print("🔍 Running GenOps Guardian...")
    result = run_analysis(args.mode, args.repo)

    print("\n📊 Analysis Result:\n")
    print(result)

    # Save output for GitHub Actions logs
    os.makedirs("analysis_results", exist_ok=True)
    with open("analysis_results/output.txt", "w", encoding="utf-8") as f:
        f.write(result)
