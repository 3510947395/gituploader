#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""GitUploader 安装脚本"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="gituploader",
    version="1.0.9",
    author="GitUploader Team",
    author_email="contact@gituploader.com",
    description="Git上传命令生成工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gituploader/gituploader",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        # 无外部依赖，仅使用标准库
    ],
    entry_points={
        "console_scripts": [
            "gitup=gitup:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
