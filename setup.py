from setuptools import setup

with open("requirements.txt") as f:
  install_requires = f.read().splitlines()

setup(
  name="netgear-telenetenable",
  version="0.1.0",
  author="Paul Gebheim <pgebheim@gmail.com>",
  description="Telenet Enable for Netgear routers",
  install_requires=install_requires,
  scripts=[
    "telnetenable.py",
  ],
)
