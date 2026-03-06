# Obsidian 笔记同步工具

## 功能

这个工具用于将 Obsidian 笔记同步到 Hugo 项目的 `content/notes` 目录中。

- 支持同步单个文件或整个目录
- 对于目录，递归处理所有子目录及其文件
- 只同步标记为 `finished: true` 的笔记
- 自动生成唯一的时间戳作为文件名前缀
- 转换 Obsidian 前置元数据为 Hugo 格式
- 支持跨平台使用（Windows、Linux、macOS）

## 使用方法

### Windows 系统

```bash
# 进入 scripts 目录
cd scripts

# 同步单个文件
sync-obsidian-notes.bat <obsidian_note_file.md>

# 同步整个目录（递归处理）
sync-obsidian-notes.bat <obsidian_vault_directory>
```

### Linux/macOS 系统

```bash
# 进入 scripts 目录
cd scripts

# 给脚本添加执行权限（首次使用时）
chmod +x sync-obsidian-notes.sh

# 同步单个文件
./sync-obsidian-notes.sh <obsidian_note_file.md>

# 同步整个目录（递归处理）
./sync-obsidian-notes.sh <obsidian_vault_directory>
```

## 脚本说明

- `sync-obsidian-notes.py`：核心 Python 脚本，实现同步功能
- `sync-obsidian-notes.bat`：Windows 批处理文件
- `sync-obsidian-notes.sh`：Linux/macOS shell 脚本

## 注意事项

1. 确保 Obsidian 笔记中包含 `finished: true` 标记，否则不会被同步
2. 脚本会自动创建 `content/notes` 目录（如果不存在）
3. 同步时会覆盖已存在的同名文件
4. 文件名格式为 `{ts}-{原文件名}.md`，其中 `ts` 是时间戳

## 依赖

- Python 3.6 或更高版本