# 图书馆管理系统

这是数据库课程做的一个图书馆管理系统，使用 Python 编写，数据存放在 MongoDB 里，程序从命令行运行。

## 能做什么

- 查看、搜索、添加、修改和删除图书
- 查看读者信息，按学院和等级统计
- 登记借阅，查看借阅记录和逾期记录
- 查看图书分类、借阅趋势和热门图书统计
- 导出数据和备份 MongoDB

## 运行前准备

需要安装：

- Python 3.10 及以上
- MongoDB

Python 依赖已经写在 `requirements.txt` 里，安装方法：

```bash
pip install -r requirements.txt
```

如果想使用虚拟环境，可以这样安装：

```bash
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## MongoDB 配置

先复制一份配置文件：

```powershell
Copy-Item .env.example .env
```

然后打开 `.env`，把 MongoDB 的地址、数据库名、用户名和密码改成自己的配置。例如：

```dotenv
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_DATABASE=library
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_AUTH_SOURCE=library
```

我的 MongoDB 是放在虚拟机里的，如果你也这样使用，把 `MONGODB_HOST` 换成虚拟机 IP 就可以。`.env` 里是自己的连接配置，提交代码时不用把这个文件一起传上去。

## 运行程序

确认 MongoDB 已经启动后，在项目目录运行：

```bash
python main.py
```

启动后会显示菜单，输入对应的编号就能使用各项功能。

## 数据导出和备份

导出 `books` 和 `category_stats`：

```bash
python export_data.py
```

备份当前数据库中的集合、索引和视图：

```bash
python backup_mongodb.py
```

备份结果会放在 `backups` 文件夹里，每次运行会新建一个带时间的文件夹。项目中也保留了一份示例备份数据。

## 文件说明

```text
main.py              程序入口和菜单
mongodb_connect.py   MongoDB 连接配置
book_manager.py      图书相关操作
reader_manager.py    读者相关操作
borrow_manager.py    借阅和归还相关操作
stat_manager.py      统计功能
export_data.py       导出部分数据
backup_mongodb.py    备份 MongoDB
requirements.txt     Python 依赖
.env.example         配置文件示例
books.txt            图书示例数据
readers.txt          读者示例数据
borrow_logs.txt      借阅示例数据
exports/             导出的 JSON 文件
backups/             数据库备份文件
```

## 说明

项目使用的是 MongoDB 数据库，所以运行前需要先保证数据库能连接上。如果虚拟机没有启动，或者 IP 地址发生变化，需要重新修改 `.env`。

## 技术说明

### 程序怎么组织

程序从 `main.py` 开始运行。`main.py` 主要负责显示菜单、接收输入和调用功能，具体的数据库操作分在几个模块中：

- `book_manager.py`：图书的增删改查和评分排行
- `reader_manager.py`：读者查询以及学院、等级统计
- `borrow_manager.py`：借阅登记、借阅记录查询和归还实验
- `stat_manager.py`：使用 MongoDB 聚合管道做统计
- `mongodb_connect.py`：读取 `.env`，建立 MongoDB 连接

各个模块都接收同一个 `db` 对象，操作结束后由主程序统一关闭连接。

### 数据库集合

数据库名称默认是 `library`，项目中主要使用下面几个集合：

| 集合 | 用途 | 主要字段 |
| --- | --- | --- |
| `books` | 保存图书信息 | `isbn`、`title`、`author`、`publisher`、`category`、`price`、`stock`、`rating`、`tags`、`publish_date`、`borrow_count` |
| `readers` | 保存读者信息 | `card_no`、`name`、`college`、`level` |
| `borrow_logs` | 保存借阅流水 | `reader_card`、`book_isbn`、`borrow_date`、`status`、`return_date` |
| `category_stats` | 分类统计数据 | 由导出脚本读取 |
| `borrow_return_demo` | 归还功能的实验副本 | 从 `borrow_logs` 复制而来 |

`borrow_logs` 在当前数据库中是时间序列集合，所以 MongoDB 还会看到对应的 `system.buckets.borrow_logs`。这个系统集合由 MongoDB 自己维护，备份脚本不会把它当作普通集合导出。

### 主要操作流程

1. 程序启动后，先连接 MongoDB，并显示 `books`、`readers`、`borrow_logs` 和 `category_stats` 的数量。
2. 查询图书时，可以按书名、分类和价格范围组合查询，结果按书名排序。
3. 登记借阅前会检查读者是否存在、图书是否存在以及库存是否大于 0。
4. 借阅记录写入 `borrow_logs`，状态初始为“借出”。当前实验只登记流水，不会自动减少 `books.stock`。
5. 归还操作使用 `borrow_return_demo`，先复制一份借阅记录，再把对应记录改成“已归还”，不会直接修改正式的 `borrow_logs`。
6. 统计功能使用 MongoDB 的 `aggregate()`，分别统计图书分类、年度借阅次数和热门图书。

### 统计查询

`stat_manager.py` 中有三组聚合查询：

- 图书分类统计：统计每类图书的数量、库存总量和平均价格。
- 借阅趋势：按 `borrow_date` 的年份统计借阅次数，显示时区使用 `Asia/Shanghai`。
- 热门图书：按 `borrow_count` 从高到低排序，显示前几名图书。

### 备份文件怎么用

`backup_mongodb.py` 会读取数据库中的非系统集合，把每个集合保存成一个 JSON 文件，同时保存索引信息；如果遇到视图，则保存视图定义。备份目录中还会生成 `manifest.json`，可以用它查看本次备份了哪些内容。

这套脚本是项目里的逻辑备份，适合课程演示和保存示例数据。要在服务器故障后完整恢复 MongoDB，建议另外使用 MongoDB Database Tools 的 `mongodump` 和 `mongorestore`。

### 目前的实验限制

- 借阅登记不会自动扣减库存，库存需要在图书管理功能中单独修改。
- 归还功能目前只演示在副本集合中更新状态，正式借阅流水保持不变。
- 程序默认使用 `.env` 中的 MongoDB 用户登录，账号需要有对应数据库的读写权限。

## 简单检查

修改代码后，可以先检查 Python 文件是否有语法错误：

```bash
python -m py_compile main.py book_manager.py reader_manager.py borrow_manager.py stat_manager.py mongodb_connect.py export_data.py backup_mongodb.py
```

检查通过后，再启动主程序测试数据库连接和菜单功能：

```bash
python main.py
```
