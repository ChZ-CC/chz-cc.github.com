+++
title = "using git"
author = "CC"
date = 2020-03-08T00:00:00
tags = ["git", "版本管理"]
categories = ["note"]
draft = false
toc = true
+++

Git 是分布式版本控制系统，核心概念包括：

- **工作区**：实际编辑文件的目录
- **暂存区**：`git add` 后的文件存放区域
- **本地仓库**：`git commit` 后的版本历史
- **远程仓库**：如 GitHub、GitLab 等托管平台
<!--more-->

## **分支**的工作流程

1. 新建分支
2. 分支上的提交
3. 与主线同步
   1. git fetch origin
   2. git rebase origin/master
   3. **[注]**：在进行下一项（用rebase -i合并commit）之前，最好先与主线同步。
4. 合并分支上的多个commit
   1. `git rebase -i origin/master`
   2. `squash`和`fixup`命令，还可以当作命令行参数使用，自动合并commit。
       1. `git commit --fixup`, `git rebase -i --autosquash`, 主要在和主分支合并之前，整理自己分支上的commit们。把不重要的小修改合并掉。
5. 推送远程仓库
   - `git push --force origin my_branch` 本地rebase之后，和远程库不一样了，需要强制push。
6. 发出 pull request 请求

### 分支冲突的处理

- 分支的变动和合并会产生文件冲突，push的时候要保证本地仓库和远程仓库一致才行。如果远程仓库有变动，push会被拒绝。
  - 如果是同一个分支上的改动，用git pull获取/合并即可。
  - 但如果远程仓库的这个分支进行过merge（`git status`会提示你`Your branch and 'qb/master' have diverged, and have 2 and 1 different commits each, respectively.`），本地仓库在pull的时候会产生冲突，需要提交一个合并的commit才行。
  - 这时候应该用`git fetch`，然后提交变动（注意不要把自己的修改和fetch到的冲突一起提交，在fetch之前commit自己的修改），然后`git rebase origin/master`。
  - 这样本地仓库就变成以当前远程仓库为基础的版本，然后再push，不会产生多余的merge commit。

## 提交comment格式

```s
<type>[optional scope]: <description>

[optional body]

[optional footers]

# example

refactor!: drop support for Node 6

docs: correct spelling

feat(lang): add polish language
```

1. fix: patches a bug
2. feat: a new feature to de codebase
3. BREAKING CHANGE: a commit has a footer `BREAKING CHANGE` or appends a `!` after the `type[scope]`, introduces a breaking API change.
4. other types:
   - `build`: build system or external dependencies.
   - `chore`: routine
   - `ci`: ci configuration files and scripts.
   - `docs`: documentation changes.
   - `feat`: A new feature.
   - `fix`: A bug fix.
   - `perf`: A code change that improves performance.
   - `refactor`: A code change that neither fixes a bug nor adds a feature.
   - `revert`: revert.
   - `style`: Changes that do not affect the meaning of the code(white-space, formatting, missing semi-colons, etc).
   - `test`: Adding missing tests or correctiong existing tests.

> 现在都可以让 AI 帮你自动生成 commit 信息，这些似乎也都不重要了。 -- 2026-03-09

## 将已提交的文件从 git 中删除，但保留本地

1. `git rm --cached [-r] ./dir-or-file`
2. 将文件/目录加入 .gitignore
3. 提交

## 特殊分支操作

### 创建空白新分支

1. `git checkout --orphan branch-name`
2. `git rm -rf .` 清空目录

### detached 分支

当你检出一个 commit 而不是一个分支时，你就进入了 detached HEAD 状态。

- 如果不小心/或故意在 detached HEAD 状态下提交变更，这些变更不会被包含在任何分支中。
  - 你可以通过 `git checkout -b branch-name` 创建一个新的分支，将 detached HEAD 状态下的变更包含在该分支中。然后通过 merge 操作合并到你的开发分支或主分支上。
  - 或者回到开发分支/主分支后，通过 cherry-pick 命令将 detached HEAD 状态下的变更应用到开发分支/主分支上。

## Git Submodule

Git Submodule 允许在一个 Git 仓库中嵌入另一个 Git 仓库，主要用于：

- 引入第三方库或公共代码库
- 共享代码模块给多个项目
- 保持子项目的独立版本控制

### 基本工作流程

