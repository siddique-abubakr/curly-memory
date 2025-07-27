#!/usr/bin/env python3
"""
Setup script for Curly Memory documentation.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False


def main():
    """Setup documentation."""
    print("📚 Setting up Curly Memory Documentation")
    print("=" * 50)

    # Check if poetry is available
    if not run_command("poetry --version", "Checking Poetry installation"):
        print("❌ Poetry is required. Please install it first.")
        sys.exit(1)

    # Install development dependencies
    if not run_command(
        "poetry install --extras dev --no-root", "Installing development dependencies"
    ):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("📁 Creating docs directory...")
        docs_dir.mkdir()

    # Generate documentation
    if not run_command("python scripts/generate_docs.py", "Generating documentation"):
        print("❌ Failed to generate documentation")
        sys.exit(1)

    print("\n🎉 Documentation setup completed!")
    print("📖 You can now view the documentation in docs/_build/html/index.html")


if __name__ == "__main__":
    main()
