#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""GitUploader 测试文件"""

import unittest
import tempfile
import shutil
import os
import json
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gitup import GitUploader, main


class TestGitUploader(unittest.TestCase):
    """GitUploader测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # 创建临时配置目录
        self.config_dir = os.path.join(self.temp_dir, '.gitup')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.templates_dir = os.path.join(self.config_dir, 'templates')
        
        # 创建GitUploader实例
        self.gitup = GitUploader()
        self.gitup.CONFIG_DIR = self.config_dir
        self.gitup.CONFIG_FILE = self.config_file
        self.gitup.TEMPLATES_DIR = self.templates_dir
        
        # 清空配置
        self.gitup.config = {'repositories': {}, 'current_repo': None}
        self.gitup.current_repo = None
    
    def tearDown(self):
        """测试后清理"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_repo(self):
        """测试创建仓库"""
        result = self.gitup.create_repo('test_repo')
        self.assertTrue(result)
        self.assertIn('test_repo', self.gitup.list_repos())
    
    def test_create_duplicate_repo(self):
        """测试创建重复仓库"""
        self.gitup.create_repo('test_repo')
        result = self.gitup.create_repo('test_repo')
        self.assertFalse(result)
    
    def test_add_template(self):
        """测试添加模板"""
        self.gitup.create_repo('test_repo')
        
        template_name = 'test_template'
        command = 'git add .'
        
        result = self.gitup.add_template('test_repo', template_name, command)
        self.assertTrue(result)
        
        # 检查模板是否添加成功
        templates = self.gitup.list_templates('test_repo')
        self.assertIn(template_name, templates)
        self.assertEqual(templates[template_name], command)
    
    def test_add_template_to_nonexistent_repo(self):
        """测试向不存在的仓库添加模板"""
        result = self.gitup.add_template('nonexistent', 'test', 'git add .')
        self.assertFalse(result)

    def test_edit_template(self):
        """测试编辑模板命令"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'daily', 'echo old')

        self.assertTrue(self.gitup.edit_template('test_repo', 'daily', 'echo new\ngit push'))
        self.assertEqual(self.gitup.list_templates('test_repo')['daily'], 'echo new\ngit push')

    def test_delete_template(self):
        """测试删除模板"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'daily', 'echo old')

        self.assertTrue(self.gitup.delete_template('test_repo', 'daily'))
        self.assertNotIn('daily', self.gitup.list_templates('test_repo'))
        self.assertFalse(self.gitup.delete_template('test_repo', 'daily'))
    
    def test_run_template(self):
        """测试运行模板"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'test_template', 'echo "test"')
        
        result = self.gitup.run_template('test_repo', 'test_template')
        self.assertTrue(result)
    
    def test_run_nonexistent_template(self):
        """测试运行不存在的模板"""
        self.gitup.create_repo('test_repo')
        result = self.gitup.run_template('test_repo', 'nonexistent')
        self.assertFalse(result)
    
    def test_list_templates(self):
        """测试列出模板"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'template1', 'git add .')
        self.gitup.add_template('test_repo', 'template2', 'git commit')
        
        templates = self.gitup.list_templates('test_repo')
        self.assertEqual(len(templates), 2)
        self.assertIn('template1', templates)
        self.assertIn('template2', templates)

    def test_generate_template_replaces_runtime_placeholders(self):
        """测试生成命令时替换实时占位符"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template(
            'test_repo', 'daily', 'git commit -m "{date} {year} {unknown}"'
        )

        command = self.gitup.generate_template('test_repo', 'daily')

        self.assertIsNotNone(command)
        self.assertRegex(command, r'git commit -m "\d{4}-\d{2}-\d{2} \d{4} \{unknown\}"')

    @patch('gitup.interactive_menu')
    def test_main_without_arguments_opens_menu(self, interactive_menu):
        """测试无参数启动交互菜单"""
        self.assertEqual(main([]), 0)
        interactive_menu.assert_called_once()

    @patch('gitup.interactive_menu')
    def test_main_with_command_skips_menu(self, interactive_menu):
        """测试有明确命令时不打开菜单"""
        self.assertEqual(main(['repo', 'list']), 0)
        interactive_menu.assert_not_called()

    def test_gen_is_short_alias_for_generate(self):
        """测试 gen 和旧 generate 命令都能生成命令"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'daily', 'echo {date}')
        with patch('gitup.GitUploader', return_value=self.gitup), patch('builtins.print') as output:
            self.assertEqual(main(['gen', 'test_repo', 'daily']), 0)
            self.assertEqual(main(['generate', 'test_repo', 'daily']), 0)
        self.assertEqual(output.call_count, 2)

    def test_create_repo_menu_adds_first_template(self):
        """测试创建仓库后自动进入首个模板创建"""
        uploader = GitUploader(self.config_dir)
        with patch('gitup._read_input', side_effect=['1', 'new_repo', 'daily', 'echo ok', 'END', '0']):
            with patch('builtins.print'):
                from gitup import interactive_menu
                interactive_menu(uploader)
        self.assertEqual(uploader.list_templates('new_repo')['daily'], 'echo ok')

    def test_multiline_template_input(self):
        """测试模板命令支持多行输入"""
        from gitup import _read_multiline
        with patch('gitup._read_input', side_effect=['git add .', 'git push', 'END']):
            self.assertEqual(_read_multiline('命令'), 'git add .\ngit push')

    def test_generated_command_prints_and_does_not_run(self):
        """测试生成命令只输出，不自动执行"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'daily', 'echo {date}')
        with patch('gitup._read_input', side_effect=['test_repo', 'daily']), \
                patch('gitup.subprocess.run') as run_command, \
                patch('builtins.print') as output:
            from gitup import _print_generated_command
            self.assertTrue(_print_generated_command(self.gitup))
        run_command.assert_not_called()
        self.assertTrue(any('echo ' in call.args[0] for call in output.call_args_list if call.args))
        self.assertFalse(any('已退出菜单' in call.args[0] for call in output.call_args_list if call.args))

    def test_edit_menu_shows_existing_command(self):
        """测试编辑菜单会显示旧命令"""
        self.gitup.create_repo('test_repo')
        self.gitup.add_template('test_repo', 'daily', 'echo old\ngit push')
        inputs = ['5', 'test_repo', 'daily', 'echo new', 'git push --tags', 'END', '0']
        with patch('builtins.input', side_effect=inputs), patch('builtins.print') as output:
            from gitup import interactive_menu
            interactive_menu(self.gitup)
        self.assertTrue(any(
            call.args and 'echo old' in call.args[0]
            for call in output.call_args_list
        ))
        self.assertEqual(
            self.gitup.list_templates('test_repo')['daily'],
            'echo new\ngit push --tags',
        )


if __name__ == '__main__':
    unittest.main()