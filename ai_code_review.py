import os
import ast
import openai
import subprocess

openai.api_key = os.environ["OPENAI_API_KEY"]

def get_changed_lines(file_path):
    try:
        base_sha = os.environ.get("GITHUB_BASE_SHA", os.environ.get("GITHUB_EVENT_PULL_REQUEST_BASE_SHA"))
        head_sha = os.environ["GITHUB_SHA"]
        diff = subprocess.check_output(
            ["git", "diff", "-U0", base_sha, head_sha, "--", file_path]
        ).decode()
        
        changed_lines = []
        for line in diff.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                parts = line[1:].strip().split(':', 1)
                if parts and parts[0].isdigit():
                    changed_lines.append(int(parts[0]))
        print(changed_lines)
        return changed_lines
    except Exception as e:
        print(f"Error getting changed lines: {e}")
        return []

def get_functions(file_path):
    """Parse Python file and return functions with line numbers"""
    with open(file_path, "r") as f:
        code = f.read()
    
    functions = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start = node.lineno
                end = node.end_lineno
                functions.append({
                    "name": node.name,
                    "start": start,
                    "end": end,
                    "code": ast.get_source_segment(code, node)
                })
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return functions

def analyze_code(code):
    """Send code to OpenAI for review"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior Python developer. Review this code for:\n- Code quality\n- Potential bugs\n- Security issues\n- Performance improvements\n- Best practices\nProvide concise feedback in markdown."},
                {"role": "user", "content": f"Code to review:\n```python\n{code}\n```"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating review: {str(e)}"

def main():
    review_output = ["## 🤖 AI Code Review Report"]

    try:
        changed_files = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=d", "origin/develop", "HEAD", "*.py"]
        ).decode().splitlines()

        for file in changed_files:
            if not os.path.exists(file):
                continue

            functions = get_functions(file)
            changed_lines = get_changed_lines(file)

            if not functions:
                continue

            review_output.append(f"\n### 📁 File: {file}")

            for func in functions:
                modified = any(
                    func["start"] <= lineno <= func["end"]
                    for line in changed_lines
                    if (lineno := int(line.split(':')[0]))
                ) if changed_lines else False

                if modified:
                    analysis = analyze_code(func["code"])
                    review_output.append(
                        f"\n#### 🛠 Function: {func['name']}\n"
                        f"{analysis}\n"
                        f"```python\n{func['code']}\n```"
                    )
    except Exception as e:
        review_output.append(f"\nError processing code review: {str(e)}")

    with open('review.md', 'w') as f:
        f.write('\n'.join(review_output))

    sanitized_review = '\n'.join(review_output).replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D')
    print(f"::set-output name=REVIEW::{sanitized_review}")

if __name__ == "__main__":
    main()
