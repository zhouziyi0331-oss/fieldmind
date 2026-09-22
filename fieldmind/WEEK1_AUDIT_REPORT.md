# FieldMind 系统审计报告
生成时间: 2026-09-13T12:29:28.724289

## 📊 数据库审计

### index.db

- 大小: 0.01 MB
- 表数量: 1

| 表名 | 记录数 | 列数 |
|------|--------|------|
| package_index | 0 | 2 |

### build.db

- 大小: 0.17 MB
- 表数量: 3

| 表名 | 记录数 | 列数 |
|------|--------|------|
| info | 1 | 4 |
| key_names | 357 | 2 |
| rule_results | 357 | 8 |

### fieldmind.db

- 大小: 0.02 MB
- 表数量: 4

| 表名 | 记录数 | 列数 |
|------|--------|------|
| chunks_fts_simple_config | 1 | 2 |
| chunks_fts_simple_data | 2 | 2 |
| chunks_fts_simple_docsize | 0 | 2 |
| chunks_fts_simple_idx | 0 | 3 |

### migration_database.sqlite

- 大小: 0.05 MB
- 表数量: 11

| 表名 | 记录数 | 列数 |
|------|--------|------|
| Album | 5 | 3 |
| Artist | 3 | 2 |
| Customer | 3 | 13 |
| Employee | 8 | 15 |
| Genre | 1 | 2 |
| Invoice | 21 | 9 |
| InvoiceLine | 114 | 5 |
| MediaType | 2 | 2 |
| Playlist | 18 | 2 |
| PlaylistTrack | 97 | 2 |
| Track | 37 | 9 |


## 🔌 API 审计

- 总端点数: 654
- 重复端点: 44

### 按 HTTP 方法统计

- DELETE: 36
- GET: 359
- PATCH: 2
- POST: 235
- PUT: 22

## 📦 数据模型审计

- 模型文件数: 50

