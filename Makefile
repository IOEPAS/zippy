.PHONY: clean data lint requirements

#################################################################################
# GLOBALS                                                                       #
#################################################################################
SHELL:=/bin/bash
CONDA=conda

PYTHON := $(shell command -v python3 2> /dev/null)
ifndef PYTHON
    $(error Python3 is not available on your system, please install python3.6)
endif

NPM := $(shell command -v npm 2> /dev/null)
ifndef NPM
    $(error npm is not available on your system, please install npm)
endif

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROFILE = default
PROJECT_NAME = zippy

TOPIC=

DATA_DIR="data"
MODELS_DIR="output/models"

FILENAME=

COLOR=\x1b[36m
NO_COLOR=\x1b[m

#################################################################################
# COMMANDS                                                                      #
#################################################################################

.PHONY: data
## Data related operations
data:
	@echo -e "${COLOR}make data:push FILENAME=<DATA_FILENAME>${NO_COLOR}\tTo push specific dataset to s3."
	@echo -e "${COLOR}make data:pull FILENAME=<DATA_FILENAME>${NO_COLOR}\tTo pull specific dataset from s3."
	@echo -e "${COLOR}make <DATA_FILENAME>${NO_COLOR}\t\t\tTo build dataset locally."
	@echo -e "\nFollowing files are available:"
	@echo -e "$$(egrep '^(data/.+)\:' ${MAKEFILE_LIST} | sed -e 's/:.*\s*/:/' -e 's/^\(.\+\):\(.*\)/\t\${COLOR}\1\${NO_COLOR}\2/')"

.PHONY: data\:push
data\:push:
ifndef FILENAME
	$(info Missing FILENAME argument)
	$(error Usage: "make data:push FILENAME=path/to/the/file")
else
	$(info TODO command. Pushes the ${FILENAME} to the s3.)
endif

.PHONY: data\:pull
data\:pull:
ifndef FILENAME
	$(info Missing FILENAME argument)
	$(error Usage: "make data:pull FILENAME=path/to/the/file")
else
	$(info TODO command. Pulls the ${FILENAME} from the s3.)
endif

# Data pipelines
data/raw/emails.csv:
	kaggle datasets download -d wcukierski/enron-email-dataset --path $(shell dirname $@) --unzip


.PHONY: models
## Models related operations
models:
	@echo -e "${COLOR}make models:push FILENAME=<MODEL_FILENAME>${NO_COLOR}\tTo push specific model to s3."
	@echo -e "${COLOR}make models:pull FILENAME=<MODEL_FILENAME>${NO_COLOR}\tTo pull specific model from s3."
	@echo -e "${COLOR}make <MODEL_FILENAME>${NO_COLOR}\t\t\tTo train model locally."
	@echo -e "\nFollowing files are available:"
	@echo -e "$$(egrep '^(output/models/.+)\:' ${MAKEFILE_LIST} | sed -e 's/:.*\s*/:/' -e 's/^\(.\+\):\(.*\)/\t\\x1b[36m\1\\x1b[m\2/')"

.PHONY: models\:push
models\:push:
ifndef FILENAME
	$(info Missing FILENAME argument)
	$(error Usage: "make models:push FILENAME=path/to/the/file")
else
	$(info TODO command. Pushes the ${FILENAME} to the s3.)
endif

.PHONY: models\:pull
models\:pull:
ifndef FILENAME
	$(info Missing FILENAME argument)
	$(error Usage: "make models:pull FILENAME=path/to/the/file")
else
	$(info TODO command. Pulls the ${FILENAME} from the s3.)
endif

# model pipelines

#################################################################################

.PHONY: clean
## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

.PHONY: lint
## Lint using flake8
lint:
	@echo -e "Use ${COLOR}make lint:fix${NO_COLOR} to fix linter issues. \n"
	$(PYTHON) -m isort -c --diff
	$(PYTHON) -m black . --check --diff
	$(PYTHON) -m pylint src/pipeline src/server src/utils tests scripts

.PHONY: lint\:fix
lint\:fix:
	$(PYTHON) -m isort -y
	$(PYTHON) -m black .

.PHONY: notebook
## Create notebook
notebook:
ifndef TOPIC
	$(info Missing TOPIC argument)
	$(error Usage: "make notebook TOPIC=<topic>")
else
	$(PYTHON) scripts/utils.py create_nb $(TOPIC)
endif

.PHONY: run
## Run jupyter notebook
run:
	$(PYTHON) -m jupyter lab

.PHONY: docs
## Make docs
docs:
	cd docs && make html

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################




#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
## Show this help message
help:
	@echo -e "Usage:\n\tmake <target>\n"
	@echo "$$(tput bold)Available targets:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
	@echo -e $$(echo "version commit@" && git rev-parse --short HEAD)
