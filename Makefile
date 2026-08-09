SKILLS_DIR := skills
SKILLS := $(sort $(shell ls -1 $(SKILLS_DIR)))
CLAUDE_SKILLS_DIR := $(HOME)/.claude/skills
SKILLS_ABS := $(abspath $(SKILLS_DIR))

# Every tracked markdown file, not just the skills — README and AGENTS.md are
# the most-read pages here and were previously unlinted.
MARKDOWN := $(SKILLS_DIR) docs reports README.md AGENTS.md CONTRIBUTING.md .github

# .tool-versions is the single source of truth; CI reads the same file.
TOOL_VERSIONS := .tool-versions
RUMDL_VERSION := $(shell awk '$$1 == "rumdl" { print $$2 }' $(TOOL_VERSIONS))
SKILL_VALIDATOR_VERSION := $(shell awk '$$1 == "skill-validator" { print $$2 }' $(TOOL_VERSIONS))

.PHONY: all ci validate lint lint-check fmt-check lint-and-validate check-tools install-tools link unlink

lint-and-validate: lint validate

# Non-mutating gate for CI: structure, formatting and lint rules.
ci: validate fmt-check lint-check

# Fail loudly when local tooling has drifted from the versions CI runs.
check-tools:
	@have=$$(rumdl --version | awk '{ print $$NF }'); \
	if [ "$$have" != "$(RUMDL_VERSION)" ]; then \
		echo "rumdl $$have installed, $(TOOL_VERSIONS) pins $(RUMDL_VERSION)"; exit 1; \
	fi
	@have=$$(skill-validator --version | awk '{ print $$NF }' | sed 's/^v//'); \
	if [ "$$have" != "$(SKILL_VALIDATOR_VERSION)" ]; then \
		echo "skill-validator $$have installed, $(TOOL_VERSIONS) pins $(SKILL_VALIDATOR_VERSION)"; exit 1; \
	fi
	@echo "tooling matches $(TOOL_VERSIONS)"

validate:
	@for skill in $(SKILLS); do \
		skill-validator validate structure --strict $(SKILLS_DIR)/$$skill/; \
	done

# Homebrew works on macOS and Linuxbrew. Without it, install the pinned releases
# from github.com/rvcas/rumdl and github.com/agent-ecosystem/skill-validator, or
# use `cargo binstall`. Either way, `make check-tools` is the arbiter.
install-tools:
	@command -v brew >/dev/null || { \
		echo "Homebrew not found. Install rumdl $(RUMDL_VERSION) and"; \
		echo "skill-validator $(SKILL_VALIDATOR_VERSION) from their GitHub releases,"; \
		echo "then run 'make check-tools' to confirm."; exit 1; \
	}
	@brew install rumdl
	@brew install agent-ecosystem/tap/skill-validator
	@$(MAKE) --no-print-directory check-tools

lint:
	@rumdl fmt $(MARKDOWN)
	@rumdl check --fix $(MARKDOWN)

fmt-check:
	@rumdl fmt --check $(MARKDOWN)

lint-check:
	@rumdl check $(MARKDOWN)

link:
	@mkdir -p $(CLAUDE_SKILLS_DIR)
	@for skill in $(SKILLS); do \
		ln -sfn $(SKILLS_ABS)/$$skill $(CLAUDE_SKILLS_DIR)/$$skill; \
		echo "linked $(CLAUDE_SKILLS_DIR)/$$skill -> $(SKILLS_ABS)/$$skill"; \
	done

unlink:
	@for skill in $(SKILLS); do \
		if [ -L $(CLAUDE_SKILLS_DIR)/$$skill ]; then \
			rm $(CLAUDE_SKILLS_DIR)/$$skill; \
			echo "removed $(CLAUDE_SKILLS_DIR)/$$skill"; \
		fi; \
	done
