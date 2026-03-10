+++
title = "【Git】fork 仓库与源仓库的同步更新"
author = "CC"
date = 2026-03-09T00:00:00
tags = []
categories = ["note"]
draft = false
toc = true
+++

同步fork项目与原项目的更新是GitHub协作中的常见需求。以下是详细的操作步骤：
<!--more-->

## 1. 配置上游仓库

首先需要添加原项目作为上游仓库：

```bash
# 查看当前远程仓库
git remote -v

# 添加原项目作为上游仓库（只需执行一次）
git remote add upstream https://github.com/原项目所有者/原项目名称.git

# 再次查看确认
git remote -v
```

## 2. 获取原项目更新

```bash
# 获取上游仓库的所有更新
git fetch upstream

# 查看所有分支
git branch -a
```

## 3. 同步更新到本地

### 方法一：合并更新（推荐）

```bash
# 切换到主分支
git checkout main

# 合并上游主分支的更新
git merge upstream/main

# 推送到自己的fork仓库
git push origin main
```

### 方法二：变基更新（保持线性历史）

```bash
# 切换到主分支
git checkout main

# 变基到上游主分支
git rebase upstream/main

# 强制推送到自己的fork仓库
git push origin main --force-with-lease
```

## 4. 同步其他分支

如果原项目有其他分支也需要同步：

```bash
# 创建并切换到新分支
git checkout -b 新分支名 upstream/新分支名

# 推送到自己的fork仓库
git push origin 新分支名
```

## 5. 定期同步的最佳实践

### 设置自动化同步脚本

创建一个同步脚本 `sync-upstream.sh`：

```bash
#!/bin/bash
echo "正在同步上游仓库更新..."

# 获取上游更新
git fetch upstream

# 切换到主分支
git checkout main

# 合并更新
git merge upstream/main

# 推送到自己的fork
git push origin main

echo "同步完成！"
```

### 使用GitHub Actions自动同步

在 `.github/workflows/sync.yml` 中创建：

```yaml
name: Sync Upstream

on:
  schedule:
    - cron: '0 0 * * *'  # 每天午夜运行
  workflow_dispatch:  # 允许手动触发

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Add upstream remote
        run: git remote add upstream https://github.com/原项目所有者/原项目名称.git
      
      - name: Fetch upstream
        run: git fetch upstream
      
      - name: Merge upstream
        run: |
          git checkout main
          git merge upstream/main
      
      - name: Push changes
        run: git push origin main
```

## 6. 处理冲突

如果在合并过程中出现冲突：

```bash
# 查看冲突文件
git status

# 手动解决冲突后
git add 冲突文件
git commit -m "解决合并冲突"
git push origin main
```

## 7. 实用命令速查

```bash
# 查看远程仓库配置
git remote -v

# 查看分支差异
git log --oneline --graph --decorate main upstream/main

# 查看特定文件的差异
git diff upstream/main -- 文件路径

# 查看上游仓库的最新提交
git log upstream/main -5 --oneline
```

## 注意事项

1. **不要直接在主分支上开发**，始终创建功能分支
2. **定期同步**，避免积累过多差异导致合并困难
3. **备份重要更改**，在同步前确保本地更改已提交
4. **使用`--force-with-lease`**而不是`--force`，更安全地强制推送

通过以上步骤，您可以有效地保持fork项目与原项目的同步，确保及时获取原项目的最新更新和修复。
