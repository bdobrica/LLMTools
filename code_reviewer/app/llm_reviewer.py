import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import git
import git.exc
import openai


class LLMReviewer:
    """
    A code reviewer that uses LLMs to analyze git diffs and provide code review feedback.

    This class integrates git diff analysis, static code analysis (via pyright), and
    LLM-based code review to provide comprehensive feedback on code changes.

    Attributes:
        repo_path (str): Path to the git repository to analyze.
        base_branch (str): The base branch to compare against (default: "main").
        ssh_key (Optional[str]): SSH key path for git operations if needed.
        repo (git.Repo): GitPython repository object.
    """

    def __init__(self, repo_path: str, base_branch: str = "main", ssh_key: Optional[str] = None):
        """
        Initialize the LLMReviewer.

        Args:
            repo_path (str): Path to the git repository to analyze.
            base_branch (str, optional): The base branch to compare against. Defaults to "main".
            ssh_key (Optional[str], optional): Path to SSH key for git operations. Defaults to None.
        """
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.ssh_key = ssh_key
        self.repo = self._load_repo()

    def _load_repo(self):
        """
        Load and validate the git repository.

        Sets up SSH key if provided and creates a GitPython Repo object.

        Returns:
            git.Repo: The loaded git repository object.

        Raises:
            SystemExit: If the path is not a valid git repository.
        """
        # Optionally set SSH key for Git
        if self.ssh_key:
            os.environ["GIT_SSH_COMMAND"] = f"ssh -i {self.ssh_key}"
        try:
            return git.Repo(self.repo_path, search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            print("Error: Not a git repository.", file=sys.stderr)
            sys.exit(1)

    def get_diff(self) -> Dict[str, List[int]]:
        """
        Get the git diff between remote base branch and HEAD, extracting changed line numbers.

        Analyzes the git diff output to identify which files have changed and which
        specific line numbers were modified in each file.

        Returns:
            Dict[str, List[int]]: A dictionary mapping file paths to lists of changed line numbers.
                Example: {"src/file.py": [10, 11, 12], "other/file.py": [5, 6]}
        """
        # Returns dict: {file_path: [changed_line_numbers]}
        diff = self.repo.git.diff(f"origin/{self.base_branch}...HEAD", "--unified=0", "--no-color")
        file_diffs = {}
        current_file = None
        for line in diff.splitlines():
            if line.startswith("diff --git"):
                parts = line.split(" b/")
                if len(parts) == 2:
                    current_file = parts[1]
            elif line.startswith("@@") and current_file:
                match = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if match:
                    start = int(match.group(1))
                    length = int(match.group(2)) if match.group(2) else 1
                    changed_lines = list(range(start, start + length))
                    file_diffs.setdefault(current_file, []).extend(changed_lines)
        return file_diffs

    def get_full_diff(self) -> str:
        """
        Get the complete git diff between remote base branch and HEAD with context.

        Returns the full diff output including added, removed, and context lines
        for comprehensive code review.

        Returns:
            str: The complete git diff output with context lines.
        """
        return self.repo.git.diff(f"origin/{self.base_branch}...HEAD", "--no-color")

    def run_pyright_on_files(self, files: Dict[str, List[int]]) -> Dict[str, Dict[int, List[str]]]:
        """
        Run pyright static analysis on the specified files and extract issues for changed lines.

        Args:
            files (Dict[str, List[int]]): Dictionary mapping file paths to lists of line numbers
                that have changed and should be analyzed.

        Returns:
            Dict[str, Dict[int, List[str]]]: Nested dictionary structure:
                - Outer key: file path
                - Inner key: line number
                - Inner value: list of pyright issue messages for that line
                Example: {"src/file.py": {10: ["error: undefined variable"], 11: []}}
        """
        # Returns: {file_path: {line: [pyright_issues]}}
        results = {}
        for file, lines in files.items():
            working_dir = Path(self.repo.working_tree_dir or ".")
            rel_path = Path(file).resolve().relative_to(working_dir)
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
        """
        Parse pyright output and extract issues for specific line numbers.

        Args:
            pyright_output (str): Raw output from pyright command.
            interested_lines (List[int]): List of line numbers to extract issues for.

        Returns:
            Dict[int, List[str]]: Dictionary mapping line numbers to lists of issue messages.
                Only includes lines that are in the interested_lines list.
                Example: {10: ["error: undefined variable"], 15: ["warning: unused import"]}
        """
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
        """
        Load review instructions from a file using a fallback hierarchy.

        The method tries to find instructions in the following order:
        1. Custom instructions path (if provided and exists)
        2. INSTRUCTIONS.md in the repository root
        3. instructions/GENERAL_REVIEW.md in the app directory (default fallback)

        Args:
            instructions_path (Optional[str], optional): Path to a custom instructions file.
                Defaults to None.

        Returns:
            str: The contents of the instructions file.

        Raises:
            SystemExit: If no instructions file can be found in any of the fallback locations.
        """
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

    def build_prompt(
        self,
        file_diffs: Dict[str, List[int]],
        pyright_results: Dict[str, Dict[int, List[str]]],
        full_diff: str,
    ) -> str:
        """
        Build a user prompt summarizing the code changes and static analysis results.

        Creates a structured text prompt that includes information about changed files,
        the actual code diff, modified line numbers, and any pyright issues found on those lines.

        Args:
            file_diffs (Dict[str, List[int]]): Dictionary mapping file paths to lists of
                changed line numbers.
            pyright_results (Dict[str, Dict[int, List[str]]]): Nested dictionary with
                pyright issues organized by file and line number.
            full_diff (str): The complete git diff showing actual code changes.

        Returns:
            str: A formatted text prompt suitable for sending to an LLM, containing
                the actual code diff and associated static analysis messages.
        """
        # Build a comprehensive prompt with actual code changes and analysis
        lines = ["## Code Changes", ""]
        lines.append("Here is the git diff showing the actual code changes:")
        lines.append("```diff")
        lines.append(full_diff)
        lines.append("```")
        lines.append("")

        # Add pyright analysis if there are any issues
        has_pyright_issues = any(
            any(issues for issues in file_issues.values()) for file_issues in pyright_results.values()
        )

        if has_pyright_issues:
            lines.append("## Static Analysis (Pyright) Issues")
            lines.append("")
            for file, changed_lines in file_diffs.items():
                file_has_issues = False
                file_issues = []
                for line_no in changed_lines:
                    pyright_msgs = pyright_results.get(file, {}).get(line_no, [])
                    if pyright_msgs:
                        file_has_issues = True
                        file_issues.append(f"  Line {line_no}:")
                        for msg in pyright_msgs:
                            file_issues.append(f"    {msg}")

                if file_has_issues:
                    lines.append(f"**File: {file}**")
                    lines.extend(file_issues)
                    lines.append("")

        return "\n".join(lines)

    def call_openai(self, system_prompt: str, user_prompt: str, model="gpt-4-turbo") -> str:
        """
        Make a request to OpenAI's API for code review analysis.

        Sends the system instructions and user prompt to OpenAI's chat completion API
        and returns the response. Handles API key validation and error cases.

        Args:
            system_prompt (str): The system message containing review instructions.
            user_prompt (str): The user message containing code changes and issues.
            model (str, optional): The OpenAI model to use. Defaults to "gpt-4-turbo".

        Returns:
            str: The AI's response to the code review request, with whitespace stripped.
                Returns empty string if the response content is None.

        Raises:
            SystemExit: If the OPENAI_API_KEY environment variable is not set.
        """
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
