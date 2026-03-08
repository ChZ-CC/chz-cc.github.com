#!/usr/bin/env python3
"""
命令行版本的转换工具
"""

import argparse
import os
import sys
from converter import HugoToObsidianConverter, ObsidianToHugoConverter


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Hugo-Obsidian 笔记转换工具')
    parser.add_argument('input', help='输入文件或目录')
    parser.add_argument('output', help='输出文件或目录')
    parser.add_argument('--direction', choices=['hugo-to-obsidian', 'obsidian-to-hugo'], 
                        default='hugo-to-obsidian', help='转换方向')
    
    args = parser.parse_args()
    
    # 检查输入是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件或目录 {args.input} 不存在")
        sys.exit(1)
    
    # 处理输入
    input_files = []
    if os.path.isfile(args.input):
        if args.input.endswith('.md'):
            input_files.append(args.input)
        else:
            print("错误: 输入文件必须是 Markdown 文件 (.md)")
            sys.exit(1)
    elif os.path.isdir(args.input):
        for root, _, files in os.walk(args.input):
            for file in files:
                if file.endswith('.md'):
                    input_files.append(os.path.join(root, file))
    
    if not input_files:
        print("错误: 没有找到 Markdown 文件")
        sys.exit(1)
    
    # 确保输出目录存在
    if os.path.isdir(args.output):
        output_dir = args.output
    else:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    # 执行转换
    for input_file in input_files:
        try:
            # 读取文件
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 选择转换器
            if args.direction == 'hugo-to-obsidian':
                converter = HugoToObsidianConverter()
                converted_content = converter.convert(content)
                if os.path.isdir(args.output):
                    output_file = os.path.join(args.output, os.path.basename(input_file))
                else:
                    output_file = args.output
            else:
                converter = ObsidianToHugoConverter()
                converted_content = converter.convert(content)
                if os.path.isdir(args.output):
                    output_file = os.path.join(args.output, os.path.basename(input_file))
                else:
                    output_file = args.output
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            
            print(f"转换完成: {input_file} -> {output_file}")
            
        except Exception as e:
            print(f"转换失败 {input_file}: {str(e)}")


if __name__ == '__main__':
    main()