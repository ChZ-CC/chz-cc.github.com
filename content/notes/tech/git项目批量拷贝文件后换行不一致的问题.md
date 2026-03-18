+++
title = "git项目批量拷贝文件后换行不一致的问题"
author = "CC"
date = 2026-03-02T00:00:00
tags = ["git"]
categories = ["note"]
draft = false
toc = true
+++

问题情境：Windows 环境 git 管理的项目，手动 copy 项目代码，本地原本是 CRLF 换行的文件变成了 LF 换行，导致所有文件都变成了 `modified` 状态。实际上大部分没有修改，只是换行变了。

解决方法：

```bash
# 移除暂存区的缓存
git rm --cached -r .
# 重新追踪项目文件
git add .
# 此时 modified 文件就只有实际修改的文件，而没有仅换行差异的，可以提交代码。
git commit -m "Fix line endings"
```

`git rm` 移除对文件的追踪，同时删除本地文件。`--cached` 只是从暂存区删除，保留工作目录中的文件。这个命令的效果是：

- 清空暂存区 ：移除所有已跟踪文件的暂存状态
- 保留工作文件 ：不会删除本地工作目录中的实际文件
- 更新 Git 跟踪 ：使所有文件变为"未跟踪"状态（untracked）

使用场景

1. 解决换行符问题 ：当换行符转换导致文件状态异常时，清除缓存后重新添加
2. 重新应用 .gitignore ：当修改了 .gitignore 文件后，需要清除缓存以忽略新的文件
3. 修复文件跟踪状态 ：当文件权限或属性变更导致 Git 错误跟踪时
4. 重新初始化 Git 跟踪 ：需要重新开始文件跟踪时
