| Hugo 字段  | 类型       | 格式                      | Obsidian 对应字段 | 类型       | 格式           |
| ---------- | ---------- | ------------------------- | ----------------- | ---------- | -------------- |
| title      | 字符串     | "标题"={ts}-{文件名}      | 文件名            | -          | -              |
| author     | 字符串数组 | ["作者1", "作者2"]        | -                 | -          | -              |
| date       | 日期时间   | YYYY-MM-DDThh:mm:ss±hh:mm | date              | 日期       | YYYY-MM-DD     |
| slug       | 字符串     | "URL路径"                 | -                 | -          | -              |
| tags       | 字符串数组 | ["标签1", "标签2"]        | tags              | 字符串数组 | 换行列表       |
| categories | 字符串数组 | ["分类1", "分类2"]        | type              | 字符串数组 | 换行列表       |
| draft      | 布尔值     | true/false                | draft             | 布尔值     | true/false     |
| toc        | 布尔值     | true/false                | -                 | -          | -              |
| -          | -          | -                         | aliases           | -          | -              |
| -          | -          | -                         | ts                | 字符串     | YYYYMMDDHHmmss |