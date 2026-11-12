
from pprint import pprint


def find_reader_by_card(db, card_no):
    """根据借阅证号查询读者信息"""
    reader = db.readers.find_one({"card_no": card_no})

    if reader:
        print("\n查询成功，读者信息如下：")
        pprint(reader, sort_dicts=False)
    else:
        print("未找到该借阅证号对应的读者")

    return reader


def list_readers(db):
    """查看全部读者信息"""
    readers = list(
        db.readers.find(
            {},
            {
                "_id": 0,
                "card_no": 1,
                "name": 1,
                "college": 1,
                "level": 1
            }
        ).sort("card_no", 1)
    )

    if not readers:
        print("当前没有读者信息")
        return readers

    print(f"\n共有 {len(readers)} 名读者：")

    for reader in readers:
        print(
            f"借阅证号：{reader.get('card_no')} | "
            f"姓名：{reader.get('name')} | "
            f"学院：{reader.get('college')} | "
            f"等级：{reader.get('level')}"
        )

    return readers


def count_readers(db):
    """统计读者总人数"""
    count = db.readers.count_documents({})
    print(f"\n读者总人数：{count}")
    return count


def search_readers_by_college(db, college):
    """按学院查询读者"""
    readers = list(
        db.readers.find(
            {"college": college},
            {"_id": 0, "card_no": 1, "name": 1,
             "college": 1, "level": 1}
        )
    )

    if not readers:
        print(f"没有找到属于 {college} 的读者")
    else:
        print(f"\n{college} 共 {len(readers)} 名读者：")
        for reader in readers:
            print(
                f"{reader.get('card_no')} - "
                f"{reader.get('name')} - "
                f"{reader.get('level')}"
            )

    return readers


def college_statistics(db):
    """统计各学院读者人数"""
    colleges = db.readers.distinct("college")

    if not colleges:
        print("没有可统计的学院数据")
        return []

    results = []

    print("\n========== 各学院读者人数 ==========")

    for college in sorted(colleges):
        count = db.readers.count_documents({
            "college": college
        })

        results.append({
            "college": college,
            "count": count
        })

        print(f"{college}：{count} 人")

    print("===================================")
    return results


def level_statistics(db):
    """统计不同借阅等级的读者人数"""
    levels = db.readers.distinct("level")

    if not levels:
        print("没有借阅等级数据")
        return []

    results = []

    print("\n========== 借阅等级分布 ==========")

    for level in sorted(levels):
        count = db.readers.count_documents({
            "level": level
        })

        results.append({
            "level": level,
            "count": count
        })

        print(f"{level}：{count} 人")

    print("=================================")
    return results


if __name__ == "__main__":
    from mongodb_connect import get_database

    client = None

    try:
        client, db = get_database()

        print("\n===== 读者管理模块测试 =====")

        print("\n1. 查询读者总人数")
        count_readers(db)

        print("\n2. 根据借阅证号查询读者")
        find_reader_by_card(db, "R20240001")

        print("\n3. 查看全部读者")
        list_readers(db)

        print("\n4. 查询计算机学院读者")
        search_readers_by_college(db, "计算机学院")

        print("\n5. 统计各学院读者人数")
        college_statistics(db)

        print("\n6. 统计借阅等级分布")
        level_statistics(db)

    except Exception as e:
        print("程序运行失败：", e)

    finally:
        if client is not None:
            client.close()
            print("\nMongoDB 数据库连接已关闭")
