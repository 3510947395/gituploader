#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitUploader - Git上传命令生成工具
用于生成和管理git上传命令的模板
"""

import argparse
import os
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class GitUploader:
    def __init__(self, config_dir: str = "~/.gituploader"):
        self.CONFIG_DIR = str(Path(config_dir).expanduser())
        self.CONFIG_FILE = str(Path(self.CONFIG_DIR) / "config.json")
        self.TEMPLATES_DIR = str(Path(self.CONFIG_DIR) / "templates")

    @property
    def repos_dir(self) -> Path:
        path = Path(self.CONFIG_DIR).expanduser() / "repos"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _valid_name(name: str) -> bool:
        return bool(name) and name not in {".", ".."} and Path(name).name == name

    def _config_path(self, repo_name: str) -> Path:
        return self.repos_dir / repo_name / "config.json"

    def _read_repo(self, repo_name: str) -> Optional[Dict]:
        config_file = self._config_path(repo_name)
        if not config_file.is_file():
            return None
        try:
            with config_file.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError):
            return None

    def _write_repo(self, repo_name: str, config: Dict) -> None:
        with self._config_path(repo_name).open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=2, ensure_ascii=False)
    
    def create_repo(self, name: str) -> bool:
        """创建新的仓库"""
        if not self._valid_name(name):
            print("仓库名称无效")
            return False
        repo_path = self.repos_dir / name
        if repo_path.exists():
            print(f"仓库 '{name}' 已存在")
            return False
        
        repo_path.mkdir()
        self._write_repo(name, {"name": name, "templates": {}})
        
        print(f"仓库 '{name}' 创建成功")
        return True
    
    def list_repos(self) -> List[str]:
        """列出所有仓库"""
        repos = [p.name for p in self.repos_dir.iterdir() if p.is_dir()]
        return repos
    
    def add_template(self, repo_name: str, template_name: str, command: str) -> bool:
        """为仓库添加模板"""
        if not self._valid_name(template_name) or not command.strip():
            print("模板名称或命令无效")
            return False
        config = self._read_repo(repo_name)
        if config is None:
            print(f"仓库 '{repo_name}' 不存在")
            return False
        
        if template_name in config["templates"]:
            print(f"模板 '{template_name}' 已存在")
            return False
        
        config["templates"][template_name] = command
        self._write_repo(repo_name, config)
        
        print(f"模板 '{template_name}' 添加成功")
        return True

    def list_templates(self, repo_name: str) -> Dict[str, str]:
        """返回仓库中的模板及其原始命令。"""
        config = self._read_repo(repo_name)
        if config is None:
            return {}
        return dict(config.get("templates", {}))

    def generate_template(self, repo_name: str, template_name: str) -> Optional[str]:
        """生成替换实时占位符后的命令，但不执行。"""
        templates = self.list_templates(repo_name)
        if template_name not in templates:
            return None
        return self._replace_placeholders(templates[template_name])
    
    def run_template(self, repo_name: str, template_name: str) -> bool:
        """运行模板命令"""
        command = self.generate_template(repo_name, template_name)
        if command is None:
            if self._read_repo(repo_name) is None:
                print(f"仓库 '{repo_name}' 不存在")
            else:
                print(f"模板 '{template_name}' 不存在")
            return False

        repo_path = self.repos_dir / repo_name
        
        print(f"执行命令: {command}")
        try:
            subprocess.run(command, shell=True, check=True, cwd=repo_path)
            print("命令执行成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {e}")
            return False
    
    def _replace_placeholders(self, command: str) -> str:
        """替换命令中的占位符"""
        now = datetime.now()
        placeholders = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "timestamp": now.strftime("%Y%m%d%H%M%S"),
            "username": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
            "hostname": os.getenv("HOSTNAME") or os.getenv("COMPUTERNAME", "unknown"),
        }
        command = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}",
                         lambda match: placeholders.get(match.group(1), match.group(0)), command)
        legacy = {
            "%Y-%m-%d": placeholders["date"],
            "%H:%M:%S": placeholders["time"],
            "%username": placeholders["username"],
            "%hostname": placeholders["hostname"],
        }
        for placeholder, value in legacy.items():
            command = command.replace(placeholder, value)
        return command

def main():
    parser = argparse.ArgumentParser(description="GitUploader - Git上传命令生成工具")
    parser.add_argument("--version", action="version", version="gituploader 1.0.0")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # repo 命令
    repo_parser = subparsers.add_parser("repo", help="仓库管理")
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command")
    
    # repo create
    create_parser = repo_subparsers.add_parser("create", help="创建仓库")
    create_parser.add_argument("name", help="仓库名称")
    
    # repo list
    repo_subparsers.add_parser("list", help="列出仓库")
    
    # template 命令
    template_parser = subparsers.add_parser("template", help="模板管理")
    template_subparsers = template_parser.add_subparsers(dest="template_command")
    
    # template add
    add_parser = template_subparsers.add_parser("add", help="添加模板")
    add_parser.add_argument("repo_name", help="仓库名称")
    add_parser.add_argument("template_name", help="模板名称")
    add_parser.add_argument("command", help="命令模板")

    list_templates_parser = template_subparsers.add_parser("list", help="列出仓库模板")
    list_templates_parser.add_argument("repo_name", help="仓库名称")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行模板")
    run_parser.add_argument("repo_name", help="仓库名称")
    run_parser.add_argument("template_name", help="模板名称")

    # generate 命令
    generate_parser = subparsers.add_parser("generate", help="输出替换后的上传命令")
    generate_parser.add_argument("repo_name", help="仓库名称")
    generate_parser.add_argument("template_name", help="模板名称")
    
    args = parser.parse_args()
    
    uploader = GitUploader()
    
    if args.command == "repo":
        if args.repo_command == "create":
            uploader.create_repo(args.name)
        elif args.repo_command == "list":
            repos = uploader.list_repos()
            if repos:
                print("可用仓库:")
                for repo in repos:
                    print(f"- {repo}")
            else:
                print("没有可用仓库")
    elif args.command == "template":
        if args.template_command == "add":
            uploader.add_template(args.repo_name, args.template_name, args.command)
        elif args.template_command == "list":
            templates = uploader.list_templates(args.repo_name)
            if not templates:
                print("没有可用模板")
            else:
                for name, command in templates.items():
                    print(f"- {name}: {command}")
    elif args.command == "run":
        uploader.run_template(args.repo_name, args.template_name)
    elif args.command == "generate":
        generated = uploader.generate_template(args.repo_name, args.template_name)
        if generated is None:
            print("仓库或模板不存在")
            return 1
        print(generated)
    else:
        parser.print_help()

    return 0

if __name__ == "__main__":
    main()