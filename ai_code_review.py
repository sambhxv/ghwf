import os
import ast
import openai
import subprocess
from unidiff import PatchSet

openai.api_key = os.environ["OPENAI_API_KEY"]
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

def get_changed_lines(file_path):
    try:
        base_sha = os.environ.get("GITHUB_BASE_SHA")
        head_sha = os.environ["GITHUB_SHA"]
        diff = subprocess.check_output(
            ["git", "diff", "-U0", base_sha, head_sha, "--", file_path]
        ).decode()
        
        patch = PatchSet(diff)
        changed_lines = set()
        for file in patch:
            for hunk in file:
                # Collect all lines in the target (new file) range
                start = hunk.target_start
                length = hunk.target_length
                changed_lines.update(range(start, start + length))
        return list(changed_lines)
    except Exception as e:
        print(f"Error getting changed lines: {e}")
        return []

def get_functions(file_path):
    with open(file_path, "r") as f:
        code = f.read()
    
    functions = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": node.name,
                    "start": node.lineno,
                    "end": node.end_lineno,
                    "code": ast.get_source_segment(code, node)
                })
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return functions

def analyze_code(code_snippet):
    MAX_CODE_LENGTH = 3000
    truncated = code_snippet[:MAX_CODE_LENGTH] + "\n... (truncated)" if len(code_snippet) > MAX_CODE_LENGTH else code_snippet
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a senior Python developer. Review this code for quality, bugs, security, performance, and best practices. Provide concise feedback in markdown."},
                {"role": "user", "content": f"Code to review:\n```python\n{truncated}\n```"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error generating review: {str(e)}"

def main():
    review_output = ["## 🤖 AI Code Review Report"]
    try:
        base_sha = os.environ.get("GITHUB_BASE_SHA")
        if not base_sha:
            raise ValueError("GITHUB_BASE_SHA environment variable not set")

        changed_files = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=d", base_sha, "HEAD", "--", "*.py"]
        ).decode().splitlines()

        for file_path in changed_files:
            if not os.path.exists(file_path):
                continue

            functions = get_functions(file_path)
            changed_lines = get_changed_lines(file_path)
            if not functions or not changed_lines:
                continue

            review_output.append(f"\n### 📄 File: `{file_path}`")
            file_reviews = []

            for func in functions:
                if any(func["start"] <= line <= func["end"] for line in changed_lines):
                    analysis = analyze_code(func["code"])
                    file_reviews.append(
                        f"\n#### 🔧 Function: `{func['name']}`\n"
                        f"{analysis}\n"
                        f"```python\n{func['code'][:500]}\n...\n```"
                    )

            if file_reviews:
                review_output.extend(file_reviews)
                
    except Exception as e:
        review_output.append(f"\n❌ **Critical Error**: {str(e)}")

    review_content = '\n'.join(review_output)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f'REVIEW<<REVIEW_EOF\n{review_content}\nREVIEW_EOF\n')

if __name__ == "__main__":
    main()
