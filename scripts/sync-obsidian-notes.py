#!/usr/bin/env python3
import os
import sys
import re
import time
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 模板文件路径
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, 'resources', 'templates', 'hugo-header.md')
# 目标目录
CONTENT_DIR = os.path.join(PROJECT_ROOT, 'content', 'notes')

# 读取模板文件并解析为模板对象
def read_template():
    template = {
        'content': '',
        'fields': {}
    }
    
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_field = None
    field_properties = {}
    pending_properties = {}
    
    for line in lines:
        line = line.rstrip()
        
        # 处理注释行
        if line.startswith('#'):
            # 解析字段属性，暂时存储在 pending_properties 中
            comment_text = line[1:].strip()
            if '类型: ' in comment_text:
                pending_properties['type'] = comment_text.split('类型: ')[1].strip()
            elif '必需: ' in comment_text:
                pending_properties['required'] = comment_text.split('必需: ')[1].strip() == '是'
            elif '格式: ' in comment_text:
                pending_properties['format'] = comment_text.split('格式: ')[1].strip()
            elif '默认值: ' in comment_text:
                pending_properties['default'] = comment_text.split('默认值: ')[1].strip()
        elif ': ' in line or '=' in line:
            # 新字段开始
            if current_field and field_properties:
                template['fields'][current_field] = field_properties
            
            # 提取字段名
            if ': ' in line:
                field_name = line.split(': ')[0].strip()
            elif '=' in line:
                field_name = line.split('=')[0].strip()
            else:
                field_name = line[:-1].strip()
            
            current_field = field_name
            # 将待处理的属性应用到当前字段
            field_properties = pending_properties.copy()
            pending_properties = {}
        else:
            # 非注释和非字段行，添加到模板内容
            template['content'] += line + '\n'
    
    # 添加最后一个字段的属性
    if current_field and field_properties:
        template['fields'][current_field] = field_properties
    
    return template

# 解析 Obsidian 笔记的前置元数据
def parse_front_matter(content):
    front_matter = {}
    # 查找前置元数据
    match = re.search(r'^---\n(.*?)---\n', content, re.DOTALL)
    if match:
        front_matter_text = match.group(1)
        lines = front_matter_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and (': ' in line or line.endswith(':')):
                i += 1
                if ': ' in line:
                    key, value = line.split(': ', 1)
                else:
                    key = line[:-1].strip()
                    value = ''
                # 处理数组类型
                if value.startswith('[') and value.endswith(']'):
                    # 单行数组
                    elements = re.findall(r'"([^"]*)"', value)
                    front_matter[key] = elements
                elif value == '':
                    # 可能是多行数组的开始
                    elements = []
                    while i < len(lines):
                        item_line = lines[i].strip()
                        if item_line.startswith('- '):
                            # 提取数组元素
                            item = item_line[2:].strip()
                            # 去除引号
                            if item.startswith('"') and item.endswith('"'):
                                item = item[1:-1]
                            elements.append(item)
                            i += 1
                        else:
                            break
                    front_matter[key] = elements
                elif value.lower() in ['true', 'false']:
                    front_matter[key] = value.lower() == 'true'
                else:
                    # 去除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    front_matter[key] = value
            else:
                i += 1
    return front_matter

# 提取 Obsidian 笔记的内容（去除前置元数据）
def extract_content(content):
    match = re.search(r'^---\n.*?---\n(.*)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()

# 生成 Hugo 格式的前置元数据
def generate_hugo_front_matter(front_matter, filename):
    template = read_template()
    
    # 提取 ts 字段
    ts = front_matter.get('ts', None)
    if not ts:
        ts = str(int(time.time()))
    
    # 构建 Hugo 前置元数据
    hugo_front_matter = '+++\n'
    
    # 处理每个字段
    for field_name, properties in template['fields'].items():
        # 获取字段值
        if field_name == 'title':
            value = front_matter.get('title', os.path.splitext(filename)[0])
            hugo_front_matter += f'title = "{value}"\n'
        elif field_name == 'author':
            value = front_matter.get('author', ['CC'])
            author_str = '[' + ', '.join([f'"{a}"' for a in value]) + ']'
            hugo_front_matter += f'author = {author_str}\n'
        elif field_name == 'date':
            value = front_matter.get('date', datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'))
            hugo_front_matter += f'date = {value}\n'
        elif field_name == 'slug':
            value = front_matter.get('slug', '')
            hugo_front_matter += f'slug = "{value}"\n'
        elif field_name == 'tags':
            value = front_matter.get('tags', [])
            tags_str = '[' + ', '.join([f'"{t}"' for t in value]) + ']'
            hugo_front_matter += f'tags = {tags_str}\n'
        elif field_name == 'categories':
            value = front_matter.get('categories', ['note'])
            categories_str = '[' + ', '.join([f'"{c}"' for c in value]) + ']'
            hugo_front_matter += f'categories = {categories_str}\n'
        elif field_name == 'draft':
            value = front_matter.get('draft', 'false')
            hugo_front_matter += f'draft = {value}\n'
        elif field_name == 'toc':
            value = front_matter.get('toc', 'true')
            hugo_front_matter += f'toc = {value}\n'
    
    hugo_front_matter += '+++'
    
    return hugo_front_matter, ts

# 同步单个 Obsidian 笔记
def sync_note(note_path):
    with open(note_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析前置元数据
    front_matter = parse_front_matter(content)
    
    # 检查是否 finished: true
    if front_matter.get('finished', False) is not True:
        return False
    
    # 提取内容
    note_content = extract_content(content)
    
    # 生成 Hugo 格式的前置元数据
    filename = os.path.basename(note_path)
    hugo_front_matter, ts = generate_hugo_front_matter(front_matter, filename)
    
    # 生成目标文件名
    base_filename = os.path.splitext(filename)[0]
    target_filename = f"{ts}-{base_filename}.md"
    target_path = os.path.join(CONTENT_DIR, target_filename)
    
    # 组合最终内容
    final_content = hugo_front_matter + '\n\n' + note_content
    
    # 写入文件
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"Synced: {note_path} -> {target_path}")
    return True

# 同步目录下的所有 Obsidian 笔记
def sync_directory(directory):
    synced_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                note_path = os.path.join(root, file)
                if sync_note(note_path):
                    synced_count += 1
    
    return synced_count

# 主函数
def main():
    if len(sys.argv) != 2:
        print("Usage: python sync-obsidian-notes.py <obsidian_file_or_directory>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # 确保目标目录存在
    os.makedirs(CONTENT_DIR, exist_ok=True)
    
    # 开始同步
    start_time = time.time()
    
    if os.path.isfile(input_path):
        # 同步单个文件
        print(f"Syncing Obsidian note from {input_path} to {CONTENT_DIR}")
        synced_count = 1 if sync_note(input_path) else 0
    elif os.path.isdir(input_path):
        # 同步目录
        print(f"Syncing Obsidian notes from {input_path} to {CONTENT_DIR}")
        synced_count = sync_directory(input_path)
    else:
        print(f"Error: {input_path} is not a file or directory")
        sys.exit(1)
    
    end_time = time.time()
    
    print(f"Sync completed in {end_time - start_time:.2f} seconds")
    print(f"Synced {synced_count} notes")

if __name__ == "__main__":
    main()