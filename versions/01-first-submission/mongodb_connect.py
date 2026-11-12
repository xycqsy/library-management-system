
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# 加载项目根目录中的 .env 文件
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


def get_database():
    """获取 MongoDB 数据库连接"""

    host = os.getenv("MONGODB_HOST", "localhost")
    port = int(os.getenv("MONGODB_PORT", "27017"))
    database = os.getenv("MONGODB_DATABASE", "library")
    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")
    auth_source = os.getenv("MONGODB_AUTH_SOURCE", "library")

    if not username or not password:
        raise ValueError("请在 .env 中配置 MongoDB 用户名和密码")

    client = MongoClient(
        host=host,
        port=port,
        username=username,
        password=password,
        authSource=auth_source,
        serverSelectionTimeoutMS=5000
    )

    try:
        client.admin.command("ping")
        print("MongoDB 数据库连接成功！")
        return client, client[database]
    except Exception:
        client.close()
        raise


if __name__ == "__main__":
    client = None

    try:
        client, db = get_database()

        print("当前数据库：", db.name)
        print("图书数量：", db.books.count_documents({}))
        print("读者数量：", db.readers.count_documents({}))
        print("借阅记录数量：", db.borrow_logs.count_documents({}))

    except Exception as e:
        print("数据库连接失败：", e)

    finally:
        if client is not None:
            client.close()
            print("数据库连接已关闭")
