from setuptools import setup, find_packages

setup(
    name="quilt-fleet-snapshot",
    version="0.1.0",
    description="Bake the Quilt fleet state into a portable tarball. Solves the wipe problem.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
)
