const core = require('@actions/core');
const github = require('@actions/github');
const OpenAI = require('openai');

async function run() {
  try {
    const diffContent = core.getInput('diff-content');
    const apiKey = process.env.OPENAI_API_KEY;

    const openai = new OpenAI({ apiKey });

    const prompt = `Please review the following code changes and provide a concise code review:\n${diffContent}`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 1000,
    });

    const review = completion.choices[0].message.content;
    core.setOutput('review-comment', review);

    const octokit = github.getOctokit(process.env.GITHUB_TOKEN);
    await octokit.rest.issues.createComment({
      owner: github.context.repo.owner,
      repo: github.context.repo.repo,
      issue_number: github.context.issue.number,
      body: `## 🤖 OpenAI Code Review\n\n${review}\n\n---\n*Note: Automated review. Verify before implementing.*`,
    });
  } catch (error) {
    core.setFailed(`Error: ${error.message}`);
  }
}

run();
