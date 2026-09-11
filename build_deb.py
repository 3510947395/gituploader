#!/usr/bin/env python3
"""Build a standalone Debian package for Debian or Termux."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_package(output_dir: Path, prefix: str) -> Path:
    project_root = Path(__file__).parent
    version = "1.0.0"
    package_root = output_dir / f"gituploader_{version}_all"
    if package_root.exists():
        shutil.rmtree(package_root)

    python_dir = package_root / prefix.lstrip("/") / "lib" / (
        f"python{sys.version_info.major}.{sys.version_info.minor}"
    ) / "site-packages"
    bin_dir = package_root / prefix.lstrip("/") / "bin"
    debian_dir = package_root / "DEBIAN"
    python_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    debian_dir.mkdir(parents=True)

    shutil.copy2(project_root / "src" / "gitup.py", python_dir / "gitup.py")
    wrapper = "#!/bin/sh\nexec python3 -m gitup \"$@\"\n"
    (bin_dir / "gitup").write_text(wrapper, encoding="utf-8")
    (bin_dir / "gitup").chmod(0o755)
    control = "\n".join([
        "Package: gituploader",
        f"Version: {version}",
        "Section: utils",
        "Priority: optional",
        "Architecture: all",
        "Depends: python3",
        "Maintainer: GitUploader Team <team@gituploader.com>",
        "Description: Git upload command generator",
        " Stores reusable Git upload commands and expands runtime placeholders.",
        "",
    ])
    (debian_dir / "control").write_text(control, encoding="utf-8")

    package_file = output_dir / f"gituploader_{version}_all.deb"
    subprocess.run(["dpkg-deb", "--build", str(package_root), str(package_file)], check=True)
    return package_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the GitUploader .deb package")
    parser.add_argument("--output", default="dist", help="输出目录")
    parser.add_argument(
        "--prefix",
        default=os.environ.get("PREFIX", "/usr"),
        help="安装前缀，Termux 中通常来自 PREFIX 环境变量",
    )
    args = parser.parse_args()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    package_file = build_package(output_dir, args.prefix)
    print(f"已生成: {package_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())