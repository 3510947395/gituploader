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
import sys
try:
    import readline
except ImportError:
    readline = None
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def _supports_color() -> bool:
    """仅在 Termux 交互终端启用颜色。"""
    return sys.stdout.isatty() and os.getenv("TERM", "") != "dumb"


def _style(text: str, code: str) -> str:
    if not _supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"

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

    def edit_template(self, repo_name: str, template_name: str, command: str) -> bool:
        """修改已有模板的命令内容。"""
        if not command.strip():
            print("命令内容不能为空")
            return False
        config = self._read_repo(repo_name)
        if config is None:
            print(f"仓库 '{repo_name}' 不存在")
            return False
        if template_name not in config.get("templates", {}):
            print(f"模板 '{template_name}' 不存在")
            return False
        config["templates"][template_name] = command
        self._write_repo(repo_name, config)
        print(f"模板 '{template_name}' 已更新")
        return True

    def delete_template(self, repo_name: str, template_name: str) -> bool:
        """删除已有模板。"""
        config = self._read_repo(repo_name)
        if config is None:
            print(f"仓库 '{repo_name}' 不存在")
            return False
        if template_name not in config.get("templates", {}):
            print(f"模板 '{template_name}' 不存在")
            return False
        del config["templates"][template_name]
        self._write_repo(repo_name, config)
        print(f"模板 '{template_name}' 已删除")
        return True

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

def _read_input(prompt: str) -> Optional[str]:
    """读取菜单输入，退出或 EOF 时返回 None。"""
    try:
        value = input(prompt)
        if readline is None:
            value = re.sub(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|O[@-~])", "", value)
        return value.strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _read_input_with_default(prompt: str, default: str = "") -> Optional[str]:
    """显示默认文本并允许使用 readline 逐字编辑。"""
    if readline is None or not default:
        if default:
            print(f"{prompt}{default}")
        return _read_input(prompt)
    try:
        readline.set_startup_hook(lambda: readline.insert_text(default))
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    finally:
        readline.set_startup_hook()


def _read_multiline(
    prompt: str, end_marker: str = "END", initial: Optional[List[str]] = None
) -> Optional[str]:
    """读取可粘贴的多行命令，单独输入 END 表示结束。"""
    print(prompt)
    if initial:
        print("原命令已逐行载入，可用方向键移动并修改每一行")
    print(f"输入完成后，单独输入 {end_marker} 保存；直接输入 {end_marker} 取消")
    lines = []
    for index, default in enumerate(initial or [], 1):
        line = _read_input_with_default(f"第 {index} 行: ", default)
        if line is None:
            return None
        lines.append(line)
    while True:
        line = _read_input("| ")
        if line is None:
            return None
        if line == end_marker:
            command = "\n".join(lines).strip()
            return command or None
        lines.append(line)


def _add_template_interactively(uploader: GitUploader, repo_name: str) -> None:
    print(_style(f"\n已创建仓库：{repo_name}", "32"))
    print("现在添加第一套模板（直接回车可稍后添加）")
    template_name = _read_input("模板名称: ")
    if template_name:
        print("可用占位符：{date} {time} {datetime} {year} {month} {day}")
        print("             {timestamp} {username} {hostname}")
        command = _read_multiline("命令内容（支持多行）:")
        if command:
            uploader.add_template(repo_name, template_name, command)


def _print_generated_command(uploader: GitUploader) -> bool:
    """展开并输出命令，然后结束菜单让用户手动复制执行。"""
    repo_name = _read_input("仓库名称: ")
    template_name = _read_input("模板名称: ")
    if not repo_name or not template_name:
        return False
    command = uploader.generate_template(repo_name, template_name)
    if command is None:
        print("仓库或模板不存在")
        return False
    print("\n生成的命令（请复制到目标 Git 目录手动执行）：")
    print(command)
    return True


