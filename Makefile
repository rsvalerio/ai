SKILLS_DIR := skills
SKILLS := $(sort $(shell ls -1 $(SKILLS_DIR)))
CLAUDE_SKILLS_DIR := $(HOME)/.claude/skills
SKILLS_ABS := $(abspath $(SKILLS_DIR))

.PHONY: all ci validate lint lint-check fmt-check lint-and-validate install-tools link unlink

lint-and-validate: lint validate

# Non-mutating gate for CI: structure, formatting and lint rules.
ci: validate fmt-check lint-check

validate:
	@for skill in $(SKILLS); do \
		skill-validator validate structure --strict $(SKILLS_DIR)/$$skill/; \
	done

install-tools:
	@brew install rumdl
	@brew install agent-ecosystem/tap/skill-validator

lint:
	@for skill in $(SKILLS); do \
		rumdl fmt $(SKILLS_DIR)/$$skill/; \
		rumdl check --fix $(SKILLS_DIR)/$$skill/; \
	done

fmt-check:
	@for skill in $(SKILLS); do \
		rumdl fmt --check $(SKILLS_DIR)/$$skill/; \
	done

lint-check:
	@for skill in $(SKILLS); do \
		rumdl check $(SKILLS_DIR)/$$skill/; \
	done

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
