#!/usr/bin/env python3
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
                "You are a code review assistant. Provide a detailed and critical review "
                "of the following pull request diff. Point out potential issues, pitfalls, "
                "and offer improvement suggestions where applicable."
            )
        },
        {"role": "user", "content": diff_text}
    ]
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1024,
            temperature=0.2
        )
    except Exception as e:
        print(f"Error calling OpenAI API: {e}", file=sys.stderr)
        sys.exit(1)
    return response.choices[0].message.content.strip()

def post_pr_comment(owner, repo, pr_number, comment, github_token):
    """
    Posts a comment to the pull request using the provided GitHub token.
    When using the default GITHUB_TOKEN provided by GitHub Actions,
    the comment will appear as posted by github-actions[bot].
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"body": comment}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 201:
        print(f"Error posting comment: HTTP {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()

def main():
    # Ensure required environment variables are present.
    github_event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not github_event_path:
        print("Error: GITHUB_EVENT_PATH not set.", file=sys.stderr)
        sys.exit(1)
    with open(github_event_path, 'r') as f:
        event_data = json.load(f)

    # Extract pull request data from the event payload.
    pr = event_data.get("pull_request")
    if not pr:
        print("Error: This event is not a pull_request.", file=sys.stderr)
        sys.exit(1)
    pr_number = pr.get("number")
    if not pr_number:
        print("Error: Could not determine pull request number.", file=sys.stderr)
        sys.exit(1)

    # Extract repository information.
    repo_full = os.environ.get("GITHUB_REPOSITORY")
    if not repo_full or "/" not in repo_full:
        print("Error: GITHUB_REPOSITORY not set or invalid.", file=sys.stderr)
        sys.exit(1)
    owner, repo = repo_full.split("/")

    # Get authentication tokens.
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN not set.", file=sys.stderr)
        sys.exit(1)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching diff for PR #{pr_number} in {owner}/{repo}...")
    diff_text = get_pr_diff(owner, repo, pr_number, github_token)
    if not diff_text:
        print("Error: No diff fetched.", file=sys.stderr)
        sys.exit(1)

    print("Sending diff to OpenAI for code review...")
    review = get_code_review(diff_text, openai_api_key)

    # Post the review as a comment on the pull request.
    print("Posting code review as a comment on the PR (using github-actions bot)...")
    post_pr_comment(owner, repo, pr_number, review, github_token)
    print("Comment posted successfully!")

if __name__ == "__main__":
    main()