def interactive_menu(uploader: GitUploader) -> None:
    """启动兼容彩色终端和纯文本终端的交互菜单。"""
    while True:
        print(_style("\n┌─ GitUploader ─────────────────────┐", "36"))
        print(_style("│ Git 命令管理 · Termux │", "36"))
        print(_style("├───────────────────────────────────┤", "36"))
        print("│ 1  创建仓库                         │")
        print("│ 2  查看仓库                         │")
        print("│ 3  添加模板                         │")
        print("│ 4  查看模板                         │")
        print("│ 5  编辑模板                         │")
        print("│ 6  删除模板                         │")
        print("│ 7  生成命令                         │")
        print("│ 8  执行命令                         │")
        print("│ 0  退出                             │")
        print(_style("└───────────────────────────────────┘", "36"))
        choice = _read_input("选择 [0-8]: ")
        if choice is None or choice == "0":
            print("已退出")
            return
        if choice == "1":
            name = _read_input("仓库名称: ")
            if name and uploader.create_repo(name):
                _add_template_interactively(uploader, name)
        elif choice == "2":
            repos = uploader.list_repos()
            print("\n".join(f"  * {name}" for name in repos) if repos else "没有可用仓库")
        elif choice == "3":
            repo_name = _read_input("仓库名称: ")
            template_name = _read_input("模板名称: ")
            print("可用占位符：{date} {time} {datetime} {year} {month} {day}")
            print("             {timestamp} {username} {hostname}")
            command = _read_multiline("命令内容（支持多行）:")
            if repo_name and template_name and command:
                uploader.add_template(repo_name, template_name, command)
        elif choice == "4":
            repo_name = _read_input("仓库名称: ")
            if repo_name:
                templates = uploader.list_templates(repo_name)
                if templates:
                    for name, command in templates.items():
                        print(f"  * {name}: {command}")
                else:
                    print("没有可用模板")
        elif choice == "5":
            repo_name = _read_input("仓库名称: ")
            template_name = _read_input("模板名称: ")
            if repo_name and template_name:
                existing = uploader.list_templates(repo_name).get(template_name)
                if existing is None:
                    print("仓库或模板不存在")
                    continue
                print(f"\n当前命令：\n{existing}")
                print("可用占位符：{date} {time} {datetime} {year} {month} {day}")
                print("             {timestamp} {username} {hostname}")
                command = _read_multiline(
                    "新的命令内容（逐行编辑，支持多行）:",
                    initial=existing.splitlines(),
                )
                if command:
                    uploader.edit_template(repo_name, template_name, command)
        elif choice == "6":
            repo_name = _read_input("仓库名称: ")
            template_name = _read_input("模板名称: ")
            if repo_name and template_name:
                confirm = _read_input(f"确定删除模板 '{template_name}'？输入 y 确认: ")
                if confirm and confirm.lower() == "y":
                    uploader.delete_template(repo_name, template_name)
                else:
                    print("已取消删除")
        elif choice in {"7", "8"}:
            if choice == "7":
                if _print_generated_command(uploader):
                    return
            else:
                repo_name = _read_input("仓库名称: ")
                template_name = _read_input("模板名称: ")
                if repo_name and template_name:
                    uploader.run_template(repo_name, template_name)
        else:
            print("无效选项，请重新选择")


def main(argv=None):
    examples = """示例:
  gitup                              打开交互菜单
  gitup repo create myproject        创建仓库
  gitup template add myproject daily "git add . && git push"
  gitup template list myproject      查看模板
    gitup template edit myproject daily "git add . && git push --tags"
    gitup template delete myproject daily 删除模板
  gitup gen myproject daily          生成命令，不执行
  gitup run myproject daily          执行命令
"""
    parser = argparse.ArgumentParser(
        description="GitUploader - Git 命令管理工具",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="gituploader 1.0.9")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    repo_parser = subparsers.add_parser("repo", help="仓库管理")
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command")
    create_parser = repo_subparsers.add_parser("create", help="创建仓库")
    create_parser.add_argument("name", help="仓库名称")
    repo_subparsers.add_parser("list", help="列出仓库")

    template_parser = subparsers.add_parser("template", help="模板管理")
    template_subparsers = template_parser.add_subparsers(dest="template_command")
    add_parser = template_subparsers.add_parser("add", help="添加模板")
    add_parser.add_argument("repo_name", help="仓库名称")
    add_parser.add_argument("template_name", help="模板名称")
    add_parser.add_argument("command", help="命令内容")
    edit_parser = template_subparsers.add_parser("edit", help="编辑模板")
    edit_parser.add_argument("repo_name", help="仓库名称")
    edit_parser.add_argument("template_name", help="模板名称")
    edit_parser.add_argument("command", help="新的命令内容")
    delete_parser = template_subparsers.add_parser(
        "delete", aliases=["remove"], help="删除模板"
    )
    delete_parser.add_argument("repo_name", help="仓库名称")
    delete_parser.add_argument("template_name", help="模板名称")
    list_parser = template_subparsers.add_parser("list", help="列出模板")
    list_parser.add_argument("repo_name", help="仓库名称")

    run_parser = subparsers.add_parser("run", help="执行模板命令")
    run_parser.add_argument("repo_name", help="仓库名称")
    run_parser.add_argument("template_name", help="模板名称")
    gen_parser = subparsers.add_parser("gen", aliases=["generate"], help="生成命令")
    gen_parser.add_argument("repo_name", help="仓库名称")
    gen_parser.add_argument("template_name", help="模板名称")

    command_args = sys.argv[1:] if argv is None else argv
    if not command_args:
        interactive_menu(GitUploader())
        return 0
    args = parser.parse_args(command_args)
    uploader = GitUploader()

    if args.command == "repo":
        if args.repo_command == "create":
            uploader.create_repo(args.name)
        elif args.repo_command == "list":
            repos = uploader.list_repos()
            print("可用仓库:\n" + "\n".join(f"- {repo}" for repo in repos) if repos else "没有可用仓库")
    elif args.command == "template":
        if args.template_command == "add":
            uploader.add_template(args.repo_name, args.template_name, args.command)
        elif args.template_command == "edit":
            uploader.edit_template(args.repo_name, args.template_name, args.command)
        elif args.template_command in {"delete", "remove"}:
            uploader.delete_template(args.repo_name, args.template_name)
        elif args.template_command == "list":
            templates = uploader.list_templates(args.repo_name)
            print("没有可用模板" if not templates else "\n".join(f"- {name}: {command}" for name, command in templates.items()))
    elif args.command == "run":
        uploader.run_template(args.repo_name, args.template_name)
    elif args.command in {"gen", "generate"}:
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