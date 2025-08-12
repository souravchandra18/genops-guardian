# GenOps Guardian

 GenOps Guardian is an AI-powered automated code review and DevOps analysis tool designed for GitHub repositories, integrated as a GitHub Action. AI-powered DevOps assistant that analyzes logs, configs, and recent code changes
in GitHub Actions workflows.

It leverages:

GitHub Actions to trigger on PRs or manual dispatch.

Python script to collect relevant repo or PR context (configs, commits, diffs).

OpenAI GPT model (gpt-4.1-mini) to analyze the DevOps-related context and generate actionable feedback.

Posts AI-generated insights directly as PR comments, improving developer feedback loops.

## 🚀 Features
- **Real Mode**: Analyzes actual repo configs, logs, and git history.
- **Demo Mode**: Uses placeholder data for testing.
- **PR Mode**: Analyzes the changed files in PR.
- **Runs directly in GitHub Actions** without Docker.
- **AI Driven DevOps Analysis**: Uses OpenAI GPT-4.1-mini model for AI-powered analysis. Unlike typical static linters or manual code review, it uses advanced AI to understand pipeline configurations, recent changes, and give natural language feedback on potential pipeline failures, security issues, and optimization tips.
- **Context-Aware Analysis**: Instead of just code, it analyzes YAML/JSON configs, recent commit logs, diffs — giving a holistic view of changes affecting the DevOps pipeline.

## 🛠 Setup
1. Create a GitHub repository and add these files.
2. In repo **Settings → Secrets and variables → Actions**, add:
GENOPS_API_KEY=<your OpenAI API key>
GITHUB_TOKEN=<your_github_token>

3. Trigger the workflow from the Actions tab.

## 📂 Output
- Analysis is shown in workflow logs.
- A text file is saved at `analysis_results/output.txt` in the Actions run.

## 📄 License
This is a novel AI + DevOps pipeline analyzer created by Sourav Chandra.
