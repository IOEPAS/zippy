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

WGET := $(shell command -v wget 2> /dev/null)
ifndef WGET
    $(error Wget is not installed on your system, please install wget.)
endif

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROFILE = default
PROJECT_NAME = zippy
PROJECT_VERSION=v1.0.0-alpha

TOPIC=

DATA_DIR="data"
MODELS_DIR="output/models"

FILENAME=

TEST_ARGS=--reruns 3
TEST_ON_DOVECOT=
COVERAGE?=
COV_ARGS?=

ifeq ($(COVERAGE), true)
    COV_ARGS+=--cov=./
endif


COLOR=\x1b[36m
NO_COLOR=\x1b[m

#################################################################################
# COMMANDS                                                                      #
#################################################################################

.PHONY: data
## List available datasets
data:
	@echo -e "${COLOR}make <DATA_FILENAME>${NO_COLOR}\t\t\tTo build dataset locally."
	@echo -e "\nFollowing files are available:"
	@echo -e "$$(egrep '^(data/.+)\:' ${MAKEFILE_LIST} | sed -e 's/:.*\s*/:/' -e 's/^\(.\+\):\(.*\)/\t\${COLOR}\1\${NO_COLOR}\2/')"

.PHONY: data\:push
data\:push:
ifndef FILENAME
	$(info Missing FILENAME argument)
	$(error Usage: "make data:push FILENAME=path/to/the/file")
else
	$(PYTHON) scripts/utils.py push $(FILENAME)
endif

.PHONY: data\:pull
data\:pull:
ifndef FILENAME
	$(info Missing FILENAME argument)
	$(error Usage: "make data:pull FILENAME=path/to/the/file")
else
	$(PYTHON) scripts/utils.py pull $(FILENAME)
endif

# Data pipelines
data/raw/emails.csv:
	kaggle datasets download -d wcukierski/enron-email-dataset --path $(shell dirname $@) --unzip

data/raw/enron-dataset-clean-v1.pkl:
	@echo "Not implemented yet"

data/raw/emails-processed.pkl:
	@echo "Not implemented yet"

data/raw/bc3:
	@echo "Not implemented yet"

.PHONY: models
## Models related operations
models:
	@echo -e "${COLOR}make models:push FILENAME=<MODEL_FILENAME>${NO_COLOR} To push specific model to Azure (Server down at the moment)."
	@echo -e "${COLOR}make models:pull ${NO_COLOR}\tTo pull all the models from Github release."

.PHONY: models\:push
models\:push:
	@echo "Pushing model does not work, as the server is currently down."
	@echo "Please upload models in github releases instead."
ifdef FILENAME
	$(PYTHON) scripts/utils.py push ${FILENAME}
else
	@echo "If you want to, you can try using the following command:"
	@echo -e "\t${COLOR}$(PYTHON) scripts/utils.py push <FILENAME_PATH_TO_PUSH>${NO_COLOR}"
endif

.PHONY: models\:pull
models\:pull:
	$(WGET) https://github.com/IOEPAS/zippy/releases/download/${PROJECT_VERSION}/models.tar.xz -O ${MODELS_DIR}/models.tar.xz
	@test -f  ${MODELS_DIR}/models.tar.xz || { echo "Could not find the downloaded file. Exiting..."; exit 1; }
	tar -xvf ${MODELS_DIR}/models.tar.xz -C ${MODELS_DIR}
	rm -f ${MODELS_DIR}/models.tar.xz

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
	$(PYTHON) -m pylint zippy/pipeline zippy/server zippy/utils zippy/client tests scripts
	$(PYTHON) -m flake8
	$(PYTHON) -m pydocstyle zippy/pipeline zippy/server zippy/utils zippy/client tests scripts

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

.PHONY: log-server
## Run logger
log-server:
	$(PYTHON) scripts/json_server.py

.PHONY: docs
## Make docs
docs:
	# Sphinx searches in _static dir for static files
	# Create one if it doesnot exist.
	mkdir -p docs/_static
	cd docs && make html SPHINXOPTS=-W

.PHONY: test
## Run tests
test:
	$(PYTHON) -m pytest $(COV_ARGS) $(TEST_ARGS)

.PHONY: type-check
## Run mypy for typecheck
type-check:
	$(PYTHON) -m mypy zippy/**/*.py tests/*py scripts/*py

.PHONY: package
## Make zippy available as a package
package:
	$(PYTHON) -m pip install -e . --no-use-pep517

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
