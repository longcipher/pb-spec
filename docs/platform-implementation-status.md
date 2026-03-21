# Platform Implementation Status

All platform adapters in pb-spec are **fully implemented** and production-ready.

## Supported Platforms

| Platform | Status | Directory Structure | File Format | Global Install Support |
| :--- | :--- | :--- | :--- | :--- |
| **Claude Code** | ✅ Complete | `.claude/skills/<name>/SKILL.md` | YAML frontmatter + Markdown | ✅ Yes (`~/.claude/skills/`) |
| **VS Code Copilot** | ✅ Complete | `.github/prompts/<name>.prompt.md` | Plain Markdown | ✅ Yes (`~/.copilot/prompts/`) |
| **OpenCode** | ✅ Complete | `.opencode/skills/<name>/SKILL.md` | YAML frontmatter + Markdown | ✅ Yes (`~/.config/opencode/skills/`) |
| **Gemini CLI** | ✅ Complete | `.gemini/commands/<name>.toml` | TOML (description + prompt) | ✅ Yes (`~/.gemini/commands/`) |
| **OpenAI Codex** | ✅ Complete | `.codex/prompts/<name>.md` | YAML frontmatter + Markdown | ✅ Yes (`~/.codex/prompts/`) |

## Implementation Details

### Claude Code (`claude.py`)

- Uses SKILL.md files with YAML frontmatter
- Supports `CLAUDE_CONFIG_DIR` environment variable for custom config location
- Installs reference files alongside skill files

### VS Code Copilot (`copilot.py`)

- Uses `.prompt.md` files without frontmatter
- Simplest format - just raw prompt content
- Self-contained prompts (no reference files)

### OpenCode (`opencode.py`)

- Uses SKILL.md files with YAML frontmatter
- Supports XDG Base Directory specification (`XDG_CONFIG_HOME`)
- Installs reference files alongside skill files

### Gemini CLI (`gemini.py`)

- Uses TOML format with `description` and `prompt` fields
- Self-contained prompts (no reference files)
- Handles quote escaping in TOML values

### OpenAI Codex (`codex.py`)

- Uses `.md` files with YAML frontmatter
- Supports `CODEX_HOME` environment variable for custom config location
- Self-contained prompts (no reference files)

## Platform-Specific Features

### Skill Loading Strategy

- **Claude, OpenCode**: Use `load_skill_content()` (SKILL.md with frontmatter)
- **Copilot, Gemini, Codex**: Use `load_prompt()` (simple prompt files)

### Reference File Installation

- **Claude, OpenCode**: Install reference files in `references/` subdirectory
- **Copilot, Gemini, Codex**: Self-contained, no reference files needed

## Usage Examples

```bash
# Install for all platforms
pb-spec init --ai all

# Install for specific platform
pb-spec init --ai claude
pb-spec init --ai copilot
pb-spec init --ai opencode
pb-spec init --ai gemini
pb-spec init --ai codex

# Global installation
pb-spec init --ai claude -g
```

## Testing

All platform adapters are tested in `tests/test_platforms.py`:

- Path generation (local and global)
- Content rendering
- File installation
- Idempotency (skip existing files without `--force`)

## Contributing

When adding new platform support:

1. Create a new file in `src/pb_spec/platforms/`
2. Inherit from `Platform` base class
3. Implement required abstract methods:
   - `name` property
   - `get_skill_path()` method
   - `render_skill()` method
4. Add platform to `PLATFORMS` dict in `src/pb_spec/platforms/__init__.py`
5. Add tests in `tests/test_platforms.py`
6. Update this documentation
