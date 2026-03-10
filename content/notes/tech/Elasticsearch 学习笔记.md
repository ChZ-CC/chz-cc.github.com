+++
title = "Elasticsearch 学习笔记"
author = "CC"
date = 2023-03-24T00:00:00
tags = ["elasticsearch"]
categories = ["note"]
draft = false
toc = true
+++

Elasticsearch 学习笔记：包括搜索机制、分词分析、分布式架构、聚合分析、数据建模、安全认证和集群扩展等内容。涵盖了从基础概念到高级特性的完整学习路径，帮助掌握ES的搜索、存储和集群管理能力。
<!--more-->

- [Elasticsearch 基本概念与搜索入门](https://godleon.github.io/blog/Elasticsearch/Elasticsearch-getting-started/)

## search

- query: 搜索，打分
- filter: 筛选，不打分

## analyze

- char_filter: 分词前对字串的处理
  - html strip
  - mapping
  - pattern replace
- tokenizer: 分词，把一个字符串拆分成单个的词
  - Word Oriented Tokenizer
    - Standard Tokenizer
    - Letter Tokenizer
    - Lowercase Tokenizer
    - Whitespace Tokenizer
    - UAX URL Email Tokenizer
    - Classic Tokenizer
    - Thai Tokenizer
  - Partial Word Tokenizers
    - N-Gram Tokenizer: quick → [qu, ui, ic, ck]
    - Edge N-Gram Tokenizer: quick → [q, qu, qui, quic, quick]
  - Structured Text Tokenizer
    - Keyword Tokenizer
    - Pattern Tokenizer
    - Simple Pattern Tokenizer
    - Char Group Tokenizer
    - Simple Pattern Split Tokenizer
    - Path Tokenizer: /foo/bar/baz → [/foo, /foo/bar, /foo/bar/baz]
- filter: 又叫 token filter，是对分词结果做处理
  - word_delimiter: 单词定界 EN。将单词分解为子词，并对子词进行可选的转换
    - 词内分隔符，大小写分隔/驼峰，数字分隔，缩写's删除。
    - 参数：
      - generate_word_parts: "PowerShot" >> "Power" "Shot" [true]
      - generate_number_parts: "500-42" >> "500" "42" [true]
      - catenate_words: "wi-fi" >> "wifi" [false]
      - catenate_numbers: "500-42" >> "50042" [false]
      - catenate_all: "wi-fi-4000" >> "wifi4000" [false]
      - split_on_case_change: "PowerShot" >> "Power" "Shot" [true]
      - preserve_original: "500-42" >> "j" "2" "se" [true]
      - stem_english_possessive: "O'Neil's" >> "O", "Neil" [true]
      - protected_words: 数组，被分隔时的受保护词列表。
        - protected_words_path: 文件路径，受保护词表文件。
  - cjk_width: 日语片假名不分割，当做单词处理
    - "シーサイドライナー花は花" >> "シーサイドライナー", "花", "は", "花"
  - cjk_bigram: 二分
  - classic: 来自 "classic tokenizer"

## Course from time.geek

### 第二章 安装

### 第三章 入门

#### search api 概述

- precision / 精准率: 击中 / 实际返回的总数（击中+虚报）
- recall / 召回率: 击中 / 应该返回的总数（击中+漏报）

### 第四章 深入搜索

#### term/词项查询 VS text/全文查询

基于 term 的查询：

- 不分词，在倒排索引中查找准确的词项；
- 包括：term query / range query / exists query / prefix query / wildcard query
- 通过 constant score 将查询转为 filtering，避免算分，利用缓存，提高性能。

基于 text 的查询

- 索引和搜索都会先进行分词，生成查询词项列表。查询时，对每个词项逐个查询，把结果合并，为每个文档算分。
- 包括：match query / match phrase query / query string query
  - match query: 默认是 OR 词项是"或"的关系
    - operator: AND
  - match phrase query: AND, 词序有关系。
    - slop: 1 (词项中间可以出现其他词的数量)

#### Structured search / 结构化搜索

- 日期、Boolean、数字
- 文本：固定集合，如颜色集合：红、绿、蓝。（choices/enums）
- 使用 term 查询，返回 true/false。
- 例：
  - Boolean查询：term。
  - 数值查询：term、range-gte/lte。
  - 日期查询：range。"2014-01-01 00:00:00||+1M", "now-1y"
    - y : year
    - M : month
    - w : week
    - d : day
    - H/h : hour
    - m : minute
    - s : second
  - 多值/列表字段的查询
    - term：包含查询字段就会返回。
    - 想要精确匹配，增加一个count字段计数，判断是否完全一致。

#### 搜索的相关性计算

相关性 / relevance 算法：TF-IDF >> BM 25

可以指定相似度算法："custom_similarity": {"type": "BM25", "b": 0, "k1": 2}；mapping 的字段指定 "similarity": "custom_similarity"。

explain API：查看查询和算分的详情。

Boosting Relevance：控制相关度的一种手段，在索引、字段、查询子条件中。

- boost > 1，权重提升；
- 0 < boost < 1，权重降低；
- boost < 0，贡献负分。

#### bool query 多字段查询

bool 查询：一个或多个查询子句的组合。

- must: 必须匹配，贡献算分；
- should: 选择性匹配，贡献算分；
- must_not: filter context，必须不匹配；
- filter: filter context，必须匹配，不贡献算分。

bool 查询可以嵌套，会影响算分。

#### Dis Max Query 单字符串多字段查询

普通算分是每一个匹配字段的得分的总和。

Disjunction Max Query："dis_max" 将字段上最匹配的评分作为最终评分。

#### multi match 单字符串多字段查询

multi match query: 

- type: 
  - "best_fields" default，最高分。
  - "most_fields" 做累加。无法使用 operator；可以用 copy to，需要额外空间。
  - "cross_fields"
    - 跨字段搜索：地址信息 -> street/city/country/postcode
    - 可以使用 operator；设置权重。
- query
- fields
- tie_breaker
- minimum_should_match: "20%"

#### 混合多语言

- 不同索引使用不同语言
- 同一索引，不同字段使用不同语言
- 字段内混合不同语言

中文分词器

- HanLP：面向生产环境的自然语言处理工具包
  - 安装：./elastcsearch-plugin install https://github.com/zip_file_of_the_analyzer_you_want_to_install
  - hanlp: defualt
  - hanlp_standard
  - hanlp_index
  - hanlp_nlp
  - hanlp_n_short: N-最短路径
  - hanlp_dijkstra: 最短路径分词
  - hanlp_crf: 1.6.6+ 废弃
  - hanlp_speed
- ik 分词器
  - ik_max_word
  - ik_smart
- pinyin

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "user_name_analyzer": {
          "tokenizer": "whitespace",
          "filter": "pinyin_first_letter_and_full_pinyin_filter"
        }
      },
      "filter": {
        "pinyin_first_letter_and_full_pinyin_filter": {
          "type": "pinyin",
          "keep_first_letter": true,
          "keep_full_pinyin": false,
          "keep_none_chinese": true,
          "keep_original": false,
          "limit_first_letter_length": 16,
          "lowercase": true,
          "trim_whitespace": true,
          "keep_none_chinese_in_first_letter": true
        }
      }
    }
  }
}
```

自然语言与查询

- 不完全匹配，意思相同，希望能搜到。
  - quick brown fox
  - fast brown fox / jumping fox
  - jumped foxes
- 优化方法
  - 归一化：清除变音符
  - 抽词根：清除复数、时态差异
  - 同义词
  - 拼写错误

#### Search Template & Index Alias

Search Template：定义一个 contract，解耦程序与搜索，开发、搜索、性能各司其职。

```
POST _scripts/tmdb
{
  "script": {
    "lang": "mustache",
    "source": {
      "_source": [
        "title","overview"
      ],
      "size": 20,
      "query": {
        "multi_match": {
          "query": "{{q}}",
          "fields": ["title","overview"]
        }
      }
    }
  }
}
DELETE _scripts/tmdb

