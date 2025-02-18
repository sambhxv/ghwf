import os
import sys
import json
import requests

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

def get_code_review(diff_text, cloud_function_url):
    function_api_key = os.environ.get("FUNCTION_API_KEY")
    if not function_api_key:
        print("function_api_key not found", file=sys.stderr)
        sys.exit(1)
    headers = {
      "Content-Type": "application/json",
      "Authorization": function_api_key
    }
    payload = json.dumps({"diff": diff_text})
    try:
        response = requests.request("POST", cloud_function_url, headers=headers, data=payload)
        if response.status_code != 200:
            print(f"Error: Cloud Function returned HTTP {response.status_code}: {response.text}", file=sys.stderr)
            sys.exit(1)
        return response.json().get("review", "No review received.")
    
    except Exception as e:
        print(f"Error calling Cloud Function: {e}", file=sys.stderr)
        sys.exit(1)

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

    cloud_function_url = os.environ.get("CLOUD_FUNCTION_URL")
    print(cloud_function_url, file=sys.stderr)
    if not cloud_function_url:
        print("Error: CLOUD_FUNCTION_URL not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching diff for PR #{pr_number} in {owner}/{repo}...", file=sys.stderr)
    diff_text = get_pr_diff(owner, repo, pr_number, github_token)
    
    if not diff_text:
        print("Error: No diff fetched.", file=sys.stderr)
        sys.exit(1)

    print("Sending diff to Cloud Function for code review...", file=sys.stderr)
    review = get_code_review(diff_text, cloud_function_url)

    print(review)

if __name__ == "__main__":
    main()
