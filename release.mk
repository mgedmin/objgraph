# release.mk version 2.1 (2021-04-19)
#
# Helpful Makefile rules for releasing Python packages.
# https://github.com/mgedmin/python-project-skel

# You might want to change these
FILE_WITH_VERSION ?= setup.py
FILE_WITH_CHANGELOG ?= CHANGES.rst
CHANGELOG_DATE_FORMAT ?= %Y-%m-%d
CHANGELOG_FORMAT ?= $(changelog_ver) ($(changelog_date))
DISTCHECK_DIFF_OPTS ?= $(DISTCHECK_DIFF_DEFAULT_OPTS)

# These should be fine
PYTHON ?= python3
PYPI_PUBLISH ?= rm -rf dist && $(PYTHON) setup.py -q sdist bdist_wheel && twine check dist/* && twine upload dist/*
LATEST_RELEASE_MK_URL = https://raw.githubusercontent.com/mgedmin/python-project-skel/master/release.mk
DISTCHECK_DIFF_DEFAULT_OPTS = -x PKG-INFO -x setup.cfg -x '*.egg-info' -x .github -I'^\#'

# These should be fine, as long as you use Git
VCS_GET_LATEST ?= git pull
VCS_STATUS ?= git status --porcelain
VCS_EXPORT ?= git archive --format=tar --prefix=tmp/tree/ HEAD | tar -xf -
VCS_TAG ?= git tag -s $(changelog_ver) -m \"Release $(changelog_ver)\"
VCS_COMMIT_AND_PUSH ?= git commit -av -m "Post-release version bump" && git push && git push --tags

# These are internal implementation details
changelog_ver = `$(PYTHON) setup.py --version`
changelog_date = `LC_ALL=C date +'$(CHANGELOG_DATE_FORMAT)'`

# Tweaking the look of 'make help'; most of these are awk literals and need the quotes
HELP_INDENT = ""
HELP_PREFIX = "make "
HELP_WIDTH = 24
HELP_SEPARATOR = " \# "
HELP_SECTION_SEP = "\n"

.PHONY: help
help:
	@grep -Eh -e '^[a-zA-Z0-9_ -]+:.*?##: .*$$' -e '^##:' $(MAKEFILE_LIST) \
	    | awk 'BEGIN {FS = "(^|:[^#]*)##: "; section=""}; \
	          /^##:/ {printf "%s%s\n%s", section, $$2, $(HELP_SECTION_SEP); section=$(HELP_SECTION_SEP)} \
	          /^[^#]/ {printf "%s\033[36m%-$(HELP_WIDTH)s\033[0m%s%s\n", \
	                   $(HELP_INDENT), $(HELP_PREFIX) $$1, $(HELP_SEPARATOR), $$2}'

.PHONY: dist
dist:
	$(PYTHON) setup.py -q sdist bdist_wheel

# Provide a default 'make check' to be the same as 'make test', since that's
# what 80% of my projects use, but make it possible to override.  Now
# overriding Make rules is painful, so instead of a regular rule definition
# you'll have to override the check_recipe macro.
.PHONY: check
check:
	$(check_recipe)

ifndef check_recipe
define check_recipe =
	@$(MAKE) test
endef
endif

.PHONY: distcheck
distcheck: distcheck-vcs distcheck-sdist

.PHONY: distcheck-vcs
distcheck-vcs:
ifndef FORCE
	# Bit of a chicken-and-egg here, but if the tree is unclean, make
	# distcheck-sdist will fail.
	@test -z "`$(VCS_STATUS) 2>&1`" || { echo; echo "Your working tree is not clean:" 1>&2; $(VCS_STATUS) 1>&2; exit 1; }
endif

# NB: do not use $(MAKE) in rules with multiple shell commands joined by &&
# because then make -n distcheck will actually run those instead of just
# printing what it does

# TBH this could (and probably should) be replaced by check-manifest

.PHONY: distcheck-sdist
distcheck-sdist: dist
	pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	  rm -rf tmp && \
	  mkdir tmp && \
	  $(VCS_EXPORT) && \
	  cd tmp && \
	  tar -xzf ../dist/$$pkg_and_version.tar.gz && \
	  diff -ur $$pkg_and_version tree $(DISTCHECK_DIFF_OPTS) && \
	  cd $$pkg_and_version && \
	  make dist check && \
	  cd .. && \
	  mkdir one two && \
	  cd one && \
	  tar -xzf ../../dist/$$pkg_and_version.tar.gz && \
	  cd ../two/ && \
	  tar -xzf ../$$pkg_and_version/dist/$$pkg_and_version.tar.gz && \
	  cd .. && \
	  diff -ur one two -x SOURCES.txt -I'^#:' && \
	  cd .. && \
	  rm -rf tmp && \
	  echo "sdist seems to be ok"

.PHONY: check-latest-rules
check-latest-rules:
ifndef FORCE
	@curl -s $(LATEST_RELEASE_MK_URL) | cmp -s release.mk || { printf "\nYour release.mk does not match the latest version at\n$(LATEST_RELEASE_MK_URL)\n\n" 1>&2; exit 1; }
endif

.PHONY: check-latest-version
check-latest-version:
	$(VCS_GET_LATEST)

.PHONY: check-version-number
check-version-number:
	@$(PYTHON) setup.py --version | grep -qv dev || { \
	    echo "Please remove the 'dev' suffix from the version number in $(FILE_WITH_VERSION)"; exit 1; }

.PHONY: check-long-description
check-long-description:
	@$(PYTHON) setup.py --long-description | rst2html --exit-status=2 > /dev/null

.PHONY: check-changelog
check-changelog:
	@ver_and_date="$(CHANGELOG_FORMAT)" && \
	    grep -q "^$$ver_and_date$$" $(FILE_WITH_CHANGELOG) || { \
	        echo "$(FILE_WITH_CHANGELOG) has no entry for $$ver_and_date"; exit 1; }


# NB: the Makefile that includes release.mk may want to add additional
# dependencies to the releasechecklist target, but I want 'make distcheck' to
# happen last, so that's why I put it into the recipe and not at the end of the
# list of dependencies.

.PHONY: releasechecklist
releasechecklist: check-latest-rules check-latest-version check-version-number check-long-description check-changelog
	$(MAKE) distcheck

.PHONY: release
release: releasechecklist do-release    ##: prepare a new PyPI release

.PHONY: do-release
do-release:
	$(release_recipe)

define default_release_recipe_publish_and_tag =
	# I'm chicken so I won't actually do these things yet
	@echo "Please run"
	@echo
	@echo "  $(PYPI_PUBLISH)"
	@echo "  $(VCS_TAG)"
	@echo
endef
define default_release_recipe_increment_and_push =
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  $(VCS_COMMIT_AND_PUSH)'
	@echo
endef
ifndef release_recipe
define release_recipe =
$(default_release_recipe_publish_and_tag)
$(default_release_recipe_increment_and_push)
endef
endif
