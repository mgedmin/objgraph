# release.mk version 1.3 (2018-11-03)
#
# Helpful Makefile rules for releasing Python packages.
# https://github.com/mgedmin/python-project-skel

# You might want to change these
FILE_WITH_VERSION ?= setup.py
FILE_WITH_CHANGELOG ?= CHANGES.rst
CHANGELOG_DATE_FORMAT ?= %Y-%m-%d
CHANGELOG_FORMAT ?= $(changelog_ver) ($(changelog_date))

# These should be fine
PYTHON ?= python
PYPI_PUBLISH ?= rm -rf dist && $(PYTHON) setup.py -q sdist bdist_wheel && twine check dist/* && twine upload dist/*
LATEST_RELEASE_MK_URL = https://raw.githubusercontent.com/mgedmin/python-project-skel/master/release.mk

# These should be fine, as long as you use Git
VCS_GET_LATEST ?= git pull
VCS_STATUS ?= git status --porcelain
VCS_EXPORT ?= git archive --format=tar --prefix=tmp/tree/ HEAD | tar -xf -
VCS_TAG ?= git tag -s $(changelog_ver) -m \"Release $(changelog_ver)\"
VCS_COMMIT_AND_PUSH ?= git commit -av -m "Post-release version bump" && git push && git push --tags

# These are internal implementation details
changelog_ver = `$(PYTHON) setup.py --version`
changelog_date = `LC_ALL=C date +'$(CHANGELOG_DATE_FORMAT)'`


.PHONY: dist
dist:
	$(PYTHON) setup.py -q sdist bdist_wheel

.PHONY: distcheck
distcheck: distcheck-vcs distcheck-sdist

.PHONY: distcheck-vcs
distcheck-vcs:
	# Bit of a chicken-and-egg here, but if the tree is unclean, make
	# distcheck-sdist will fail.
ifndef FORCE
	@test -z "`$(VCS_STATUS) 2>&1`" || { echo; echo "Your working tree is not clean:" 1>&2; $(VCS_STATUS) 1>&2; exit 1; }
endif

# NB: do not use $(MAKE) because then make -n distcheck will actually run
# it instead of just printing what it does

# TBH this could (and probably should) be replaced by check-manifest

.PHONY: distcheck-sdist
distcheck-sdist:
	make dist
	pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	  rm -rf tmp && \
	  mkdir tmp && \
	  $(VCS_EXPORT) && \
	  cd tmp && \
	  tar -xzf ../dist/$$pkg_and_version.tar.gz && \
	  diff -ur $$pkg_and_version tree -x PKG-INFO -x setup.cfg -x '*.egg-info' -I'^#' && \
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

# NB: do not use $(MAKE) because then make -n releasechecklist will
# actually run the distcheck instead of just printing what it does

.PHONY: releasechecklist
releasechecklist: check-latest-rules check-latest-version check-version-number check-long-description check-changelog
	make distcheck

.PHONY: release
release: releasechecklist do-release

.PHONY: do-release
do-release:
	$(release_recipe)

define release_recipe =
	# I'm chicken so I won't actually do these things yet
	@echo "Please run"
	@echo
	@echo "  $(PYPI_PUBLISH)"
	@echo "  $(VCS_TAG)"
	@echo
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  $(VCS_COMMIT_AND_PUSH)'
	@echo
endef
