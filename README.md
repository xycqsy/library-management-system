# 图书情报检索与统计平台技术文档

## 1. 系统说明

### 1.1 系统定位

本项目是一个基于 MongoDB 的图书情报检索与统计平台。系统采用 Python 命令行程序作为客户端，MongoDB 负责保存图书、读者和借阅流水。程序启动后建立一次数据库连接，再通过菜单调用各个业务模块。

项目目录中的 `books.txt`、`readers.txt` 和 `borrow_logs.txt` 是示例数据文件。当前程序默认读取已经部署好的 MongoDB 数据库，不会在启动时自动导入这三个文本文件。

### 1.2 技术栈和运行方式

| 项目    | 采用方案                             |
| ----- | -------------------------------- |
| 开发语言  | Python 3.12                      |
| 数据库   | MongoDB 6.x/7.x，默认端口 27017       |
| 数据库驱动 | PyMongo 4.x                      |
| 配置读取  | python-dotenv                    |
| 交互方式  | 命令行菜单                            |
| 数据格式  | BSON，导出时使用 MongoDB Extended JSON |

安装依赖并启动程序：

```bash
pip install -r requirements.txt
python main.py
```

MongoDB 运行在虚拟机时，`.env` 中的 `MONGODB_HOST` 应填写虚拟机 IP。连接模块读取 `MONGODB_HOST`、`MONGODB_PORT`、`MONGODB_DATABASE`、`MONGODB_USERNAME`、`MONGODB_PASSWORD` 和 `MONGODB_AUTH_SOURCE`，创建 `MongoClient` 后先执行 `ping`，连接失败就关闭客户端并抛出异常。

## 2. 系统结构

### 2.1 模块划分

```text
main.py              程序入口、菜单、输入校验和异常处理
mongodb_connect.py   环境变量读取和 MongoClient 创建
book_manager.py      图书检索、增删改和评分排序
reader_manager.py    读者查询及学院、等级统计
borrow_manager.py    借阅登记、记录查询和归还实验
stat_manager.py      分类、趋势和热门图书聚合统计
export_data.py       集合数据的 Extended JSON 导出
backup_mongodb.py    集合、索引、视图定义的逻辑备份
```

`main.py` 不直接实现数据库细节。菜单分支负责收集参数和确认高风险操作，再把 `db` 对象和业务参数传给对应模块。各模块使用 PyMongo 的 `find`、`find_one`、`insert_one`、`insert_many`、`update_one`、`update_many`、`delete_one`、`delete_many` 和 `aggregate` 完成数据库操作。

### 2.2 一次操作的处理流程

1. `get_database()` 从项目根目录加载 `.env`。

2. `MongoClient` 连接 MongoDB，并使用 `admin.command("ping")` 检查服务是否可用。

3. `main()` 显示集合数量和功能菜单。

4. 用户输入经过字符串、整数、浮点数和日期校验。

5. 业务模块执行查询或写操作，并根据 `matched_count`、`modified_count`、`deleted_count` 输出结果。

6. 程序退出时在 `finally` 中关闭 MongoDB 客户端。

新增、修改和删除操作都设置了二次确认；主循环捕获 `KeyboardInterrupt` 和一般异常，单次操作失败不会直接结束整个菜单程序。

## 3. 数据库设计

### 3.1 业务集合

数据库名称为 `library`，主要业务对象如下：

| 集合或对象                | 类型        | 关键字段                                                                                                         | 用途                 |
| -------------------- | --------- | ------------------------------------------------------------------------------------------------------------ | ------------------ |
| `books`              | 普通集合      | `isbn`、`title`、`author`、`publisher`、`category`、`price`、`stock`、`rating`、`tags`、`publish_date`、`borrow_count` | 图书基础信息、库存和借阅量      |
| `readers`            | 普通集合      | `card_no`、`name`、`college`、`level`                                                                           | 读者基本资料             |
| `borrow_logs`        | 时间序列集合    | `reader_card`、`book_isbn`、`borrow_date`、`status`、`return_date`                                               | 借阅流水               |
| `category_stats`     | 普通集合      | 统计结果字段                                                                                                       | 保存或导出分类统计数据        |
| `book_logs`          | 普通集合/实验集合 | 以日志字段为主                                                                                                      | 保存任务书中的图书日志数据      |
| `borrow_return_demo` | 普通集合      | 借阅流水字段加 `return_date`                                                                                        | 归还操作实验副本           |
| `book_in_stock`      | 视图        | 来源于 `books`                                                                                                  | 筛选 `stock > 0` 的图书 |

`isbn` 和 `card_no` 分别作为图书、读者的业务标识。借阅流水不嵌入图书或读者文档，而是通过 `book_isbn` 和 `reader_card` 保存引用关系。`borrow_logs` 是时间序列集合时，MongoDB 会在内部维护 `system.buckets.borrow_logs`；该桶集合属于数据库内部实现，不作为业务集合直接操作。

### 3.2 字段约束

程序层面对输入做以下约束：图书价格不能为负数，库存和借阅量必须是不小于 0 的整数，评分范围为 0 到 5，出版日期按 `YYYY-MM-DD` 转换为 Python `datetime`。标签输入使用逗号分隔，写入 MongoDB 时保存为字符串数组。

修改图书时只允许修改 `title`、`author`、`publisher`、`category`、`price`、`stock`、`rating`、`tags`、`publish_date` 和 `borrow_count`，不会通过菜单修改 `_id` 或 `isbn`。

### 3.3 索引设计

项目查询频率较高的字段是图书 ISBN、读者借阅证号、图书分类、借阅时间和借阅状态。数据库端可以使用以下索引降低检索和排序开销：

