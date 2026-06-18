.PHONY: install-hooks test build clean

install-hooks:
	@sh scripts/install-hooks.sh

install-hooks-force:
	@sh scripts/install-hooks.sh --force

test:
	python -m unittest discover -s tests -p "test_*.py" -v

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info/ .impact_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