GET _scripts/tmdb

POST tmdb/_search/template
{
    "id":"tmdb",
    "params": {
        "q": "basketball with cartoon aliens"
    }
}
```

Index Alias：别名，零停机运维

- reindex：新建一个index，指向原有 alias；删除旧的 index 的alias。这样同一个 alias 就无痛切换到了新的索引上。
- 同一个 index 指向不同 alias，通过添加 filter 形成不同的索引。
- 不同的 index 指向同一个 alias，搜索多个 indices 的数据。

#### Function Score Query 优化算分

在查询结束后，对每一个匹配的文档重新算分，然后根据新的分数做排序。

- weight: 为单个文档设置（简单、不被规范化的）权重。
- field value factor: 用这个值来修改 _score，例如投票数、点赞数。
  - boost_mode: 默认乘。sum。
  - "modifier": "log1p"
  - "factor"
- random score: 广告投放。
  - seed
- 衰减函数: 以某个字段的值为标准，距离某个值越近，得分越高。
- script score: 完全有自定义脚本控制。

#### sugester 搜索引擎输入提示

原理：将输入文本分解为 token，然后在索引的字典中查找相似的 term 并返回。

实现：在 mapping 中设置字段 type=completion；搜索时使用 suggest，prefix=搜索内容，completion=对应字段。

```json
PUT articles
{
  "mappings": {
    "properties": {
      "title_completion":{
        "type": "completion"
      }
    }
  }
}
```

- Term suggester: 返回相似文本, leenshtein edit distance 算法实现。
  - suggest_mode 包括：
    - missing: 索引中已经存在就不提供建议；
    - popular: 推荐出现频率高的词；
    - always: 无论存在与否，都提供建议。

```
POST /articles/_search
{
  "size": 1,
  "query": {
    "match": {
      "body": "lucen rock"
    }
  },
  "suggest": {
    "term-suggestion": {
      "text": "lucen rock",
      "term": {
        "suggest_mode": "missing",
        "field": "body"
      }
    }
  }
}
```

- phrase suggester: 使用 phrase 关键字。在 term 基础上增加了额外逻辑。
  - suggest_mode: missing, popular, always
  - max_errors: 最多可以拼错的 term 数
  - confidence: 置信度，控制返回结果数量。默认为 1。

```
POST /articles/_search
{
  "suggest": {
    "my-suggestion": {
      "text": "lucne and elasticsear rock hello world ",
      "phrase": {
        "field": "body",
        "max_errors":2,
        "confidence":0,
        "direct_generator":[{
          "field":"body",
          "suggest_mode":"always"
        }],
        "highlight": {
          "pre_tag": "<em>",
          "post_tag": "</em>"
        }
      }
    }
  }
}
```

- complete suggester
  - auto complete / 自动补全，精准、即时。
  - 所以不用倒排索引，而是将 analyze 的数据编码成 FST 和索引一起存放。FST 会被 ES 加载进内存。
  - FST 只能用于前缀查找。

```
POST articles/_search?pretty
{
  "size": 0,
  "suggest": {
    "article-suggester": {
      "prefix": "elk ",
      "completion": {
        "field": "title_completion"
      }
    }
  }
}
```

- context suggerster
  - context 类型：category, geo 地理位置

#### cross data search 跨集群搜索

在每个集群上配置动态的设置：

```json
PUT _cluster/settings
{
  "persistent": {
    "cluster": {
      "remote": {
        "cluster0": {
          "seeds": [
            "127.0.0.1:9300"
          ],
          "transport.ping_schedule": "30s"
        },
        "cluster1": {
          "seeds": [
            "127.0.0.1:9301"
          ],
          "transport.compress": true,
          "skip_unavailable": true
        },
        "cluster2": {
          "seeds": [
            "127.0.0.1:9302"
          ]
        }
      }
    }
  }
}
```

- kibana > index pattern > create index pattern

### 第五章 分布式特性及分布式搜索的机制

#### 分布式模型及选主和脑裂问题

- 集群: 通过名字来区分，默认名字是 "elasticsearch"。
  - 修改集群名称：1. 配置文件；2. -E cluster.name=geettime
- 节点: 一个 elasticsearch 实例，本质是一个 JAVA 进程。生产环境，一台机器运行一个节点。
  - 修改节点名称：1. 配置文件；2. -E node.name=node2
  - ID：节点启动自动分配一个 UID，保存在 data 目录下。
- data node
- ingest node
- master node 的职责：
  - 处理创建、删除索引等请求
  - 决定分片被分配到哪个节点
  - 维护、更新 cluster state
  - 最佳实践： so in large or high-throughput clusters it is a good idea to avoid using the master-eligible nodes for tasks such as indexing and searching. You can do this by configuring three of your nodes to be dedicated master-eligible nodes. Dedicated master-eligible nodes only have the master role, allowing them to focus on managing the cluster. 
- coordinationg node: 处理请求信息，路由到正确的节点。默认是 true。将其他项设置为 false 成为 dedicated coordinating node。

- 集群状态
  - 所有节点信息
  - 所有索引和其他相关 mapping、setting 信息
  - 分片的路由信息
  - 每个节点都保存了集群状态信息，但只有 master 能修改，并负责同步给其他节点。
- 选举：
  - 节点之间相互 ping，ID 小的做 master。
- 脑裂：
  - 节点之间网络不通，产生多个 master 节点。
  - 如何避免：设置 quorum（仲裁）限定选举条件，只有 master-eligible 节点数大于 quorum 才进行选举。
    - quorum = （master-eligible 数量 / 2） +  1
    - 7.0 无需配置
- dedicated master-eligible node / default distribution
  - node.master: true 
  - node.voting_only: false 
  - node.data: false 
  - node.ingest: false 
  - node.ml: false 
  - xpack.ml.enabled: true 
  - node.transform: false 
  - xpack.transform.enabled: true 
  - node.remote_cluster_client: false 
- dedicated master-eligible node / oss-only disctrbution
  - node.master: true 
  - node.data: false 
  - node.ingest: false 
  - node.remote_cluster_client: false

#### 38 | 分片与集群的故障转移

#### 39 | 文档分布式存储

#### 40 | 分片及其生命周期

#### 41 | 剖析分布式查询及相关性算分

#### 42 | 排序及Doc Values&Fielddata

#### 43 | 分页与遍历：From, Size, Search After & Scroll API

#### 44 | 处理并发读写操作

### 第六章：深入聚合分析 (4讲)

#### 45 | Bucket & Metric聚合分析及嵌套聚合

#### 46 | Pipeline聚合分析

#### 47 | 作用范围与排序

#### 48 | 聚合分析的原理及精准度问题

### 第七章：数据建模 (7讲)

#### 49 | 对象及Nested对象

一个字段包含多个数值对象（list of object [{"a": 1, "b":2}]），需要对对象进行查询，使用 nested 对象类型。

#### 50 | 文档的父子关系

关联文档，父子分开存储，适合子文档更新频繁的情况，例如 博客的评论。

#### 51 | Update By Query & Reindex API

- update_by_query: 索引新增字段，更新旧 doc 的索引
- _reindex: 字段类型更改、分片数量改变、跨集群迁移

#### 52 | Ingest Pipeline & Painless Script

- Ingest Pipeline
  - ingest node: 在 index 和 bulk 前，对数据进行预处理。
  - vs Logstash
    - ingest node: 1. API获取数据，写入es；2. 不支持缓冲；3. es 内置，可以开发扩展插件；4. 无需额外部署。
    - Logstash: 1. 支持不同数据源，写入不同数据库；2. 列队，支持重写；3. 支持大量插件，可定制开发；4. 需要部署，增加架构的复杂度。
- Painless
  - 高性能、安全；支持所有 java 数据类型和 java API 子集。
  - 通过 Painless 脚本访问字段：
    - ingestion : ctx.field_name
    - update : ctx._source.field_name
    - search & aggregation : doc["field_name"]

#### 53 | Elasticsearch数据建模实例

创建数据模型：第三范式，ES 反范式/denomalization。

- 设置字段类型
  - text: 分词，不支持聚合分析和排序。
    - fielddata: true 支持聚合、排序
  - keyword: 不分词。
    - ES 默认为文本类型/text的字段设置一个 keyword 字段。
  - 数字：
    - 贴近类型
    - 枚举值 设置为 keyword
- 检索
  - index: false, 不需要搜索
  - index_options.norms: false, 不需要归一化。
- 聚合和排序
- 额外存储
  - store: true, 存储该字段的原始内容；
  - _source.enable: false, 节约磁盘。
    - 不建议，因为无法做 reindex 或 update。
    - 优先考虑增加压缩比。

#### 54 | Elasticsearch数据建模最佳实践

- kibana 对 nested 和父子结构支持不好。
- 防止字段无线扩张
  - Dynamic 设置 false/strict 控制字段的增加。
  - 使用 nested object 设置 key value。
- 避免使用正则查询
- 初始化空值，避免 null 值对聚合结果的影响。
- 加入 meta 信息，对 mapping 做版本控制（GitHub）。

#### 55 | 第二部分总结回顾

### 第八章：保护你的数据 (3讲)

#### 56 | 集群身份认证与用户鉴权

ES 集群

- security 插件：search-guard、readonly rest
- xpack.secutity.enable=true 开启权限管理
  - es 默认有一些管理员账号。
  - `$ bin/elasticsearch-setup-passwords interactive` 在命令行配置用户密码。

Kibana :: RBAC(role based access control)

- kibana-path/config/kibana.yml, 取消 username 和 password 的注释。
- 设置 role，添加 user。

#### 57 | 集群内部安全通信

加密通讯：TLS(Trusted Certificate Authority/CA)

认证级别
- certificate: 节点加入需要使用相同 CA 签发的证书
- full verification: certificate + host name 和 ip 地址验证
- no verification: 任何节点都可加入。开发环境，用于诊断。

创建证书
- 创建 CA：`bin/elasticsearch-certutil ca`。生成一个 elastic-stack-ca.p12 文件。
- 签发证书：`bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12`。生成一个 elastic-certificates.p12 证书文件。
- `mv elastic-certificates.p12 config/certs`

配置 
- xpack.security.enable=true 
- xpack.security.transport.ssl.enable=true 
- xpack.security.transport.ssl.verification_mode=cerificate
- xpack.security.transport.ssl.keystore.path=certs/elastic-certificates.p12
- xpack.security.transport.ssl.truststore.path=certs/elastic-certificates.p12

#### 58 | 集群与外部间的安全通信

ES 的 HTTPS 配置，同上打开 ssl。

Kibana 的 HTTPS 配置 -- kibana.yml

- Kibana 连接 ES HTTPS
  - 签发 .pem 证书：`openssl pkcs12 -in elastic-certificates.p12 -cacerts -nokeys -out elastic-ca.pem`。把 .pem 文件copy到 es 的 config/certs 下。
  - 配置 kibana.yml，取消注释 `elasticsearch.hosts: ["https://localhost/9200"]` 及下面两行。
- Kibana 使用 HTTPS 访问
  - `bin/elasticsearch-certutil ca --pem` 生成一个 zip 文件，包含 ca.cert 和 ca.key 两个文件
  - cp ca.* kibana-path/config/certs（kibana 的 config/certs 下还有 .p12 的文件？）
  - kibana.yml 取消注释 server.ssl.enable: true 及下面几行。

### 第九章：水平扩展Elasticsearch集群 (6讲)

#### 59 | 常见的集群部署方式

1. 配置单一职责的节点
  - master: 3 台，低性能。
  - data: 多台，高性能。
  - ingest << write
  - coordinate << kibana | >> read, aggregation
2. LB(load balance)

#### 60 | Hot & Warm架构与Shard Filtering

- hot/warm node
  - 不同机器、不同数据
    - hot: 高配置、ssd、新数据
    - warm: 大容量磁盘、只读
  - 步骤
    - 标记节点：node.attr.my_node_type=hot/warm
      - `GET /_cat/nodeattr?v` 查看节点属性
    - 配置 hot 数据
      - 设置 index 的 settings：

```
PUT logs-2019-06-27
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 0,
    "index.routing.allocation.require.my_node_type": "hot"
  }
}
```

    - 旧数据移动到 warm 节点

```
PUT logs-2019-06-27/settings
{
  "index.routing.allocation.require.my_node_type": "warm"
}

