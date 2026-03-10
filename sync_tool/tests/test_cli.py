#!/usr/bin/env python3
"""
测试命令行版本的转换功能
"""

import subprocess
import os
import tempfile
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))


def test_hugo_to_obsidian():
    """测试 Hugo 到 Obsidian 的转换"""
    # 创建测试文件
    hugo_content = '''+++
title = "Test Note"
author = ["CC"]
date = 2023-11-18T22:27:00+08:00
slug = "test"
tags = ["test", "example"]
categories = ["note", "tech"]
draft = false
toc = true
+++

# Test Content

This is a test note.
'''
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(hugo_content)
        input_file = f.name
    
    # 输出文件
    output_file = input_file.replace('.md', '-obsidian.md')
    
    try:
        # 运行命令
        result = subprocess.run(
            ["python", "cli.py", input_file, output_file, "--direction", "hugo-to-obsidian"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True
        )
        
        # 检查结果
        print("Hugo → Obsidian 转换测试:")
        print("退出码:", result.returncode)
        print("输出:", result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
        
        # 检查输出文件是否存在
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print("输出文件内容:")
            print(content)
            
            # 验证关键内容
            assert 'type:' in content
            assert 'note' in content
            assert 'tech' in content
            assert 'tags:' in content
            assert 'test' in content
            assert 'example' in content
            assert 'date: 2023-11-18' in content
            assert 'ts: 20231118222700' in content
            assert 'draft: False' in content
            assert '# Test Content' in content
            print("✓ 测试通过")
        else:
            print("✗ 输出文件不存在")
            
    finally:
        # 清理临时文件
        if os.path.exists(input_file):
            os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_obsidian_to_hugo():
    """测试 Obsidian 到 Hugo 的转换"""
    # 创建测试文件
    obsidian_content = '''---
type:
  - note
  - tech
aliases:
tags:
  - test
  - example
date: 2023-11-18
ts: 20231118222700
draft: false
---

# Test Content

This is a test note.
'''
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(obsidian_content)
        input_file = f.name
    
    # 输出文件
    output_file = input_file.replace('.md', '-hugo.md')
    
    try:
        # 运行命令
        result = subprocess.run(
            ["python", "cli.py", input_file, output_file, "--direction", "obsidian-to-hugo"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True
        )
        
        # 检查结果
        print("\nObsidian → Hugo 转换测试:")
        print("退出码:", result.returncode)
        print("输出:", result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
        
        # 检查输出文件是否存在
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print("输出文件内容:")
            print(content)
            
            # 验证关键内容
            assert 'title = "Test Content"' in content
            assert 'date = 2023-11-18T22:27:00+08:00' in content
            assert 'tags = ["test", "example"]' in content
            assert 'categories = ["note", "tech"]' in content
            assert 'draft = False' in content
            assert '# Test Content' in content
            print("✓ 测试通过")
        else:
            print("✗ 输出文件不存在")
            
    finally:
        # 清理临时文件
        if os.path.exists(input_file):
            os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


if __name__ == '__main__':
    test_hugo_to_obsidian()
    test_obsidian_to_hugo()
    print("\n所有测试完成！")