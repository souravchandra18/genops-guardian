# GenOps Guardian

AI-powered DevOps assistant that analyzes logs, configs, and recent code changes
in GitHub Actions workflows.

## 🚀 Features
- **Real Mode**: Analyzes actual repo configs, logs, and git history.
- **Demo Mode**: Uses placeholder data for testing.
- **Runs directly in GitHub Actions** without Docker.

## 🛠 Setup
1. Create a GitHub repository and add these files.
2. In repo **Settings → Secrets and variables → Actions**, add:
GENOPS_API_KEY=<your OpenAI API key>

3. Trigger the workflow from the Actions tab.

## 📂 Output
- Analysis is shown in workflow logs.
- A text file is saved at `analysis_results/output.txt` in the Actions run.

## 📄 License
This is a novel AI + DevOps pipeline analyzer created by Sourav Chandra.
