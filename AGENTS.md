Always use the OpenAI developer documentation MCP server if you need to work with the OpenAI API, ChatGPT Apps SDK, Codex, Responses API, or related OpenAI platform features unless explicitly instructed otherwise.

# AGENTS Instructions for `new-chapter`

## Skills

### Available project skill (versioned in repo)
- `project-docling-engineer`: Project-specific engineering workflow for robust Python + Docling + DOCX pipelines, with practical implementation gates and fallback strategy.
  - Path: `.codex/skills/project-docling-engineer/SKILL.md`

### Available global skills (if installed in `$CODEX_HOME/skills`)
- `doc`: advanced `.docx` handling and layout fidelity
- `pdf`: PDF reading/generation/review
- `playwright`: browser automation flows
- `gh-fix-ci`: CI diagnosis and fixes for GitHub repos
- `gh-address-comments`: systematic PR comment resolution
- `security-best-practices`, `security-threat-model`, `security-ownership-map`

## Trigger Rules
- If the request involves Python architecture, Docling analysis, OCR fallback strategy, DOCX rendering/editability, RTL mixed-direction handling, or implementation planning for this repo, use `project-docling-engineer`.
- If the request is explicitly about `.docx` editing/layout fidelity, also use `doc`.
- If the request is CI-related in GitHub workflows, also use `gh-fix-ci`.
- If multiple skills apply, use the minimal set and state order briefly.

## Portable Setup
- Install project skills into local Codex with:
  - `python scripts/install_repo_skills.py --force`
- Run full local bootstrap with:
  - Windows: `powershell -ExecutionPolicy Bypass -File scripts/bootstrap_dev.ps1 -InstallOptionalEngines -ForceSkillOverwrite`
  - Linux/macOS: `INSTALL_OPTIONAL_ENGINES=1 FORCE_SKILL_OVERWRITE=1 bash scripts/bootstrap_dev.sh`
