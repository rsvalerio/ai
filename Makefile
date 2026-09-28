# The repo is a multi-plugin marketplace: each plugin lives in plugins/<name>/ with
# its own skills/, and a top-level skills/ holds standalone skills that belong to no
# plugin (optional). Everything below discovers skills by globbing both, so adding a
# plugin needs no Makefile edit.
PLUGINS := $(sort $(patsubst %/,%,$(wildcard plugins/*/)))
SKILL_DIRS := $(sort $(patsubst %/,%,$(wildcard plugins/*/skills/*/ skills/*/)))
CLAUDE_SKILLS_DIR := $(HOME)/.claude/skills

# Every tracked markdown file, not just the skills — README and AGENTS.md are
# the most-read pages here and were previously unlinted.
MARKDOWN := $(wildcard plugins/*/skills skills) docs reports README.md AGENTS.md CONTRIBUTING.md .github

# .tool-versions is the single source of truth; CI and `mise install` read the
# same file. Names may carry a mise backend prefix, so match on the last segment.
TOOL_VERSIONS := .tool-versions
tool_version = $(shell awk -v t=$(1) '$$1 == t || $$1 ~ "/" t "$$" { print $$2 }' $(TOOL_VERSIONS))
RUMDL_VERSION := $(call tool_version,rumdl)
SKILL_VALIDATOR_VERSION := $(call tool_version,skill-validator)

.PHONY: all ci validate validate-marketplace validate-rules check-install eval lint lint-check fmt-check lint-and-validate check-tools install-tools link unlink

lint-and-validate: lint validate validate-marketplace validate-rules

# Every non-mutating check, without ops: the set `ops qa` runs, minus check-tools and the
# action-pin lint, which is the ops built-in `ops lint-actions`. .ops.toml is where the
# gates are defined; this target is for machines without ops.
ci: validate validate-marketplace validate-rules fmt-check lint-check check-install

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

# A plain `for` loop here discarded every skill's exit code except the last one,
# so the gate reported success while skills were failing. scripts/validate-skills.py
# runs the same --strict check, propagates failures, and carries one documented
# allowlist entry (see the script).
validate:
	@python3 scripts/validate-skills.py

# The repo root is a Claude Code plugin marketplace (.claude-plugin/
# marketplace.json) listing every plugin under plugins/. Validate the marketplace
# and each plugin's own manifest. claude-code is expected on PATH rather than
# pinned in .tool-versions: anyone developing skills already runs it, and CI
# installs its own pinned copy.
validate-marketplace:
	@claude plugin validate .
	@for plugin in $(PLUGINS); do claude plugin validate $$plugin || exit 1; done

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

# The review skills load rules in three tiers, and rules/index.md is maintained
# by hand (AGENTS.md explains why). A rule that lands in references/rules/<CAT>.md
# without an index line is invisible to a scan — the skill silently stops
# enforcing it, and nothing else in `make ci` notices. Compare the two ID sets.
validate-rules:
	@python3 scripts/validate-rules.py

# Behavioural gate: do the skills still trigger? `claude plugin eval` runs each
# case twice (plugin loaded / not loaded) and reports the delta. Every grader in
# plugins/<name>/evals/ is free — tool_used only — so this costs agent runs, not
# judge calls. Each plugin with an evals/ directory runs against its own manifest.
# Deliberately not part of `make ci`: it is non-deterministic and needs
# credentials. Run it before a release and after a Claude Code model bump.
#
# The --allow-tools grant is what makes "must not write / must not research"
# graders mean anything: without it a gated tool is withheld from both arms, so
# a max-0 count passes vacuously. Each case's allowed_tools still bounds what
# its runs can reach.
EVAL_ALLOW_TOOLS := Write Edit WebSearch WebFetch

eval:
	@for plugin in $(PLUGINS); do \
		[ -d $$plugin/evals ] || continue; \
		echo "== $$plugin"; \
		claude plugin eval $$plugin --trust-plugin --no-publish --allow-tools $(EVAL_ALLOW_TOOLS) || exit 1; \
	done

lint:
	@rumdl fmt $(MARKDOWN)
	@rumdl check --fix $(MARKDOWN)

fmt-check:
	@rumdl fmt --check $(MARKDOWN)

lint-check:
	@rumdl check $(MARKDOWN)

link:
	@mkdir -p $(CLAUDE_SKILLS_DIR)
	@for dir in $(SKILL_DIRS); do \
		skill=$$(basename $$dir); \
		ln -sfn $(CURDIR)/$$dir $(CLAUDE_SKILLS_DIR)/$$skill; \
		echo "linked $(CLAUDE_SKILLS_DIR)/$$skill -> $(CURDIR)/$$dir"; \
	done

# `make link` must install every skill as a readable SKILL.md, and `make unlink` must remove
# exactly those links. Runs against a scratch directory, never ~/.claude/skills.
check-install:
	@[ -n "$(SKILL_DIRS)" ] || { echo "no skills found"; exit 1; }
	@tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	$(MAKE) --no-print-directory link CLAUDE_SKILLS_DIR="$$tmp" >/dev/null; \
	for dir in $(SKILL_DIRS); do \
		skill=$$(basename $$dir); \
		test -f "$$tmp/$$skill/SKILL.md" || { echo "$$skill did not link to a readable SKILL.md"; exit 1; }; \
	done; \
	$(MAKE) --no-print-directory unlink CLAUDE_SKILLS_DIR="$$tmp" >/dev/null; \
	left=$$(ls -A "$$tmp"); [ -z "$$left" ] || { echo "unlink left behind: $$left"; exit 1; }; \
	echo "all $(words $(SKILL_DIRS)) skills link and unlink cleanly"

unlink:
	@for dir in $(SKILL_DIRS); do \
		skill=$$(basename $$dir); \
		if [ -L $(CLAUDE_SKILLS_DIR)/$$skill ]; then \
			rm $(CLAUDE_SKILLS_DIR)/$$skill; \
			echo "removed $(CLAUDE_SKILLS_DIR)/$$skill"; \
		fi; \
	done
