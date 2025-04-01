from setuptools import setup, find_packages

setup(
    name='masto',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'requests',
        'tqdm',
        'w3lib',
        'beautifulsoup4'
    ],
)