```bash
# 添加子模块
git submodule add <repository_url> <path>

# 克隆包含子模块的项目
git clone --recurse-submodules <main_repo_url>

# 更新子模块
git submodule update --remote
# 更新所有子模块
git submodule update --remote --recursive

# 查看子模块状态
git submodule status
```

### submodule 子模块更新

#### 方式一：子项目独立开发，主项目同步子模块的变更

1. 在子项目中开发，提交变更。
2. 主项目中更新子模块，执行 `git submodule update --remote` 更新子模块。
   1. 在主项目中更新子模块，其实就是更新子模块的引用，也就是子模块的 commit 指针。
3. 提交主项目的变更，推送变更到远程仓库。

#### 方式二：主项目中更新子模块，同时更新主项目和子模块

1. 在主项目中，进入子模块目录，进行修改，然后提交变更。
   1. `git commit` 提交变更。通常子模块处于某个版本的 detached 状态，这时候需要按上面*detached 分支* 的说明将变更提交对应分支上。
   2. `git push` 推送变更到远程仓库。
2. 主项目中更新子模块的引用。通常这时主分支的子模块引用也会更新，指向子模块的新的 commit。如果没有，执行 `git submodule update --remote` 更新子模块即可。
3. 同上，提交主项目的变更，推送变更到远程仓库。

## 遇到的问题

### rebase过程报错

```bash
$ git rebase -i origin/release
error: Unable to create 'D:/WorkSpace/question-bank-haoli/.git/index.lock': File exists.
```

遇到这个错误的时候，本地压根儿没有 index.lock 这个文件。忽视错误继续执行`git rebase --continue`有时候会继续下去，有时候会出其他错误。

```bash
$ git rebase --continue
fatal: could not read log file '.git/rebase-merge/message': No such file or directory
```

这个问题就无解了。上网查，说是尚未完成rebase强制中断导致的。

### github 访问问题

- 更新host
  - [GitHub Hosts](https://ineo6.github.io/hosts/)，作者的[git](https://github.com/ineo6)。
  - 更新hosts之后，刷新DNS。
    - MacOS: `sudo killall -HUP mDNSResponder`
    - Windows: `ipconfig /flushdns`

- <2025-04-29 Tue> 再次遇到无法访问 github 的问题
  - 现象
    - 许久没用，再次打开无法访问。更新了hosts，可以访问了，但是不久之后又不行了。用的是 <https://gitlab.com/ineo6/hosts/-/raw/master/next-hosts>
    - 设置 dns 为 8.8.8.8 GoogleDns，不行。
    - 不得已买了个 vpn，可以打开 github 主页。但是本地git命令不能用。
    - 查看 <https://www.githubstatus.com/> git状态页面，git operations degraded，只能等服务修好。
    - 之后 git 命令还是不行，连接 timeout。
  - 修复
    - `ssh -vT git@github.com` 查看debug信息，ping 了一下 github 的 ip，不通（8.8.8.8 的结果）。ping 另一个 ip 可以通（1.1.1.1）。
    - 查看 dns 解析的结果：`nslookup.exe github.com 1.1.1.1`，不加 dns 地址，使用环境默认的。
    - 修改 hosts 中 github.com 的 ip，然后再执行 `ssh -vT`，成功了。git 命令执行成功。
    - 此时关掉 vpn 依然奏效。

---

## 参考资源

- [Git Submodule 官方文档](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Pro Git Book - Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [git 使用规范流程](http://www.ruanyifeng.com/blog/2015/08/git-use-process.html)
- [ThoughtBot|Git](https://github.com/thoughtbot/guides/tree/main/git)
- [常用的git命令清单](http://www.ruanyifeng.com/blog/2015/12/it-cheat-sheet.html)
- [git工作流程](http://www.ruanyifeng.com/blog/2015/12/git-workflow.html)
- [git远程操作详解](http://www.ruanyifeng.com/blog/2014/06/git_remote.tml)
- [git分支管理策略](http://www.ruanyifeng.com/blog/2012/07/git.html)
- [git commit message conventions](https://www.conventionalcommits.org/en/v1.0.0/)
- [writing meaningful commit message](https://medium.com/@menuka/writing-meaningful-git-commit-messages-a62756b65c81)
- [Keep your branch clean with fixup and autosquash](http://fle.github.io/git-tip-keep-your-branch-clean-with-fixup-and-autosquash.html)
