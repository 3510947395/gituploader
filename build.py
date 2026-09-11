#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""GitUploader 构建脚本"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """清理构建目录"""
    build_dirs = ['build', 'dist', '*.egg-info']
    for pattern in build_dirs:
        if '*' in pattern:
            import glob
            for dir_path in glob.glob(pattern):
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path)
        else:
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
    
    print("清理完成")

def run_tests():
    """运行测试"""
    print("运行测试...")
    try:
        # 切换到项目根目录
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover',
                     '-s', 'tests', '-v'],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 所有测试通过")
        else:
            print("✗ 测试失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
        
        return True
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

def build_package():
    """构建包"""
    print("构建包...")
    try:
        # 切换到项目根目录
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # 使用 pip 构建 wheel，避免本目录的 build.py 遮蔽 build 模块
        result = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '.',
                     '--no-deps', '--wheel-dir', 'dist'],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 构建成功")
            return True
        else:
            print("✗ 构建失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"构建包时出错: {e}")
        return False

def build_deb_package():
    """构建 Debian/Termux 安装包"""
    project_root = Path(__file__).parent
    result = subprocess.run([sys.executable, str(project_root / 'build_deb.py')])
    return result.returncode == 0

def install_package():
    """安装包"""
    print("安装包...")
    try:
        # 切换到项目根目录
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # 安装包
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 安装成功")
            return True
        else:
            print("✗ 安装失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"安装包时出错: {e}")
        return False

def check_installation():
    """检查安装"""
    print("检查安装...")
    try:
        # 检查gitup命令是否可用
        result = subprocess.run(['gitup', '--version'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ GitUploader 已正确安装")
            print(f"版本: {result.stdout.strip()}")
            return True
        else:
            print("✗ GitUploader 安装检查失败")
            return False
    except Exception as e:
        print(f"检查安装时出错: {e}")
        return False

def main():
    """主函数"""
    print("GitUploader 构建脚本")
    print("=" * 40)
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = 'all'
    
    if command == 'clean':
        clean_build()
    elif command == 'test':
        success = run_tests()
        sys.exit(0 if success else 1)
    elif command == 'build':
        success = build_package()
        sys.exit(0 if success else 1)
    elif command == 'deb':
        success = build_deb_package()
        sys.exit(0 if success else 1)
    elif command == 'install':
        success = install_package()
        sys.exit(0 if success else 1)
    elif command == 'check':
        success = check_installation()
        sys.exit(0 if success else 1)
    elif command == 'all':
        print("执行完整构建流程...")
        
        clean_build()
        
        if not run_tests():
            print("测试失败，停止构建")
            sys.exit(1)
        
        if not build_package():
            print("构建失败，停止安装")
            sys.exit(1)
        
        if not install_package():
            print("安装失败")
            sys.exit(1)
        
        if not check_installation():
            print("安装检查失败")
            sys.exit(1)
        
        print("\n✓ GitUploader 构建和安装完成！")
    else:
        print(f"未知命令: {command}")
        print("可用命令: clean, test, build, deb, install, check, all")
        sys.exit(1)

if __name__ == '__main__':
    main()
