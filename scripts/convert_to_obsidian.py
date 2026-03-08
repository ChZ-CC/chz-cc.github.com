#!/usr/bin/env python3
"""
将 Hugo 格式的 Markdown 文件转换为 Obsidian 格式

用法:
    python convert_to_obsidian.py <input_directory> <output_directory>
"""

import os
import re
import argparse
from datetime import datetime


def read_obsidian_template(template_path):
    """读取 Obsidian 模板文件"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_hugo_frontmatter(content):
    """解析 Hugo 格式的前端"""
    frontmatter_match = re.match(r'^\+\+\+(.*?)\+\+\+', content, re.DOTALL)
    if not frontmatter_match:
        return {}
    
    frontmatter = frontmatter_match.group(1)
    data = {}
    
    # 提取 title
    title_match = re.search(r'title\s*=\s*["\'](.*?)["\']', frontmatter)
    if title_match:
        data['title'] = title_match.group(1)
    
    # 提取 date
    date_match = re.search(r'date\s*=\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2})', frontmatter)
    if date_match:
        data['date'] = date_match.group(1)
    
    # 提取 tags
    tags_match = re.search(r'tags\s*=\s*\[(.*?)\]', frontmatter, re.DOTALL)
    if tags_match:
        tags_str = tags_match.group(1)
        # 提取引号中的内容
        tags = re.findall(r'["\'](.*?)["\']', tags_str)
        data['tags'] = tags
    
    return data


def convert_to_obsidian_format(hugo_data, template_content):
    """转换为 Obsidian 格式"""
    # 解析日期
    date_str = hugo_data.get('date', '')
    if date_str:
        try:
            date_obj = datetime.fromisoformat(date_str)
            formatted_date = date_obj.strftime('%Y-%m-%d')
            ts = date_obj.strftime('%Y%m%d%H%M%S')
        except:
            formatted_date = "YYYY-MM-DD"
            ts = "YYYYMMDDHHmmss"
    else:
        formatted_date = "YYYY-MM-DD"
        ts = "YYYYMMDDHHmmss"
    
    # 替换模板中的占位符
    obsidian_frontmatter = template_content
    obsidian_frontmatter = obsidian_frontmatter.replace('YYYY-MM-DD', f'{formatted_date}')
    obsidian_frontmatter = obsidian_frontmatter.replace('YYYYMMDDHHmmss', f'{ts}')
    
    # 处理 categories -> type
    categories = hugo_data.get('categories', [])
    if categories:
        type_str = '  - ' + '\n  - '.join(categories)
        obsidian_frontmatter = obsidian_frontmatter.replace('type:', f'type:\n{type_str}')
    else:
        # 默认类型
        obsidian_frontmatter = obsidian_frontmatter.replace('type:', 'type:\n  - note')
    
    # 处理 tags
    tags = hugo_data.get('tags', [])
    if tags:
        tags_str = '  - ' + '\n  - '.join(tags)
        obsidian_frontmatter = obsidian_frontmatter.replace('tags:', f'tags:\n{tags_str}')
    
    # 处理 draft
    draft = hugo_data.get('draft', False)
    obsidian_frontmatter = obsidian_frontmatter.replace('draft: false', f'draft: {str(draft).lower()}')
    
    return obsidian_frontmatter


def process_file(input_file, output_file, template_content):
    """处理单个文件"""
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析 Hugo 前端
    hugo_data = parse_hugo_frontmatter(content)
    
    # 提取正文内容（去除前端）
    content_match = re.search(r'^\+\+\+.*?\+\+\+(.*)', content, re.DOTALL)
    if content_match:
        body = content_match.group(1).lstrip()
    else:
        body = content
    
    # 生成 Obsidian 前端
    obsidian_frontmatter = convert_to_obsidian_format(hugo_data, template_content)
    
    # 组合新内容
    new_content = obsidian_frontmatter.rstrip() + '\n\n' + body
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"转换完成: {input_file} -> {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将 Hugo 格式的 Markdown 文件转换为 Obsidian 格式')
    parser.add_argument('input', help='输入文件或目录')
    parser.add_argument('output', help='输出文件或目录')
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    
    # 读取 Obsidian 模板
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'obsidian-header.md')
    if not os.path.exists(template_path):
        print(f"错误: 找不到模板文件 {template_path}")
        return
    
    template_content = read_obsidian_template(template_path)
    
    # 检查输入是文件还是目录
    if os.path.isfile(input_path):
        # 处理单个文件
        if input_path.endswith('.md'):
            # 如果输出是目录，使用原文件名
            if os.path.isdir(output_path):
                output_file = os.path.join(output_path, os.path.basename(input_path))
            else:
                output_file = output_path
            process_file(input_path, output_file, template_content)
    elif os.path.isdir(input_path):
        # 处理目录
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith('.md'):
                    input_file = os.path.join(root, file)
                    # 计算相对路径
                    relative_path = os.path.relpath(input_file, input_path)
                    output_file = os.path.join(output_path, relative_path)
                    # 处理文件
                    process_file(input_file, output_file, template_content)
    else:
        print(f"错误: 输入路径 {input_path} 不存在")


if __name__ == '__main__':
    main()