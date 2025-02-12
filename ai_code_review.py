import os
import ast
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path
from openai import OpenAI
from git import Repo, Git
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Function:
    name: str
    start: int
    end: int
    code: str

class CodeReviewer:
    def __init__(self, repo_path: str = '.'):
        self.repo = Repo(repo_path)
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.base_ref = os.environ.get("GITHUB_BASE_REF", "main")
        self.head_ref = os.environ.get("GITHUB_HEAD_REF", "HEAD")
        
    @lru_cache(maxsize=100)
    def get_changed_lines(self, file_path: Path) -> Dict[int, str]:
        """Returns a dictionary of changed line numbers and their content."""
        try:
            diff = self.repo.git.diff(
                f"origin/{self.base_ref}",
                self.head_ref,
                "--",
                str(file_path),
                unified=0
            )
            
            changed_lines = {}
            current_line = None
            
            for line in diff.split('\n'):
                if line.startswith('@@'):
                    # Parse the @@ -a,b +c,d @@ line to get new line numbers
                    parts = line.split(' ')[2].split(',')[0]
                    current_line = int(parts.lstrip('+'))
                elif line.startswith('+') and not line.startswith('+++'):
                    if current_line is not None:
                        changed_lines[current_line] = line[1:]
                        current_line += 1
                        
            return changed_lines
        except Exception as e:
            logger.error(f"Error getting changed lines for {file_path}: {e}")
            return {}

    def parse_functions(self, file_path: Path) -> List[Function]:
        """Parse Python file and return functions with their metadata."""
        try:
            code = file_path.read_text()
            tree = ast.parse(code)
            
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(Function(
                        name=node.name,
                        start=node.lineno,
                        end=node.end_lineno,
                        code=ast.get_source_segment(code, node)
                    ))
            return functions
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return []

    def analyze_code(self, code: str, context: Optional[str] = None) -> str:
        """Send code to OpenAI for review with improved prompt."""
        try:
            system_prompt = """You are an expert Python developer conducting a code review. Focus on:
1. Code quality and readability
2. Potential bugs and edge cases
3. Security vulnerabilities
4. Performance optimizations
5. Python best practices and idioms
6. Type hints and documentation

Provide specific, actionable feedback with examples where relevant."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review this Python code:\n```python\n{code}\n```"}
            ]

            if context:
                messages.append({"role": "user", "content": f"Additional context: {context}"})

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating review: {e}")
            return f"Error: Unable to generate review due to: {str(e)}"

    def generate_review(self) -> str:
        """Generate a complete code review report."""
        review_sections = ["# 🤖 AI Code Review Report\n"]
        
        try:
            # Get all changed Python files
            changed_files = [
                Path(item.a_path)
                for item in self.repo.index.diff(f"origin/{self.base_ref}")
                if item.a_path.endswith('.py')
            ]

            for file_path in changed_files:
                if not file_path.exists():
                    continue

                changed_lines = self.get_changed_lines(file_path)
                functions = self.parse_functions(file_path)
                
                if not functions or not changed_lines:
                    continue

                review_sections.append(f"## 📁 {file_path}\n")
                
                for func in functions:
                    # Check if function contains changed lines
                    func_changed_lines = {
                        line_num: content 
                        for line_num, content in changed_lines.items()
                        if func.start <= line_num <= func.end
                    }
                    
                    if func_changed_lines:
                        context = f"Changed lines in this function:\n" + \
                                "\n".join(f"Line {num}: {content}" 
                                        for num, content in func_changed_lines.items())
                        
                        analysis = self.analyze_code(func.code, context)
                        review_sections.extend([
                            f"### 🛠 Function: {func.name}",
                            "#### Changes:",
                            "```python",
                            *[f"{num}: {content}" for num, content in func_changed_lines.items()],
                            "```",
                            "#### Review:",
                            analysis,
                            "\n"
                        ])

            return "\n".join(review_sections)
            
        except Exception as e:
            logger.error(f"Error generating review report: {e}")
            return f"# ❌ Error Generating Review\n\nAn error occurred: {str(e)}"

def main():
    reviewer = CodeReviewer()
    review = reviewer.generate_review()
    print(review)
    return "hehe"

if __name__ == "__main__":
    main()
