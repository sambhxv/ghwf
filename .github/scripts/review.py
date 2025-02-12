import os
import sys
import json
import requests
import openai

def get_pr_diff(owner, repo, pr_number, github_token):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"token {github_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: Failed to fetch PR diff (HTTP {response.status_code}).", file=sys.stderr)
        sys.exit(1)
    return response.text

def get_code_review(diff_text, openai_api_key):
    openai.api_key = openai_api_key
    messages = [
        {
            "role": "system",
            "content": (
                """
                You are a code review assistant specializing in defensive programming and error handling. When reviewing code:
                1. Analyze for potential runtime failures and edge cases, particularly focusing on:
                   - External API calls and network operations
                   - Data parsing and serialization
                   - File operations
                   - Resource cleanup
                   - Input validation
                   - Type safety
                   - Null/undefined checks
                
                2. For each identified risk:
                   - Explain the potential failure scenario in a short and consice manner.
                   - Suggest specific error handling improvements (e.g., try-catch blocks, error boundaries, fallback behaviors)
                   - Recommend logging and monitoring where appropriate
                
                3. Suggest test cases ONLY for:
                   - New or modified business logic
                   - Error handling paths
                   - Edge cases that could lead to failures
                   - Integration points with external systems
                
                4. Keep feedback concise and actionable, prioritizing:
                   - Critical reliability issues
                   - Security vulnerabilities 
                   - Performance bottlenecks
                   - Maintainability concerns
                Please review the following code changes with these criteria in mind:
                """
            )
        },
        {"role": "user", "content": diff_text}
    ]
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=5000,
            temperature=0.2
        )
    except Exception as e:
        print(f"Error calling OpenAI API: {e}", file=sys.stderr)
        sys.exit(1)
    return response.choices[0].message.content.strip()

def main():
    github_event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not github_event_path:
        print("Error: GITHUB_EVENT_PATH not set.", file=sys.stderr)
        sys.exit(1)
    with open(github_event_path, 'r') as f:
        event_data = json.load(f)

    pr = event_data.get("pull_request")
    if not pr:
        print("Error: This event is not a pull_request.", file=sys.stderr)
        sys.exit(1)
    pr_number = pr.get("number")
    if not pr_number:
        print("Error: Could not determine pull request number.", file=sys.stderr)
        sys.exit(1)

    repo_full = os.environ.get("GITHUB_REPOSITORY")
    if not repo_full or "/" not in repo_full:
        print("Error: GITHUB_REPOSITORY not set or invalid.", file=sys.stderr)
        sys.exit(1)
    owner, repo = repo_full.split("/")

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN not set.", file=sys.stderr)
        sys.exit(1)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching diff for PR #{pr_number} in {owner}/{repo}...", file=sys.stderr)
    diff_text = get_pr_diff(owner, repo, pr_number, github_token)
    if not diff_text:
        print("Error: No diff fetched.", file=sys.stderr)
        sys.exit(1)

    print("Sending diff to OpenAI for code review...", file=sys.stderr)
    review = get_code_review(diff_text, openai_api_key)

    print(review)

if __name__ == "__main__":
    main()
