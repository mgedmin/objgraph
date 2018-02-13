PYTHON = python

FILE_WITH_VERSION = objgraph.py
FILE_WITH_CHANGELOG = CHANGES.rst

VCS_DIFF_IMAGES = git diff docs/*.png

SUPPORTED_PYTHON_VERSIONS = 2.7 3.3 3.4 3.5 3.6

SPHINXOPTS      =
SPHINXBUILD     = sphinx-build
SPHINXBUILDDIR  = docs/_build
ALLSPHINXOPTS   = -d $(SPHINXBUILDDIR)/doctrees $(SPHINXOPTS) docs/


.PHONY: default
default:
	@echo "Nothing to build here"

.PHONY: images
images:
	$(PYTHON) setup.py --build-images

.PHONY: docs
docs:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(SPHINXBUILDDIR)/html
	@echo
	@echo "Now look at $(SPHINXBUILDDIR)/html/index.html"

.PHONY: clean
clean:
	-rm -rf $(SPHINXBUILDDIR)/* build

.PHONY: test
test:
	$(PYTHON) tests.py

.PHONY:
check: coverage

.PHONY: test-all-pythons
test-all-pythons:
	set -e; \
	for ver in $(SUPPORTED_PYTHON_VERSIONS); do \
		if which python$$ver > /dev/null; then \
			$(MAKE) test PYTHON=python$$ver; \
		else \
			echo "=================================="; \
			echo "Skipping python$$ver, not available."; \
			echo "=================================="; \
		fi; \
	done

.PHONY: preview-pypi-description
preview-pypi-description:
	# pip install restview, if missing
	restview --long-description

.PHONY: coverage
coverage:
	coverage run --source=objgraph tests.py
	python3 -m coverage run -a --source=objgraph tests.py
	coverage report -m --fail-under=100

.PHONY: lint
lint:
	flake8 --exclude=build,docs/conf.py --ignore=E226
	flake8 --exclude=build,docs/conf.py --doctests --ignore=E226,F821

# Make sure $(VCS_DIFF_IMAGES) can work
.PHONY: config-imgdiff
config-imgdiff:
	@test -z "`git config diff.imgdiff.command`" && git config diff.imgdiff.command 'f() { imgdiff --eog -H $$1 $$2; }; f' || true

.PHONY: imgdiff
imgdiff: config-imgdiff
	$(VCS_DIFF_IMAGES)


.PHONY: releasechecklist
releasechecklist: check-date  # also release.mk will add other checks

include release.mk

.PHONY: check-date
check-date:
	@date_line="__date__ = '`date +%Y-%m-%d`'" && \
	    grep -q "^$$date_line$$" $(FILE_WITH_VERSION) || { \
	        echo "$(FILE_WITH_VERSION) doesn't specify $$date_line"; \
	        echo "Please run make update-date"; exit 1; }

.PHONY: update-date
update-date:
	sed -i -e "s/^__date__ = '.*'/__date__ = '`date +%Y-%m-%d`'/" $(FILE_WITH_VERSION)


.PHONY: do-release
do-release: config-imgdiff

define release_recipe =
	# I'm chicken so I won't actually do these things yet
	@echo "It is a good idea to run"
	@echo
	@echo "  make test-all-pythons"
	@echo "  make clean images docs"
	@echo
	@echo "about now.  Then sanity-check the images with"
	@echo
	@echo "  make imgdiff"
	@echo
	@echo "then either revert or commit the new images and run"
	@echo
	@echo "  $(PYPI_PUBLISH)"
	@echo "  $(VCS_TAG)"
	@echo "  make publish-docs"
	@echo
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  $(VCS_COMMIT_AND_PUSH)'
	@echo
endef

.PHONY: publish-docs
publish-docs:
	test -d ~/www/objgraph || { \
	    echo "There's no ~/www/objgraph, do you have the website checked out?"; exit 1; }
	make clean docs
	cp -r docs/_build/html/* ~/www/objgraph/
	cd ~/www/objgraph && git add . && git status
	@echo
	@echo "If everything looks fine, please run"
	@echo
	@echo "  cd ~/www/ && git commit -m \"Released objgraph `$(PYTHON) setup.py --version`\" && git push"
	@echo "  ssh fridge 'cd www && git pull'"
	@echo

