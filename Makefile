# Project Makefile (powered by ~/.reta/lib/base.mk)
#
# Rules & usage:
#   - Inherited targets: `up`, `down`, `logs`, `clean`, `export`, `git-sync`, ...
#   - Do NOT define `help:` — `base.mk` generates a combined `help` for all targets.
#   - Override any other base target (e.g. `clean`, `up`) by defining it below
#     `include $(RETA_BASE)`. (Converted Makefiles comment out colliding rules
#     first; uncomment any of them to restore your custom behavior.)
#   - Section heading: `# === Section Name ===` (shown as a bold yellow header).
#   - Documented target: `name:  ## Short description` (targets without `##`
#     still run normally, but stay hidden from `make help`).

RETA_BASE := $(HOME)/.reta/lib/base.mk
ifeq ($(wildcard $(RETA_BASE)),)
$(error reta not installed: $(RETA_BASE) missing. Run install.sh from your reta repo)
endif
include $(RETA_BASE)

# Inherited base targets (matrix view):
#   help-base        help-project     up               down             restart
#   rebuild          ps               sh               logs             logs-all
#   logs-t           logs-errors      logs-warn        clean            clean-docker
#   export           clean-export     clean-exports    git-sync         git-status
#   check-secrets

IMAGE_NAME := food-delivery-router

hi:  ## Say hello
	@echo "Hi👋"

# === Routing Engine ===

build:  ## Build the Docker image
	$(call SHOW_CMD,docker build -t $(IMAGE_NAME) .)
	@docker build -t $(IMAGE_NAME) .

run:  ## Run the multi-order routing prototype
	$(call SHOW_CMD,docker run --rm $(IMAGE_NAME))
	@docker run --rm $(IMAGE_NAME)

run-interactive:  ## Run interactive CLI to enter custom orders and routes
	$(call SHOW_CMD,docker run --rm -it $(IMAGE_NAME) python -m src.main --interactive)
	@docker run --rm -it $(IMAGE_NAME) python -m src.main --interactive

web:  ## Start interactive web presentation on http://localhost:8000
	$(call SHOW_CMD,docker run --rm -p 8000:8000 $(IMAGE_NAME) python -m src.web.server)
	@docker run --rm -p 8000:8000 $(IMAGE_NAME) python -m src.web.server

present: web

test:  ## Run all unit tests with pytest
	$(call SHOW_CMD,docker run --rm $(IMAGE_NAME) pytest -v)
	@docker run --rm $(IMAGE_NAME) pytest -v

benchmark:  ## Run logarithmic efficiency benchmarks
	$(call SHOW_CMD,docker run --rm $(IMAGE_NAME) python -m src.benchmark.analyzer)
	@docker run --rm $(IMAGE_NAME) python -m src.benchmark.analyzer

visualize:  ## Generate route map and complexity PNG charts into outputs/
	@mkdir -p outputs
	$(call SHOW_CMD,docker run --rm --user $$(id -u):$$(id -g) -e MPLCONFIGDIR=/tmp/matplotlib -v "$(CURDIR)/outputs:/app/outputs" $(IMAGE_NAME) python -m src.visualization.plotter)
	@docker run --rm --user $$(id -u):$$(id -g) -e MPLCONFIGDIR=/tmp/matplotlib -v "$(CURDIR)/outputs:/app/outputs" $(IMAGE_NAME) python -m src.visualization.plotter

create-map:  ## Generate a random 10x10 city map (outputs/0001_map.png, 0002_map.png, ...)
	@mkdir -p outputs
	$(call SHOW_CMD,docker run --rm --user $$(id -u):$$(id -g) -e MPLCONFIGDIR=/tmp/matplotlib -v "$(CURDIR)/outputs:/app/outputs" $(IMAGE_NAME) python -m src.visualization.map_generator)
	@docker run --rm --user $$(id -u):$$(id -g) -e MPLCONFIGDIR=/tmp/matplotlib -v "$(CURDIR)/outputs:/app/outputs" $(IMAGE_NAME) python -m src.visualization.map_generator

create_map: create-map

clear-maps:  ## Delete all generated NNNN_map.png files after confirmation
	@shopt -s nullglob; \
	maps=(outputs/[0-9][0-9][0-9][0-9]_map.png); \
	if [ $${#maps[@]} -eq 0 ]; then \
		echo "No generated maps found in outputs/."; \
		exit 0; \
	fi; \
	echo "Maps to delete ($${#maps[@]} files):"; \
	printf "  - %s\n" "$${maps[@]}"; \
	read -r -p "Delete all generated maps? [y/N]: " ans; \
	if [[ "$$ans" =~ ^[yY]$$ ]]; then \
		rm -f "$${maps[@]}"; \
		echo "All generated maps deleted."; \
	else \
		echo "Operation cancelled."; \
	fi

.PHONY: hi build run run-interactive web present test benchmark visualize create-map create_map clear-maps

# Add your project-specific targets below.
#
# Examples:
#
#   # === Database ===
#
#   migrate:  ## Apply database migrations
#   	alembic upgrade head
#
#   seed:  ## Fill the database with sample data
#   	python scripts/seed.py
#
#   # === Training ===
#
#   train:  ## Run model training
#   	poetry run python -m src.train
#
#   evaluate:  ## Evaluate the model on the test set
#   	poetry run python -m src.evaluate
