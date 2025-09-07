import argparse
import sys

from .llm_reviewer import LLMReviewer


def main():
    parser = argparse.ArgumentParser(description="Review Python diffs with Pyright and OpenAI LLM")
    parser.add_argument("--repo", type=str, default=".", help="Path to the git repository")
    parser.add_argument("--base-branch", type=str, default="main", help="Branch to diff against")
    parser.add_argument("--instructions", type=str, help="Path to INSTRUCTIONS.md")
    parser.add_argument("--ssh-key", type=str, help="Path to SSH key for git access")
    parser.add_argument("--model", type=str, default="gpt-4-turbo", help="OpenAI model to use")
    args = parser.parse_args()

    reviewer = LLMReviewer(args.repo, args.base_branch, args.ssh_key)
    file_diffs = reviewer.get_diff()
    if not file_diffs:
        print("No changes detected against base branch.")
        sys.exit(0)
    pyright_results = reviewer.run_pyright_on_files(file_diffs)
    instructions = reviewer.get_instructions(args.instructions)
    user_prompt = reviewer.build_prompt(file_diffs, pyright_results)
    print("Sending to LLM...\n")
    response = reviewer.call_openai(instructions, user_prompt, model=args.model)
    print("----- LLM REVIEW OUTPUT -----")
    print(response)


if __name__ == "__main__":
    main()
