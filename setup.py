from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pavone",
    version="0.1.0",
    author="PAVOne Team",
    description="一个集下载,整理等多功能的插件化的AV管理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",    install_requires=[
        "requests",
        "beautifulsoup4",
        "click",
        "tqdm",
        "configparser",
        "pillow",
        "lxml",
        "dukpy>=0.5.0",
    ],
    entry_points={
        "console_scripts": [
            "pavone=pavone.cli:main",
        ],
    },
)
