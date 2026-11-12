
from pprint import pprint
from pymongo.errors import DuplicateKeyError


def add_book(db, book):
    """添加单本图书"""
    try:
        result = db.books.insert_one(book)
        print(f"添加成功，新增文档数：1，ID：{result.inserted_id}")
        return result.inserted_id
    except DuplicateKeyError:
        print("添加失败：ISBN或_id已存在")
        return None


def update_book_info(db, isbn, updates):
    """根据ISBN修改图书信息"""

    if not updates:
        print("没有需要修改的内容")
        return 0

    # 防止修改不允许的字段
    allowed_fields = {
        "title", "author", "publisher",
        "category", "price", "stock",
        "rating", "tags", "publish_date",
        "borrow_count"
    }

    if not set(updates).issubset(allowed_fields):
        print("修改失败：包含不允许修改的字段")
        return 0

    result = db.books.update_one(
        {"isbn": isbn},
        {"$set": updates}
    )

    if result.matched_count == 0:
        print("修改失败：未找到该图书")
    elif result.modified_count == 0:
        print("图书信息没有变化")
    else:
        print("图书信息修改成功！")
        print(f"修改文档数：{result.modified_count}")

    return result.modified_count

def add_books(db, books):
    """批量添加图书"""
    if not books:
        print("没有需要添加的图书")
        return 0

    result = db.books.insert_many(books)
    print(f"批量添加成功，新增文档数：{len(result.inserted_ids)}")
    return len(result.inserted_ids)


def find_book_by_isbn(db, isbn):
    """根据ISBN精确查询图书"""
    book = db.books.find_one({"isbn": isbn})
    if book:
        pprint(book, sort_dicts=False)
    else:
        print("未找到对应图书")
    return book


def search_books(db, keyword="", category=None,
                 min_price=None, max_price=None):
    """按书名、类别、价格进行组合检索"""
    query = {}

    if keyword:
        # 使用正则转义，避免特殊字符改变查询语义
        import re
        query["title"] = {
            "$regex": re.escape(keyword),
            "$options": "i"
        }

    if category:
        query["category"] = category

    price_filter = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price

    if price_filter:
        query["price"] = price_filter

    books = list(db.books.find(query).sort("title", 1))

    if not books:
        print("没有符合条件的图书")
    else:
        print(f"查询成功，共找到 {len(books)} 本图书")
        for book in books:
            print(
                f"ISBN：{book.get('isbn')} | "
                f"书名：{book.get('title')} | "
                f"价格：{book.get('price')} | "
                f"库存：{book.get('stock')}"
            )

    return books


def update_book_stock(db, isbn, new_stock):
    """修改指定图书的库存"""
    if not isinstance(new_stock, int) or new_stock < 0:
        print("库存必须是非负整数")
        return 0

    result = db.books.update_one(
        {"isbn": isbn},
        {"$set": {"stock": new_stock}}
    )

    print(
        f"匹配文档数：{result.matched_count}，"
        f"实际修改数：{result.modified_count}"
    )
    return result.modified_count


def delete_book(db, isbn):
    """按ISBN删除一本图书"""
    result = db.books.delete_one({"isbn": isbn})
    print(f"删除文档数：{result.deleted_count}")
    return result.deleted_count


def delete_books_by_category(db, category):
    """删除指定类别的全部图书"""
    result = db.books.delete_many({"category": category})
    print(f"删除文档数：{result.deleted_count}")
    return result.deleted_count


def top_rated_books(db, limit=5):
    """评分最高的图书排行榜"""
    books = list(
        db.books.find(
            {},
            {"_id": 0, "title": 1, "rating": 1, "borrow_count": 1}
        )
        .sort([("rating", -1), ("title", 1)])
        .limit(limit)
    )

    if not books:
        print("没有图书排行数据")
    else:
        print(f"\n评分最高的前 {len(books)} 本图书：")
        for i, book in enumerate(books, start=1):
            print(
                f"{i}. {book.get('title')} | "
                f"评分：{book.get('rating')} | "
                f"借阅次数：{book.get('borrow_count')}"
            )

    return books


if __name__ == "__main__":
    from mongodb_connect import get_database

    client = None
    try:
        client, db = get_database()

        print("\n===== 图书管理模块测试 =====")

        # 仅测试查询功能，不修改已有数据
        print("\n1. ISBN精确查询")
        find_book_by_isbn(db, "9787115428028")

        print("\n2. 计算机类图书查询")
        search_books(db, category="计算机")

        print("\n3. 评分排行榜")
        top_rated_books(db, 5)

    except Exception as e:
        print("运行失败：", e)

    finally:
        if client is not None:
            client.close()
            print("\n数据库连接已关闭")
