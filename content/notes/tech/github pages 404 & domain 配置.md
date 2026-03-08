+++
title = "github pages 404 & domain 配置"
author = "CC"
date = 2023-11-30T00:00:00
tags = ["debug"]
categories = ["note"]
draft = false
toc = true
+++

### github pages 404: index.html not found {#github-pages-404-index-dot-html-not-found}

- 问题： github pages workflow 构建完毕后，打开页面显示 404，找不到 index.html。
- 原因： git settings &gt; Pages &gt; Build and Deployment, 设置为 from a branch + master。而 hugo 编译后提交在了 hg-pages 分支。
- 解决： 改了分支就可以了。

衍生问题： 在 settings 配置 custom domain，生效；提交代码再次触发 action 重新部署，失效。

- 原因： actions-gh-pages 没有拿到配置的 cname。
- 解决： 在 worflow 的配置中添加参数 `cname: custom.doamin.com` 。
