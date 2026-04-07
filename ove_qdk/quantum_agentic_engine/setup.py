#!/usr/bin/env python3
"""
Setup script for Quantum Agentic Loop Engine
QDK (Q#) Based Autonomous Agent System
"""

from setuptools import setup, find_packages
from pathlib import Path
import os

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
def read_requirements():
    requirements_path = Path(__file__).parent / "requirements.txt"
    with open(requirements_path, "r") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

# Version
VERSION = "1.0.0"

setup(
    name="quantum-agentic-loop-engine",
    version=VERSION,
    author="Quantum Agentic Engine Team",
    author_email="contact@quantum-agentic-engine.org",
    description="Advanced Quantum-Classical Hybrid Autonomous Agent System using QDK (Q#)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quantum-agentic-engine/qale",
    project_urls={
        "Bug Reports": "https://github.com/quantum-agentic-engine/qale/issues",
        "Source": "https://github.com/quantum-agentic-engine/qale",
        "Documentation": "https://quantum-agentic-engine.readthedocs.io",
    },
    packages=find_packages(where="src/python"),
    package_dir={"": "src/python"},
    include_package_data=True,
    package_data={
        "": ["*.qs", "*.json", "*.yaml", "*.yml"],
    },
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=2.0.0",
        ],
        "quantum": [
            "qiskit>=0.43.0",
            "cirq>=1.2.0",
            "pennylane>=0.31.0",
        ],
        "cloud": [
            "boto3>=1.28.0",
            "azure-identity>=1.13.0",
            "google-cloud-storage>=2.10.0",
        ],
        "all": [
            "pytest>=7.4.0",
            "black>=23.3.0",
            "sphinx>=7.0.0",
            "qiskit>=0.43.0",
            "boto3>=1.28.0",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Q#",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "quantum computing",
        "reinforcement learning",
        "autonomous agents",
        "QDK",
        "Q#",
        "quantum machine learning",
        "variational quantum circuits",
        "multi-agent systems",
        "quantum error correction",
    ],
    entry_points={
        "console_scripts": [
            "qale=main:main",
            "quantum-agent=main:main",
        ],
    },
    zip_safe=False,
)
