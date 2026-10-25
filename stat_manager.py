
from pprint import pprint


def category_statistics(db):
    """
    ST-5.4 图书分类统计
    按类别统计图书数量、库存总量、平均价格，
    按库存总量降序排列。
    """

    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "book_count": {"$sum": 1},
                "total_stock": {"$sum": "$stock"},
                "avg_price": {"$avg": "$price"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "book_count": 1,
                "total_stock": 1,
                "avg_price": {"$round": ["$avg_price", 2]}
            }
        },
        {
            "$sort": {
                "total_stock": -1,
                "category": 1
            }
        }
    ]

    results = list(db.books.aggregate(pipeline))

    print("\n========== 图书分类统计 ==========")

    if not results:
        print("暂无图书分类统计数据")
        return []

    print(
        f"{'类别':<12}"
        f"{'图书数量':<12}"
        f"{'库存总量':<12}"
        f"{'平均价格':<12}"
    )

    for item in results:
        print(
            f"{item['category']:<12}"
            f"{item['book_count']:<12}"
            f"{item['total_stock']:<12}"
            f"{item['avg_price']:<12.2f}"
        )

    print("================================")

    return results


def borrow_trend(db):
    """
    ST-5.4 借阅趋势分析
    按年份统计借阅次数，格式化年份。
    """

    pipeline = [
        {
            "$group": {
                "_id": {
                    "$year": {
                        "date": "$borrow_date",
                        "timezone": "Asia/Shanghai"
                    }
                },
                "borrow_count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "year": "$_id",
                "year_label": {
                    "$concat": [
                        {"$toString": "$_id"},
                        "年"
                    ]
                },
                "borrow_count": 1
            }
        },
        {
            "$sort": {"year": 1}
        }
    ]

    results = list(db.borrow_logs.aggregate(pipeline))

    print("\n========== 年度借阅趋势 ==========")

    if not results:
        print("暂无借阅记录")
        return []

    total = 0

    for item in results:
        print(
            f"{item['year_label']}："
            f"{item['borrow_count']} 次"
        )
        total += item["borrow_count"]

    print("--------------------------------")
    print(f"累计借阅次数：{total}")
    print("================================")

    return results


def popular_books(db, limit=5):
    """
    ST-5.4 热门图书排行榜
    根据 books.borrow_count 降序统计。
    """

    if limit <= 0:
        print("排行榜数量必须大于0")
        return []

    pipeline = [
        {
            "$sort": {
                "borrow_count": -1,
                "title": 1
            }
        },
        {
            "$limit": limit
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "category": 1,
                "borrow_count": 1,
                "rating": 1
            }
        }
    ]

    results = list(db.books.aggregate(pipeline))

    print("\n========== 热门图书排行榜 ==========")

    if not results:
        print("暂无图书排行数据")
        return []

    for rank, book in enumerate(results, start=1):
        print(
            f"{rank}. {book.get('title')} | "
            f"借阅次数：{book.get('borrow_count', 0)} | "
            f"评分：{book.get('rating', '暂无')}"
        )

    print("==================================")

    return results


def show_all_statistics(db):
    """统一执行三种统计分析"""

    print("\n========== 图书情报统计分析 ==========")

    category_statistics(db)
    borrow_trend(db)
    popular_books(db, 5)


if __name__ == "__main__":
    from mongodb_connect import get_database

    client = None

    try:
        client, db = get_database()

        print("\n===== 统计分析模块测试 =====")

        show_all_statistics(db)

    except Exception as e:
        print("统计程序运行失败：", e)

    finally:
        if client is not None:
            client.close()
            print("\nMongoDB 数据库连接已关闭")