查看节点分片信息
GET _cat/shards?v
```

- Rack Awareness 机架

  机架断电，同时丢失多个节点。Rack Awareness 机制可以尽量避免同一个索引的主、副分片分配在同一个机架的节点上。

  - 标记 Rack 节点

```
bin/elasticsearch  -E node.name=node1 -E cluster.name=geektime -E path.data=node1_data -E node.attr.my_rack_id=rack1
bin/elasticsearch  -E node.name=node2 -E cluster.name=geektime -E path.data=node2_data -E node.attr.my_rack_id=rack1
```

  - 配置集群

```
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "my_rack_id"
  }
}
```

- Fore awareness: 副本无法分配到主分片的节点
  - 标记 rack
  - 配置集群

```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "my_rack_id",
    "cluster.routing.allocation.awareness.force.my_rack_id.values": "rack1,rack2"
  }
}
GET _cluster/settings
```

#### 61 | 分片设计及管理

- 分片数 > 节点数
  - 新节点加入，分片可以自动分配
  - 分片重新分配时，不会有downtime
- 多分片的好处：
  - 并行查询
  - 分散写入
- 分片过多的副作用
  - 每个分片是一个 Lucene 索引，会使用机器资源。过多的分片导致额外的性能开销
    - Lucene indices / file dscriptor / RAM / CPU
    - 每次搜索需要从每个分片上获取资源
    - 分片的 meta 信息由 master 节点维护，过多的分片增加管理负担。
  - 经验值：分片总数在 10 万以内。
- 推荐配置
  - 物理大小：日志类 < 50GB; 搜索类应用 < 20 GB
    - 提高 update 性能
    - merge 时减少所需资源
    - 节点丢失，更快的恢复
    - 便于集群内 rebalancing
  - 副本数量：增加写的负担、提高读的性能。
- index.routing.allocation.total_shards_per_node=1 索引的分片在一个节点上只能有一个。

#### 62 | 如何对集群进行容量规划

根据业务需求。
- 搜索 日志分离
  - 搜索 ssd
    - 数据量稳定、增量少、搜索频繁
  - 日志 hot warm
    - 写入、查询近期、无修改。
- 及时监控，扩容
  - 高可用 3 台 dedicated master node
  - 聚合查询 + coordinate node
  - 写入 + ingest node
- date math 的方式写入时间序列数据（日志）
- index alias

#### 63 | 在私有云上管理Elasticsearch集群的一些方法

- 集群管理
  - 容量不足，增加节点
  - 节点丢失，修复、更换节点（rack awareness）
  - 版本升级；数据备份；滚动升级

ECE - elastic cloud enterprise，单个控制台，管理多个集群
- 支持不同方式的集群部署、跨数据中心、部署 Anti Affinity
- 统一监控所有集群的状态。
- 图形化操作
  - 增删节点
  - 升级集群
  - 滚动更新
  - 自动数据备份

基于 Kubernetes 的方案
- 基于容器技术，使用 operator 模式进行编排管理
- 配置管理多个集群
- 支持 hot & warm
- 数据快照和恢复

建构自己的管理系统
- 基于虚拟机
- 基于 kubernates

#### 64 | 在公有云上管理与部署Elasticsearch集群

### 第十章：生产环境中的集群运维 (10讲)

#### 65 | 生产环境常用配置与上线清单

系统设置：参考文档 "Set up Elasticsearch"
- 禁用swap
- ulimit（进程可以同时打开的文件数量）
- 。。。

最佳实践：
- jvm
  - 避免修改默认配置
  - Xms 和 Xmx 一样大，避免 heap resize 引发停顿
  - Xmx 不超过物理内存的 50%，不大于 32G（提高效率，小于32时会启用内存对象指针压缩技术）。
  - JVM 必须使用 server 模式
  - 关闭 JVM Swapping
- 网络
  - 单集群不要夸数据中心（不要使用WAN，广域网，英語：Wide Area Network）
  - 节点之间的 hops 越少越好（router 跳）
  - 多块网卡，最好将 transport 和 http 绑定到不同网卡，并设置不同的防火墙
  - 按需为 coordinating node 和 ingest node 配置负载均衡
- 内存
  - 搜索类：1:16，日志类：1:48 ~ 1:96 之间。
  - 例：1T数据，一个副本 = 2T 总数据量
    - 搜索类：31 × 16 = 496GB 约等于 400G，那么需要至少 5 个节点。
    - 日志类：31 × 5 = 1550GB，两个节点即可。
- 存储
  - SSD，本地存储，避免使用云存储。
  - 本地指定多个 path.data 以支持使用多块磁盘
  - ES 提供了很好的 HA(High avalibity) 机制，无需配置 RAID 1/5/10
  - warm 节点可以使用 spinning disk，但要关闭 concurrent merge
    - index.merge.scheduler.max_thread_count: 1
  - trim SSD（参考文章：is-your-elasticsearch-trimmed）
- 硬件
  - 中等配置值
  - 一台机器不要运行多个节点
- 集群设置：Throttles 限流，密码多任务对集群产生性能影响
  - cluster.routing.allocation.node_concurrent_recoveries:2
  - cluster.routing.allocation.cluster_concurrent_rebalance:2
- 安全配置

#### 66 | 监控Elasticsearch集群

```
GET _cluster/stats
GET _nodes/stats
GET my_index/_stats
GET _cluster/pending_tasks
GET tasks

