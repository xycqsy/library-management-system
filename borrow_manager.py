
from datetime import datetime, timezone
from pymongo.errors import PyMongoError


def register_borrow(db, reader_card, book_isbn):
    """新增借阅记录到正式时间序列集合"""

    reader = db.readers.find_one({
        "card_no": reader_card
    })

    book = db.books.find_one({
        "isbn": book_isbn
    })

    if reader is None:
        print("借阅失败：读者不存在")
        return 0

    if book is None:
        print("借阅失败：图书不存在")
        return 0

    if book.get("stock", 0) <= 0:
        print("借阅失败：图书库存不足")
        return 0

    record = {
        "reader_card": reader_card,
        "book_isbn": book_isbn,
        "borrow_date": datetime.now(timezone.utc),
        "status": "借出"
    }

    try:
        result = db.borrow_logs.insert_one(record)

        print("借阅登记成功！")
        print("新增记录数：1")
        print("记录ID：", result.inserted_id)
        print("注意：本实验仅登记借阅流水，不自动扣减库存")

        return 1

    except PyMongoError as e:
        print("借阅登记失败：", e)
        return 0


def list_borrow_records(db, limit=20):
    """查看借阅记录"""

    records = list(
        db.borrow_logs.find(
            {},
            {
                "_id": 0,
                "reader_card": 1,
                "book_isbn": 1,
                "borrow_date": 1,
                "return_date": 1,
                "status": 1
            }
        ).sort("borrow_date", -1).limit(limit)
    )

    if not records:
        print("没有借阅记录")
        return []

    print(f"\n===== 最近 {len(records)} 条借阅记录 =====")

    for record in records:
        print(
            f"读者：{record.get('reader_card')} | "
            f"ISBN：{record.get('book_isbn')} | "
            f"状态：{record.get('status')} | "
            f"借阅时间：{record.get('borrow_date')}"
        )

    return records


def find_overdue_records(db):
    """查询状态为逾期的借阅记录"""

    records = list(
        db.borrow_logs.find({
            "status": "逾期"
        }).sort("borrow_date", -1)
    )

    print(f"\n逾期状态记录数：{len(records)}")

    if not records:
        print("没有逾期状态记录")
        return []

    for record in records:
        print(
            f"读者：{record.get('reader_card')} | "
            f"ISBN：{record.get('book_isbn')} | "
            f"借阅日期：{record.get('borrow_date')}"
        )

    return records


def prepare_return_demo(db):
    """首次准备归还操作的普通实验集合"""

    name = "borrow_return_demo"

    if name in db.list_collection_names():
        print("归还实验集合已存在，不重复覆盖")
        return db[name]

    records = list(db.borrow_logs.find({}))

    if not records:
        print("没有可复制的借阅记录")
        return None

    db[name].insert_many(records)

    print(f"归还实验集合创建成功，共复制 {len(records)} 条")

    return db[name]


def process_return(db, reader_card, book_isbn):
    """
    在普通实验集合中演示归还操作。
    不修改正式时间序列集合 borrow_logs。
    """

    collection = db["borrow_return_demo"]

    if "borrow_return_demo" not in db.list_collection_names():
        print("请先运行 prepare_return_demo()")
        return 0

    query = {
        "reader_card": reader_card,
        "book_isbn": book_isbn,
        "status": "借出"
    }

    # 先预览待处理记录
    records = list(collection.find(query))

    if not records:
        print("没有找到符合条件的待归还记录")
        return 0

    print(f"找到 {len(records)} 条待归还记录")

    result = collection.update_many(
        query,
        {
            "$set": {
                "status": "已归还",
                "return_date": datetime.now(timezone.utc)
            }
        }
    )

    print(
        f"匹配记录数：{result.matched_count}，"
        f"实际修改数：{result.modified_count}"
    )

    return result.modified_count


if __name__ == "__main__":

    from mongodb_connect import get_database

    client = None

    try:
        client, db = get_database()

        print("\n===== 借阅管理模块测试 =====")

        print("\n1. 查看借阅记录")
        list_borrow_records(db, 5)

        print("\n2. 查询逾期记录")
        find_overdue_records(db)

        print("\n3. 检查正式借阅集合数量")
        print(
            "borrow_logs：",
            db.borrow_logs.count_documents({})
        )

        print("\n说明：")
        print("本次测试只执行查询，不修改借阅记录")
        print("借阅登记和归还操作将在主菜单中测试")

    except Exception as e:
        print("程序运行失败：", e)

    finally:
        if client is not None:
            client.close()
            print("\nMongoDB 数据库连接已关闭")
