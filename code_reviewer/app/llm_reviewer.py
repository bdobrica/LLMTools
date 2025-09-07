import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import git
import git.exc
import openai


class LLMReviewer:
    def __init__(self, repo_path: str, base_branch: str = "main", ssh_key: Optional[str] = None):
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.ssh_key = ssh_key
        self.repo = self._load_repo()

    def _load_repo(self):
        # Optionally set SSH key for Git
        if self.ssh_key:
            os.environ["GIT_SSH_COMMAND"] = f"ssh -i {self.ssh_key}"
        try:
            return git.Repo(self.repo_path, search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            print("Error: Not a git repository.", file=sys.stderr)
            sys.exit(1)

    def get_diff(self) -> Dict[str, List[int]]:
        # Returns dict: {file_path: [changed_line_numbers]}
        diff = self.repo.git.diff(f"{self.base_branch}...HEAD", "--unified=0", "--no-color")
        file_diffs = {}
        current_file = None
        for line in diff.splitlines():
            if line.startswith("diff --git"):
                parts = line.split(" b/")
                if len(parts) == 2:
                    current_file = parts[1]
            elif line.startswith("@@") and current_file:
                # @@ -old,+new @@
                hunk_header = line.split(" ")[1]
                _, new = hunk_header.split("+")
                new_info = new.split(",")
                start = int(new_info[0])
                length = int(new_info[1]) if len(new_info) > 1 else 1
                changed_lines = list(range(start, start + length))
                file_diffs.setdefault(current_file, []).extend(changed_lines)
        return file_diffs

    def run_pyright_on_files(self, files: Dict[str, List[int]]) -> Dict[str, Dict[int, List[str]]]:
        # Returns: {file_path: {line: [pyright_issues]}}
        results = {}
        for file, lines in files.items():
            working_dir = Path(self.repo.working_tree_dir or ".")
            rel_path = Path(file).relative_to(working_dir)
            try:
                output = subprocess.check_output(
                    ["pyright", str(rel_path)],
                    cwd=str(working_dir),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
            except subprocess.CalledProcessError as e:
                output = e.output
            issues = self.parse_pyright_output(output, lines)
            results[file] = issues
        return results

    @staticmethod
    def parse_pyright_output(pyright_output: str, interested_lines: List[int]) -> Dict[int, List[str]]:
        # Parse pyright output, collect messages for interested lines
        result = {}
        for line in pyright_output.splitlines():
            # Typical: path/to/file.py:12:5 - error X: description
            if ":" in line:
                parts = line.split(":")
                if len(parts) >= 3 and parts[1].isdigit():
                    line_num = int(parts[1])
                    if line_num in interested_lines:
                        msg = ":".join(parts[2:]).strip()
                        result.setdefault(line_num, []).append(msg)
        return result

    def get_instructions(self, instructions_path: Optional[str] = None) -> str:
        # Check if custom instructions path is provided and exists
        if instructions_path and Path(instructions_path).is_file():
            path = Path(instructions_path)
        else:
            # Check for INSTRUCTIONS.md in repo root
            working_dir = Path(self.repo.working_tree_dir or ".")
            repo_instructions = working_dir / "INSTRUCTIONS.md"
            if repo_instructions.is_file():
                path = repo_instructions
            else:
                # Default to GENERAL_REVIEW.md in app/instructions folder
                app_dir = Path(__file__).parent
                path = app_dir / "instructions" / "GENERAL_REVIEW.md"
                if not path.is_file():
                    print(f"Default instructions not found at {path}. Please provide --instructions.", file=sys.stderr)
                    sys.exit(1)

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def build_prompt(self, file_diffs: Dict[str, List[int]], pyright_results: Dict[str, Dict[int, List[str]]]) -> str:
        # Builds a "user" prompt summarizing the diffs and errors/warnings
        lines = []
        for file, changed_lines in file_diffs.items():
            lines.append(f"File: {file}")
            for line_no in changed_lines:
                pyright_msgs = pyright_results.get(file, {}).get(line_no, [])
                lines.append(f"  Line {line_no}:")
                for msg in pyright_msgs:
                    lines.append(f"    Pyright: {msg}")
        return "\n".join(lines)

    def call_openai(self, system_prompt: str, user_prompt: str, model="gpt-4-turbo") -> str:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("Please set your OPENAI_API_KEY environment variable.", file=sys.stderr)
            sys.exit(1)
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
