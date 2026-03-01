#!/usr/bin/env python3
"""
Run all newsletter scrapers
This script orchestrates all scraper modules
"""

import sys
import importlib.util
from pathlib import Path


def run_scraper(scraper_path):
    """Run a single scraper module"""
    scraper_name = scraper_path.stem

    try:
        print(f"\n{'='*60}")
        print(f"Running {scraper_name}...")
        print(f"{'='*60}")

        # Import and run the scraper module
        spec = importlib.util.spec_from_file_location(scraper_name, scraper_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Run the main function
        if hasattr(module, 'main'):
            module.main()
        else:
            print(f"⚠ {scraper_name} has no main() function")

        print(f"✓ Completed {scraper_name}")
        return True

    except Exception as e:
        print(f"✗ Error running {scraper_name}: {e}")
        return False


def main():
    """Run all scrapers in the scrapers directory"""
    print("Starting RSS Feed Generator")
    print(f"{'='*60}\n")

    # Get all Python files in scrapers directory
    scrapers_dir = Path(__file__).parent / 'scrapers'
    scraper_files = sorted(scrapers_dir.glob('*.py'))

    if not scraper_files:
        print("⚠ No scraper files found in scrapers/")
        sys.exit(1)

    # Run each scraper
    results = {}
    for scraper_file in scraper_files:
        success = run_scraper(scraper_file)
        results[scraper_file.stem] = success

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    successful = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")

    print(f"\n{successful}/{total} scrapers completed successfully")

    if successful < total:
        sys.exit(1)


if __name__ == '__main__':
    main()
