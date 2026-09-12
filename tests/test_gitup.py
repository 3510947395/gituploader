#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""GitUploader 测试文件"""

import unittest
import tempfile
import shutil
import os
import json
import re
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
        with patch('gitup._read_input', side_effect=['1', 'new_repo', 'daily', 'echo ok', '0']):
            with patch('builtins.print'):
                from gitup import interactive_menu
                interactive_menu(uploader)
        self.assertEqual(uploader.list_templates('new_repo')['daily'], 'echo ok')


if __name__ == '__main__':
    unittest.main()