PYTHON = python

FILE_WITH_VERSION = objgraph.py
FILE_WITH_CHANGELOG = CHANGES.rst
VCS_STATUS = git status --porcelain
VCS_EXPORT = git archive --format=tar --prefix=tmp/tree/ HEAD | tar -xf -
VCS_DIFF_IMAGES = git diff docs/*.png
VCS_TAG = git tag
VCS_COMMIT_AND_PUSH = git commit -av -m "Post-release version bump" && git push && git push --tags

SUPPORTED_PYTHON_VERSIONS = 2.4 2.5 2.6 2.7 3.1 3.2 3.3 3.4

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
BUILDDIR      = docs/_build
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(SPHINXOPTS) docs/


.PHONY: default
default:
	@echo "Nothing to build here"

.PHONY: images
images:
	$(PYTHON) setup.py --build-images

.PHONY: docs
docs:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Now look at $(BUILDDIR)/html/index.html"

.PHONY: clean
clean:
	-rm -rf $(BUILDDIR)/*

.PHONY: test check
test check:
	$(PYTHON) tests.py

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
	restview -e "$(PYTHON) setup.py --long-description"

.PHONY: coverage
coverage:
	PYTHONPATH=.:$$PYTHONPATH coverage run --source=objgraph tests.py
	coverage report

.PHONY: dist
dist:
	$(PYTHON) setup.py sdist

.PHONY: distcheck
distcheck:
	# Bit of a chicken-and-egg here, but if the tree is unclean, make
	# distcheck will fail.
	@test -z "`$(VCS_STATUS) 2>&1`" || { echo; echo "Your working tree is not clean" 1>&2; $(VCS_STATUS); exit 1; }
	make dist
	pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	rm -rf tmp && \
	mkdir tmp && \
	$(VCS_EXPORT) && \
	cd tmp && \
	tar xvzf ../dist/$$pkg_and_version.tar.gz && \
	diff -ur $$pkg_and_version tree -x PKG-INFO -x setup.cfg -x '*.egg-info' && \
	cd $$pkg_and_version && \
	make dist check && \
	cd .. && \
	mkdir one two && \
	cd one && \
	tar xvzf ../../dist/$$pkg_and_version.tar.gz && \
	cd ../two/ && \
	tar xvzf ../$$pkg_and_version/dist/$$pkg_and_version.tar.gz && \
	cd .. && \
	diff -ur one two -x SOURCES.txt && \
	cd .. && \
	rm -rf tmp && \
	echo "sdist seems to be ok"

.PHONY: releasechecklist
releasechecklist:
	@$(PYTHON) setup.py --version | grep -qv dev || { \
	    echo "Please remove the 'dev' suffix from the version number in $(FILE_WITH_VERSION)"; exit 1; }
	@$(PYTHON) setup.py --long-description | rst2html --exit-status=2 > /dev/null
	@ver_and_date="`$(PYTHON) setup.py --version` (`date +%Y-%m-%d`)" && \
	    grep -q "^$$ver_and_date$$" $(FILE_WITH_CHANGELOG) || { \
	        echo "$(FILE_WITH_CHANGELOG) has no entry for $$ver_and_date"; exit 1; }
	make distcheck

# Make sure $(VCS_DIFF_IMAGES) can work
.PHONY: config-imgdiff
config-imgdiff:
	@test -z "`git config diff.imgdiff.command`" && git config diff.imgdiff.command 'f() { imgdiff --eog -H $$1 $$2; }; f' || true

.PHONY: imgdiff
imgdiff: config-imgdiff
	$(VCS_DIFF_IMAGES)

.PHONY: release
release: releasechecklist config-imgdiff
	# I'm chicken so I won't actually do these things yet
	@echo "It is a good idea to run"
	@echo
	@echo "  make test-all-pythons"
	@echo "  make clean images docs"
	@echo
	@echo "about now.  Then sanity-check the images with"
	@echo
	@echo "  $(VCS_DIFF_IMAGES)"
	@echo
	@echo "then either revert or commit the new images and run"
	@echo
	@echo "  $(PYTHON) setup.py sdist register upload --unicode-description && $(VCS_TAG) `$(PYTHON) setup.py --version`"
	@echo "  make publish-docs"
	@echo
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  $(VCS_COMMIT_AND_PUSH)'
	@echo

.PHONY: publish-docs
publish-docs:
	test -d ~/www/objgraph || { \
	    echo "There's no ~/www/objgraph, do you have the website checked out?"; exit 1; }
	make clean docs
	cp -r docs/_build/html/* ~/www/objgraph/
	svn add ~/www/objgraph/*.html ~/www/objgraph/_images/*.png ~/www/objgraph/_sources/* ~/www/objgraph/_static/* 2>/dev/null
	svn st ~/www/objgraph/
	@echo
	@echo "If everything looks fine, please run"
	@echo
	@echo "  svn ci ~/www/objgraph/ -m \"Released objgraph `$(PYTHON) setup.py --version`\""
	@echo