```javascript
db.books.createIndex({isbn: 1}, {unique: true})
db.books.createIndex({category: 1})
db.books.createIndex({rating: -1, title: 1})
db.readers.createIndex({card_no: 1}, {unique: true})
db.readers.createIndex({college: 1})
db.borrow_logs.createIndex({borrow_date: -1})
db.borrow_logs.createIndex({status: 1, borrow_date: -1})
```

时间序列集合的索引应结合 MongoDB 版本和时间序列配置检查。备份脚本会把普通集合的 `index_information()` 保存为独立的 `*.indexes.json` 文件，便于恢复时重新建立索引。

## 4. 功能实现

### 4.1 图书检索和维护

`book_manager.py` 的精确查询使用 `find_one({"isbn": isbn})`。组合检索动态拼接条件：书名使用不区分大小写的正则表达式，分类使用等值条件，价格范围使用 `$gte` 和 `$lte`。列表查询通过投影隐藏 `_id`，再按评分或书名排序。

写入功能包括单条插入和批量插入。单条插入捕获 `DuplicateKeyError`，避免 ISBN 或 `_id` 重复时程序直接退出。修改使用 `$set`，删除使用 ISBN 或分类条件；删除操作由主菜单先显示目标记录，再要求输入 `YES` 确认。

评分排行使用如下排序规则：先按 `rating` 降序，再按 `title` 升序，最后通过 `limit()` 截取指定数量。热门图书则根据 `borrow_count` 排序，两者统计口径不同。

### 4.2 读者查询

读者模块使用 `card_no` 查询单个读者，使用 `college` 查询学院。查看列表时只返回 `card_no`、`name`、`college` 和 `level`，减少无关字段输出。

学院统计和等级统计当前通过 `distinct()` 获取分组值，再对每组执行 `count_documents()`。这种写法直观，适合当前数据量；数据量较大时可以改成一个 `$group` 聚合管道，减少客户端和数据库之间的往返次数。

### 4.3 借阅和归还

借阅登记先分别查询读者和图书，只有读者存在且图书库存大于 0 时才向 `borrow_logs` 插入记录：

```python
{
    "reader_card": reader_card,
    "book_isbn": book_isbn,
    "borrow_date": datetime.now(timezone.utc),
    "status": "借出"
}
```

当前登记操作只写入借阅流水，不自动修改 `books.stock`，因此库存字段和借阅记录需要分开理解。借阅记录按 `borrow_date` 倒序查询；逾期查询使用 `status: "逾期"` 条件。

正式的 `borrow_logs` 保留借阅流水。归还菜单先把流水复制到 `borrow_return_demo`，再对副本执行 `update_many()`，将状态改为“已归还”并写入 UTC 时间的 `return_date`，用于演示归还更新过程。

### 4.4 统计聚合

统计模块包含三个聚合管道。

图书分类统计在 `$group` 阶段计算图书数、库存总量和平均价格，在 `$project` 阶段隐藏 `_id` 并使用 `$round` 保留两位小数，最后按库存总量降序排列。

借阅趋势从 `borrow_date` 提取年份，`$year` 使用 `Asia/Shanghai` 时区，之后通过 `$project` 生成年份标签，再按年份升序输出。

热门图书先按 `borrow_count` 降序、`title` 升序排序，再使用 `$limit` 取前 N 条，最后投影书名、分类、借阅次数和评分。

## 5. 数据导出和备份

### 5.1 JSON 导出

运行 `python export_data.py` 后，程序会在 `exports` 目录生成 `books.json` 和 `category_stats.json`。导出使用 `bson.json_util.dumps()`，因此 `ObjectId` 和 `datetime` 会保留 Extended JSON 标记，重新处理时不会被当成普通字符串。

### 5.2 逻辑备份

运行下面的命令备份当前数据库：

```bash
python backup_mongodb.py
```

脚本先读取 `listCollections`，排除 `system.` 开头的内部对象。普通集合会生成：

```text
books.json
books.indexes.json
readers.json
readers.indexes.json
...
manifest.json
```

视图不执行 `find()`，而是把视图定义保存为 `*.view.json`。`manifest.json` 记录数据库名、备份时间、集合类型、文档数量、文件名和错误信息。脚本只有在连接成功且没有集合导出错误时才删除旧的时间戳目录；连接失败时保留上一份成功备份。

这套脚本属于项目级逻辑备份，适合保存课程项目数据和检查集合内容。需要迁移完整 MongoDB 实例时，应使用 MongoDB Database Tools 的 `mongodump` 和 `mongorestore`。

## 6. 测试与运行检查

检查 Python 文件语法：

```bash
python -m py_compile main.py book_manager.py reader_manager.py borrow_manager.py stat_manager.py mongodb_connect.py export_data.py backup_mongodb.py
```

启动后的检查顺序建议为：先确认 MongoDB 连接和四个主要集合数量，再测试 ISBN 查询、组合检索、读者查询、借阅登记和统计菜单。写入类功能测试后，应重新查询对应集合，确认文档数、状态字段和时间字段变化。

## 7. 运行中的限制

MongoDB 位于虚拟机时，虚拟机未启动、网络模式变化或 IP 改变都会导致连接超时，需要先确认 MongoDB 服务和 `.env` 中的地址。借阅登记目前不会自动扣减库存，归还功能也只作用于 `borrow_return_demo`，如果后续要做成完整业务流程，需要把借阅、库存扣减和归还库存恢复放进事务或统一的业务函数中。

程序入口：

```bash
python main.py
```

