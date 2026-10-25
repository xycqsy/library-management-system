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
