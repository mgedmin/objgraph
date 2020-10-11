PYTHON = python3

FILE_WITH_VERSION = objgraph.py
FILE_WITH_CHANGELOG = CHANGES.rst

VCS_DIFF_IMAGES = git diff docs/*.png

SPHINXOPTS      =
SPHINXBUILD     = sphinx-build
SPHINXBUILDDIR  = docs/_build
ALLSPHINXOPTS   = -d $(SPHINXBUILDDIR)/doctrees $(SPHINXOPTS) docs/


.PHONY: all
all:
	@echo "Nothing to build here"

.PHONY: images
images:                         ##: regenerate graphs used in documentation
	$(PYTHON) setup.py --build-images

.PHONY: docs
docs:                           ##: build HTML documentation
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(SPHINXBUILDDIR)/html
	@echo
	@echo "Now look at $(SPHINXBUILDDIR)/html/index.html"

.PHONY: clean
clean:                          ##: remove build artifacts
	-rm -rf $(SPHINXBUILDDIR)/* build

.PHONY: test
test:                           ##: run tests
	tox -p auto

.PHONY:
check:
# 'make check' is defined in release.mk and here's how you can override it
define check_recipe =
	@$(MAKE) coverage
endef

.PHONY: coverage
coverage:                       ##: measure test coverage
	tox -e coverage2,coverage3

.PHONY: flake8
flake8:                         ##: check for style problems
	flake8

# Make sure $(VCS_DIFF_IMAGES) can work
.PHONY: config-imgdiff
config-imgdiff:
	@test -z "`git config diff.imgdiff.command`" && git config diff.imgdiff.command 'f() { imgdiff --eog -H $$1 $$2; }; f' || true

.PHONY: imgdiff
imgdiff: config-imgdiff         ##: compare differences in generated images
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
update-date:                    ##: set release date in source code to today
	sed -i -e "s/^__date__ = '.*'/__date__ = '`date +%Y-%m-%d`'/" $(FILE_WITH_VERSION)


.PHONY: do-release
do-release: config-imgdiff

# override the release recipe in release.mk
define release_recipe =
	# I'm chicken so I won't actually do these things yet
	@echo "It is a good idea to run"
	@echo
	@echo "  make clean images docs"
	@echo
	@echo "about now.  Then review the images for unexpected differences with"
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

# XXX: I should switch to readthedocs.org
.PHONY: publish-docs
publish-docs:                   ##: publish documentation on the website
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
