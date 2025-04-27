from setuptools import setup, find_packages

setup(
    name="study_coach",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "discord.py",
        "python-dotenv",
        "pymongo==4.6.1",
        "motor==3.3.2",
        "pdfminer.six",
        "httpx",
        "matplotlib",
        "numpy"
    ]
)
