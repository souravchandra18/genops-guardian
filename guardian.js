import { CONFIG } from '../config.js';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export async function runAudit(mode) {
  const openai = new OpenAI({ apiKey: CONFIG.apiKey });

  let context = "";

  if (mode === "real") {
    console.log("Collecting real repo data...");

    try {
      // Get git logs
      const gitLogs = execSync("git log -n 20 --pretty=format:'%h - %an, %ar : %s'", { encoding: "utf-8" });
      context += `\n=== Recent Commits ===\n${gitLogs}\n`;

      // Get git diff stats
      const gitDiff = execSync("git diff --stat HEAD~5 HEAD", { encoding: "utf-8" });
      context += `\n=== Recent Changes ===\n${gitDiff}\n`;

      // Find and read relevant files
      const patterns = [".yml", ".yaml", ".json", ".log", ".txt"];
      const files = fs.readdirSync(process.cwd(), { withFileTypes: true })
        .flatMap(dirent => dirent.isFile() ? [dirent.name] : []);

      for (const file of files) {
        if (patterns.some(ext => file.endsWith(ext))) {
          try {
            const content = fs.readFileSync(file, "utf-8");
            context += `\n=== File: ${file} ===\n${content}\n`;
          } catch {}
        }
      }

      // Trim large context
      if (context.length > CONFIG.maxContextChars) {
        console.warn("⚠ Context too large, trimming...");
        context = context.slice(0, CONFIG.maxContextChars) + "\n...TRIMMED...";
      }
    } catch (err) {
      console.error("Error collecting repo data:", err.message);
    }

  } else {
    console.log("Using demo static context...");
    context = `
      Jenkinsfile shows unencrypted secrets.
      Dockerfile runs as root.
      CloudFormation template has public S3 bucket.
    `;
  }

  // Send to OpenAI for analysis
  console.log(" Sending data to OpenAI for DevOps audit...");
  const response = await openai.chat.completions.create({
    model: CONFIG.model,
    messages: [
      {
        role: "system",
        content: "You are a senior DevOps security auditor. Analyze provided repo data for security risks, CI/CD issues, and give recommendations."
      },
      {
        role: "user",
        content: context
      }
    ]
  });

  console.log("\n GenOps Guardian Report:\n");
  console.log(response.choices[0].message.content);
}
