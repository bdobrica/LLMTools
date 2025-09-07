# Code Reviewer

An AI-powered code review tool that analyzes git diffs using static analysis (Pyright) and OpenAI's language models to provide comprehensive code review feedback.

## Features

- **Git Integration**: Analyzes changes between your current branch and a base branch (default: `main`)
- **Static Analysis**: Runs Pyright on changed files to catch type errors and other issues
- **AI Review**: Uses OpenAI's GPT models to provide intelligent code review comments
- **Focused Analysis**: Only analyzes lines that have actually changed in your diff
- **Customizable Instructions**: Supports custom review instructions or uses built-in guidelines

## Prerequisites

- Docker (recommended) or Python 3.12+ with pip
- Git repository with changes to review
- OpenAI API key

## Quick Start

### Using Docker (Recommended)

The easiest way to use the code reviewer is with the pre-built Docker image:

```bash
docker run -it --rm \
  -e OPENAI_API_KEY="your-api-key-here" \
  -v /path/to/your/repo:/repo \
  quay.io/bdobrica/code-reviewer:latest
```

### Using the Shell Script

For convenience, you can use the provided shell script that automatically loads your API key from `~/.env`:

1. Download and install the script:
```bash
curl -o /usr/local/bin/code-reviewer https://raw.githubusercontent.com/bdobrica/LLMTools/main/code_reviewer/code-reviewer
chmod +x /usr/local/bin/code-reviewer
```

2. Create a `~/.env` file with your OpenAI API key:
```bash
echo "OPENAI_API_KEY=your-api-key-here" >> ~/.env
```

3. Run the code reviewer from any git repository:
```bash
cd /path/to/your/repo
code-reviewer
```

### Local Installation

If you prefer to run without Docker:

1. Clone the repository:
```bash
git clone https://github.com/bdobrica/LLMTools.git
cd LLMTools/code_reviewer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Pyright:
```bash
npm install -g pyright
```

4. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

5. Run the reviewer:
```bash
python -m app --repo /path/to/your/repo
```

## Usage

### Command Line Options

```bash
python -m app [OPTIONS]
```

**Options:**
- `--repo PATH`: Path to the git repository (default: current directory)
- `--base-branch BRANCH`: Branch to compare against (default: "main")
- `--instructions PATH`: Path to custom review instructions file
- `--ssh-key PATH`: Path to SSH key for git access
- `--model MODEL`: OpenAI model to use (default: "gpt-4-turbo")

### Examples

**Basic usage in current directory:**
```bash
docker run -it --rm -e OPENAI_API_KEY -v $(pwd):/repo quay.io/bdobrica/code-reviewer:latest
```

**Compare against develop branch:**
```bash
docker run -it --rm -e OPENAI_API_KEY -v $(pwd):/repo quay.io/bdobrica/code-reviewer:latest --base-branch develop
```

**Use custom review instructions:**
```bash
docker run -it --rm -e OPENAI_API_KEY -v $(pwd):/repo -v /path/to/instructions.md:/instructions.md quay.io/bdobrica/code-reviewer:latest --instructions /instructions.md
```

**Use different OpenAI model:**
```bash
docker run -it --rm -e OPENAI_API_KEY -v $(pwd):/repo quay.io/bdobrica/code-reviewer:latest --model gpt-4o
```

## How It Works

1. **Git Diff Analysis**: The tool compares your current branch against the specified base branch to identify changed files and line numbers.

2. **Static Analysis**: Runs Pyright on the changed files to detect type errors, undefined variables, and other static analysis issues.

3. **AI Review**: Sends the git diff and static analysis results to OpenAI's language model with structured review instructions.

4. **Focused Feedback**: Only reports issues for lines that have actually changed, avoiding noise from existing code.

## Review Instructions

The tool uses a comprehensive set of review guidelines based on software engineering principles, prioritized as follows:

1. **KISS** (Keep It Simple, Stupid)
2. **YAGNI** (You Ain't Gonna Need It)
3. **Single Responsibility Principle**
4. **Open/Closed Principle**
5. **Liskov Substitution Principle**
6. **Interface Segregation Principle**
7. **Law of Demeter**
8. **Dependency Inversion Principle**
9. **Composition over Inheritance**
10. **Don't Repeat Yourself (DRY)**

### Custom Instructions

You can provide custom review instructions in three ways:

1. **Via command line**: Use `--instructions /path/to/instructions.md`
2. **Repository-specific**: Create `INSTRUCTIONS.md` in your repository root
3. **Default**: Uses built-in `GENERAL_REVIEW.md` instructions

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `GIT_SSH_COMMAND`: Custom SSH command for git operations (optional)

### Git Configuration

The tool automatically configures git to trust the `/repo` directory when running in Docker. For local installations, ensure your git configuration is properly set up.

## Troubleshooting

**"Not a git repository" error:**
- Ensure you're running the tool from within a git repository
- Check that the `--repo` path points to a valid git repository

**"No changes detected" message:**
- Verify you have uncommitted changes or commits ahead of the base branch
- Check that the base branch exists (use `--base-branch` to specify a different branch)

**OpenAI API errors:**
- Verify your `OPENAI_API_KEY` is correctly set
- Check your OpenAI account has sufficient credits
- Ensure the specified model is available for your account

**Pyright not found:**
- For local installations, install Pyright: `npm install -g pyright`
- The Docker image includes Pyright automatically

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is licensed under the Apache v2.0 License - see the [LICENSE](../LICENSE) file for details.
