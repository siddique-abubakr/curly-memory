#!/usr/bin/env python3
"""
Script to generate documentation for Curly Memory.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, check=True, capture_output=True, text=True
        )
        print(f"✅ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return None


def main():
    """Generate documentation."""
    # Get project root
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    print("📚 Generating Curly Memory Documentation")
    print("=" * 50)

    # Check if we're in the right directory
    if not docs_dir.exists():
        print(f"❌ Documentation directory not found: {docs_dir}")
        sys.exit(1)

    # Change to docs directory
    os.chdir(docs_dir)

    # Clean previous build
    print("🧹 Cleaning previous build...")
    run_command("make clean")

    # Generate HTML documentation
    print("🔨 Building HTML documentation...")
    result = run_command("make html")

    if result is None:
        print("❌ Documentation generation failed!")
        sys.exit(1)

    # Check if build was successful
    html_dir = docs_dir / "_build" / "html"
    index_file = html_dir / "index.html"

    if index_file.exists():
        print("✅ Documentation generated successfully!")
        print(f"📁 Location: {html_dir}")
        print(f"🌐 Open: {index_file}")

        # Try to open in browser
        try:
            import webbrowser

            webbrowser.open(f"file://{index_file.absolute()}")
            print("🌐 Opened documentation in browser")
        except Exception:
            print("💡 To view documentation, open the index.html file in your browser")
    else:
        print("❌ Documentation generation failed - index.html not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