GET _nodes/thread_pool
GET _nodes/stats/thread_pool
GET _cat/thread_pool?v
GET _nodes/hot_threads
GET _nodes/stats/thread_pool

# 设置 Index Slowlogs
# the first 1000 characters of the doc's source will be logged
PUT my_index/_settings
{
  "index.indexing.slowlog":{
    "threshold.index":{
      "warn":"10s",
      "info": "4s",
      "debug":"2s",
      "trace":"0s"
    },
    "level":"trace",
    "source":1000  
  }
}

# 设置查询
DELETE my_index
//"0" logs all queries
PUT my_index/
{
  "settings": {
    "index.search.slowlog.threshold": {
      "query.warn": "10s",
      "query.info": "3s",
      "query.debug": "2s",
      "query.trace": "0s",
      "fetch.warn": "1s",
      "fetch.info": "600ms",
      "fetch.debug": "400ms",
      "fetch.trace": "0s"
    }
  }
}
```

#### 67 | 诊断集群的潜在问题

health api

- green: 分片有被正确的分配，不一定没有问题
- 负载过高导致集群失联，master/data node 宕机
- 副本丢失，数据可靠性受损
- 集群压力过大，数据写入失败
- 负载不均衡
- 优化分片，segment
- 规范操作：利用别名 / 避免 dynamic mapping

阿里云Elasticsearch智能优化运维工具：EYou

#### 68 | 解决集群Yellow与Red的问题 -- allocation/explain api

- yellow: 副本分片没有分配
- red: 主分片没有分配
- green: 主副分片都正常配置

```
GET _cluster/health
GET _cluster/health?level=indices
GET _cluster/health/my_index
GET _cluster/health?level=shards
GET _cluster/allocation/explain
```

#### 69 | 提升集群写性能

- 客户端：多线程、批量写（bulk）
  - 测试，确定最佳文档数
- 服务器：分解问题，单节点调整测试，压榨硬件资源，达到最高吞吐量。
  - 更好的硬件
  - 线程切换 / 堆栈状况
  - 优化手段：
    - refresh interval 降低io
    - 降低 cpu 和存储开销：不必要的分词 / 不需要的 doc_value / 字段尽量保证相同顺序
      - index: false -- agg only
      - norms: false -- 不算分
      - 不用 dynamic mapping
      - index_options 控制哪些内容可以被添加到倒排索引中。
      - 关闭 _source, 减少 IO 操作 -- 指标型数据，不能 reindex 和 update 
    - shard filtering / write load balancer
      - 副本设为 0，写入完毕后再改回来。
    - 调整 bulk 线程池和列队
      - 5～15MB
      - timeout: 60s
      - 轮询打到不同节点
      - 线程池：cpu 核数 + 1，避免上下文切换。
      - 列队大小适当增加。太大会占用过多内存增加 GC 负担。

#### 70 | 提升集群读性能

- denormalize 不要搞关系型
  - nested 类型，查询慢几倍；
  - parent/child 类型，查询慢几百倍。
- 建模
  - 先计算，再保存到es。避免 script 计算；
    - ingest pipeline，计算并写入某个字段
  - 尽量使用 filter context，利用缓存，减少不必要的算分；
  - 结合 profile、explain api 分析慢查询的问题，持续优化数据模型
    - 严禁使用 * 开头的通配符 term 查询
- 聚合查询
  - 控制聚合的数量，减少内存开销。
  - 将 query scope 改为 filter bucket。
- 优化分片
  - 避免 over sharding
  - 控制 分片尺寸
  - force-merge read-only 索引
    - 使用基于时间序列的索引，将只读的索引进行 force-merge，减少 segment 数量。

#### 71 | 集群压力测试

压力测试
- 目的：容量规划 / 性能优化 / 版本间的性能比较 / 性能问题诊断 / 系统维稳 / 系统极限和隐患
- 步骤：
  - 测试计划：确定测试场景和测试数据集
  - 脚本开发
  - 测试环境搭建 & 运行测试
  - 结果分析

ES Rally，基于 python3 的压力测试工具。
- 自动创建、配置、运行测试，并销毁 ES 集群
- 支持不同的测试数据的比较，支持将数据导入 ES 集群，进行二次分析
- 搜集测试的指标数据，方便对测试结果进行深度分析

#### 72 | 段合并优化及注意事项

force merge

#### 73 | 缓存及使用Breaker限制内存使用

- node query cache
  - 每个节点有一个 node query cache
  - 节点上的所有 shard 共享
  - 置缓存 filter context 相关内容
  - 采用 LRU 算法
  - 配置(静态 yaml)
    - node level: indices.queries.cache.size: "10%"
    - index level: index.queries.cache.enabled: true
- shard request cache 缓存分片上的查询结果
  - 只缓存 size=0 的结果，不缓存 hits。
  - 会缓存 aggregation 和 suggestions
  - cache key：
    - LRU 算法，整个 json 查询串作为 key。
    - 查询时尽量保持字段顺序相同
  - 配置(yaml)
    - indices.requests.cache.size: "1%"
- fielddata cache
  - text 类型以外 doc_value， aggregation 的 global ordinals 也在 fielddata cache 中。
  - text 类型的字段 打开 fielddata 才能进行聚合和排序，不推荐！！
  - 配置
    - indices.fielddata.cache.size (默认无限制)

常见内存问题

1. segment 个数过多，导致full GC。
  - 解决：force-merge 把 segment 合并成一个。
2. fielddata cache 过大，full GC
  - fielddata cache 的构建比较重，es 不会主动释放，所以值应该设置的保守一些。业务有需求，通过增加节点、扩容解决。
3. 复制嵌套聚合，full GC
  - dump 分析，大量 bucket 对象，查看日志，发现复杂聚合嵌套。
  - 解决：聚合优化

circuit breaker 断路器，避免不合理操作引发的 OOM(out of memrey)。
- GET /_node/stats/breaker?
  - tripped > 0, 有过熔断
  - limit_size 与 estimated_size 越接近，越可能引发熔断

#### 74 | 一些运维的相关建议

- rolling upgrade: 没有 downtime
- full cluster restart
  - 更新期间集群不可用
  - 速度更快
  - 步骤：
    - 停止索引，备份集群
    - disable shard allocation

```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "primaries"
  }
}
```

    - 执行 synced flush
      POST _flush/synced
    - 关闭并更新所有节点
    - 运行所有 master 节点，然后运行其他节点
    - 集群变黄后，打开 shard allocation
- cluster reroute 移动分片
- 从集群中移除一个节点

### 第十一章：索引生命周期管理 (2讲)

#### 75 | 使用Shrink与Rollover API有效管理时间序列索引

索引管理 api
- open/close index
  - 查看索引是否存在: HEAD test
  - 关闭索引 -- 索引存在，无法查询、搜索: POST /test/_close
  - 打开索引: POST /test/_open
- shrink index: 将主分片数收缩到较小的值
  - 场景：1. 数据量小，需要重新设定主分片数；2. 从 hot 到 warm 后，降低主分片数。
  - 过程：
    1. 使用源索引相同配置创建新索引。
      - 源分片数必须是目标分片数的倍数(必须大于目标分片数)；如果源分片数是素数，目标分片数只能是 1。
      - 分片必须是只读；所有分片必须在同一个节点；集群必须是 green。
        - 设置 readonly：{"settings": {"index.blocks.write": true}}
      - 如果文件系统支持硬链接，会将 segments 硬链接到目标索引，性能比 reindex 好。
    2. 完成后，删除源索引。
- split index: 扩大主分片数
- rollover index: 索引超过一定尺寸/时间后，创建新索引。
  - 当满足一定条件时，rollover index 可以将一个 alias 指向一个新的索引。
    - 存活时间
    - 最大文档数
    - 最大文件尺寸
  - 需要结合 index lifecycle management policies 使用。
  - 例：结尾是数字的索引可以自动生成新的；不是数字的可以指定新索引名

```
POST /nginx_logs_write/_rollover[/new_index_name]
{
  "conditions": {
    "max_age":   "1d",
    "max_docs":  5,
    "max_size":  "5gb"
  }
}
```

    - 设置索引 alias 的 is_write_index=true：rollover 之后 alias 包含旧的索引；写入文档时保存到 is_write_index==true 的分片上，也就是最新的分片。

```json
PUT apache-logs1
{
  "aliases": {
    "apache_logs": {
      "is_write_index":true
    }
  }
}
```

- rollup index: 对数据进行处理后，重现写入，减少数据量。

#### 76 | 索引全生命周期管理及工具介绍

curator 基于 python 的命令行工具

index lifecycle management
- ILM policy
- phase
  - hot phase
  - warm phase
  - cold phase
  - delete phase
- kibana 中使用
- api 使用

```json
PUT _cluster/settings
{
  "persistent": {
    "indices.lifecycle.poll_interval":"1s"
  }
}
```

### 第十二章：用Logstash和Beats构建数据管道 (3讲)

#### 77 | Logstash入门及架构介绍

[source data] input >> [event] filter >> output [targe data]

- codec(code/decode): 将原始数据 decode 成 event；将 event encode 成目标数据。
  - line
  - json
  - multiline
  - dots
- event: 是个 Java Object，在 filter 阶段可以进行增删改查。
- queue: 支持列队。
  - in memory queue
  - persistent queue

配置：
- bin/logstash -f demo.conf
- pipeline: input -- filter -- output
  - 每个阶段都有很多插件可用。
- config 文件的结构

```
input {
  file {
    path => "/Users/yiruan/dev/elk7/logstash-7.0.1/bin/movies.csv"
    start_position => "beginning"
    sincedb_path => "/dev/null"
  }
}
filter {
  csv {
    separator => ","
    columns => ["id","content","genre"]
  }
  mutate {
    split => { "genre" => "|" }
    remove_field => ["path", "host","@timestamp","message"]
  }
  mutate {
    split => ["content", "("]
    add_field => { "title" => "%{[content][0]}"}
    add_field => { "year" => "%{[content][1]}"}
  }
  mutate {
    convert => {
      "year" => "integer"
    }
    strip => ["title"]
    remove_field => ["path", "host","@timestamp","message","content"]
  }
}
output {
  elasticsearch {
    hosts => "http://localhost:9200"
    index => "movies"
    document_id => "%{id}"
  }
  stdout { codec => rubydebug }
}
```

#### 78 | 利用JDBC插件导入数据到Elasticsearch

需求：将数据库的数据同步、更新到 ES。

- 创建 alias，只显示没有被标记 deleted的用户

```json
POST /_aliases
{
  "actions": [
    {
      "add": {
        "index": "users",
        "alias": "view_users",
        "filter" : { "term" : { "is_deleted" : false } }
      }
    }
  ]
}
```

#### 79 | Beats介绍

Beats, light weight data shippers. 收集数据，支持与 logstash 或 ES 集成。基于 Go lang

- matricbeat: 定期搜集操作系统、软件的指标数据
  - 可聚合、定期搜索。
  - 指标数据存入 ES，通过 Kibana 进行实时的数据分析。
- packetbeat: 实时的网络数据分析，监控应用服务器之间的网络流量。

### 第十三章：用Kibana进行数据可视化分析 (4讲)

#### 80 | 使用Index Pattern配置数据

测试数据：设置 mapping > 导入数据到 ES

Kibana > management > index pattern

#### 81 | 使用Kibana Discover探索数据

Kibana > discover

- 加过滤器：展开字段--加号/value==，星号/exist。修改。
- add 字段到展示页面，点击查看数据分布。
- search

#### 82 | 基本可视化组件介绍

Kibana > visualiztion

饼图、面积图（area）、柱状图......

- matrics / buckets agg
- inspect: 查看数据，view request 查看查询语句。

#### 83 | 构建Dashboard

定制多个可视化组件。

### 第十四章：探索X-Pack套件 (6讲)

#### 84 | 用Monitoring和Alerting监控Elasticsearch集群
#### 85 | 用APM进行程序性能监控
#### 86 | 用机器学习实现时序数据的异常检测（上）
#### 87 | 用机器学习实现时序数据的异常检测（下）
#### 88 | 用ELK进行日志管理
#### 89 | 用Canvas做数据演示

### 实战1：电影搜索服务 (3讲)

#### 90 | 项目需求分析及架构设计
#### 91 | 将电影数据导入Elasticsearch
#### 92 | 搭建你的电影搜索服务

### 实战2：Stackoverflow用户调查问卷分析 (3讲)

#### 93 | 需求分析及架构设计
#### 94 | 数据Extract & Enrichment
#### 95 | 构建Insights Dashboard

### 备战：Elastic认证 (5讲)

#### 96 | Elastic认证介绍

#### 97 | 考点梳理
#### 98 | 集群数据备份
#### 99 | 基于Java和Elasticseach构建应用
#### 100 | 结课测试&结束语

## Note

### 索引分片设置

参考文章: https://opster.com/guides/elasticsearch/data-structuring/elasticsearch-number-of-shards/

- 多分片，bulk写入时分散到每个分片，分布式并行写入，效率高。
- 分片数大于节点数时，分片数最好是节点数的倍数。
- 为了更快的构建索引，索引分片应该至少等于集群节点数。即每个节点一个分片。
- 搜索时，多分片需要 merge，计算更复杂。数据少的话，一个分片最快。
  - 多分片时，搜索结果的相关性和分值会有道影响（relevance and score）。参考：https://www.elastic.co/guide/en/elasticsearch/guide/master/relevance-is-broken.html
