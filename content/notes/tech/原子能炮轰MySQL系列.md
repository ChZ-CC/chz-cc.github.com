+++
title = "原子能炮轰MySQL系列"
author = "CC"
date = 2025-09-11T00:00:00
tags = ["数据库"]
categories = ["note"]
draft = false
toc = true
+++

### 视频链接

[[音视频|video]] up主：原子能

- [炮轰MySQL第二弹](https://www.bilibili.com/video/BV1M1Koz6EW1)
- [炮轰MySQL第三弹](https://www.bilibili.com/video/BV12We7z8EZR)

### 外键、索引和事务

- 外键 索引 奇怪的锁表逻辑。
  - 买家表 buyers(id, username)
  - 订单表 orders(id, buyer_id, order_status) 
    - index(buyer_id, order_status) 
    - foreign key (buyer_id)...
  - 1.修改订单的买家  update orders set buyer_id = 2 where id = 1; -- buyers 买家表会被锁。（正常）
  - 2.修改订单的状态  update orders set order_status = 0 where id = 1; -- buyers 买家表还是会被锁。（X）因为订单表的 index
    - 官方：这不是bug，建议：删除索引
    - 用户：再加一个索引 index(buyer_id)，也就不会锁买家表。
- 事务不包含 DDL 语句。
  - 1.INSERT INTO new_table (id, sth) SELECT id, data FROM old_table;
  - 2.DROP TABLE old_table;   // 如果 commit 失败，1. 3. 将回退，但是 2 无法回退，导致数据无法找回。
  - 3.INSERT INTO audit_log (info, created_at) VALUES ("已迁移数据并删除旧表"， NOW());
  - 4.COMMIT;

### 奇葩隔离等级设定

| Isolation level\read phenomenon | Dirty read | Non-Repeatable read | Phantom read |
| ------------------------------- | ---------- | ------------------- | ------------ |
| Serializable                    | no         | no                  | no           |
| Reapeatable read                | no         | no                  | yes          |
| Read commit                     | no         | yes                 | yes          |
| Read uncommitted                | yes        | yes                 | yes          |

- Serializable: 只会看到事务开始时的全局景象。
- Repeatable read: Phantom read(幻读) 可以读到别人 insert 和 delete 的结果。二次 select 看到不同的 rows。
- Read commit: Non-Repeatable read(不可重复读) 可以读到别人 update 的结果。二次 select 看到 同一个 row 不同的值。
- Read uncommitted: Dirty read(脏读) 可以读到别人未 commit 的结果。

MySQL 的默认隔离级别 repeated read；其他数据库 read committed。但，MySQL 的隔离等级特性杂糅混乱：

- 纯 select 命令 -- 使用 repeatable read，获取  update 前的数据。
  - select * from customer -- 看到的是update前的数据
- 混合 select 和 insert 命令 -- 使用 read committed  获取 update 后的数据。
  - insert into costomer_backup select * from costomer; -- 选择的是 update 后的数据存入备份表，跟上面select看到的不一样。
