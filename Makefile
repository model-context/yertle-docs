# Path to the sibling backend repo where the OpenAPI spec is generated from.
# Override with `make openapi BACKEND=/some/other/path` if needed.
BACKEND ?= ../yertle/backend

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32mmake %-10s\033[0m %s\n", $$1, $$2}'

dev: ## Start the Mintlify dev server (hot reload at http://localhost:3000)
	mintlify dev

audit: ## Compare openapi.json vs docs.json — show exposed / hidden / broken endpoints
	@python3 scripts/audit_docs.py

openapi: ## Regenerate openapi.json from the backend FastAPI app
	cd $(BACKEND) && pipenv run python3 scripts/export_openapi.py --output $(CURDIR)/openapi.json

install: ## Install the Mintlify CLI globally (one-time setup)
	npm i -g mintlify

check: ## Validate docs.json is well-formed JSON
	@python3 -c "import json; json.load(open('docs.json')); print('docs.json: OK')"
