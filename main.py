from datetime import datetime
from mongodb_connect import get_database
from pprint import pprint
from book_manager import (
    add_book,
    find_book_by_isbn,
    search_books,
    update_book_stock,
    update_book_info,
    delete_book,
    top_rated_books
)
from reader_manager import (
    find_reader_by_card,
    list_readers,
    count_readers,
    search_readers_by_college,
    college_statistics,
    level_statistics
)

from borrow_manager import (
    register_borrow,
    list_borrow_records,
    find_overdue_records,
    prepare_return_demo,
    process_return
)

from stat_manager import (
    category_statistics,
    borrow_trend,
    popular_books
)


def show_menu():
    """显示系统主菜单"""

    print("\n" + "=" * 52)
    print("       图书情报检索与统计平台")
    print("=" * 52)
    print("  1. 查看全部图书")
    print("  2. 按ISBN查询图书")
    print("  3. 组合条件检索图书")
    print("  4. 添加图书")
    print("  5. 修改图书信息")
    print("  6. 删除指定图书")
    print("  7. 图书评分排行榜")
    print("-" * 52)
    print("  8. 查看全部读者")
    print("  9. 按借阅证号查询读者")
    print(" 10. 按学院查询读者")
    print(" 11. 读者学院与等级统计")
    print("-" * 52)
    print(" 12. 查看借阅记录")
    print(" 13. 新增借阅登记")
    print(" 14. 查询逾期记录")
    print(" 15. 归还处理（实验集合）")
    print("-" * 52)
    print(" 16. 综合统计分析")
    print("  0. 退出系统")
    print("=" * 52)


def show_database_info(db):
    """显示数据库连接状态和集合数量"""

    print("\nMongoDB 数据库连接成功！")
    print("当前数据库：", db.name)

    print("\n========== 集合信息 ==========")

    collections = [
        "books",
        "readers",
        "borrow_logs",
        "category_stats"
    ]

    for name in collections:
        count = db[name].count_documents({})
        print(f"{name}: {count} 条")

    print("============================")


def input_integer(prompt, minimum=0):
    """读取合法整数"""

    while True:
        value = input(prompt).strip()

        try:
            number = int(value)
            if number < minimum:
                print(f"请输入不小于 {minimum} 的整数")
                continue
            return number
        except ValueError:
            print("输入错误，请输入整数")


def input_float(prompt, allow_blank=False):
    """读取数字，可选择允许空值"""

    while True:
        value = input(prompt).strip()

        if allow_blank and not value:
            return None

        try:
            return float(value)
        except ValueError:
            print("输入错误，请输入数字")


def confirm(message):
    """高风险操作二次确认"""

    answer = input(f"{message}（输入 YES 确认）：").strip()
    return answer == "YES"


def main():
    """系统入口"""

    client = None

    try:
        client, db = get_database()
        show_database_info(db)

        while True:
            show_menu()
            choice = input("请选择功能编号：").strip()

            try:
                if choice == "0":
                    print("\n正在退出系统……")
                    break

                elif choice == "1":
                    search_books(db)

                elif choice == "2":
                    isbn = input("请输入ISBN：").strip()
                    if isbn:
                        find_book_by_isbn(db, isbn)
                    else:
                        print("ISBN不能为空")

                elif choice == "3":
                    keyword = input("请输入书名关键词（可留空）：").strip()
                    category = input("请输入图书类别（可留空）：").strip()

                    min_price = input_float(
                        "请输入最低价格（可留空）：",
                        allow_blank=True
                    )

                    max_price = input_float(
                        "请输入最高价格（可留空）：",
                        allow_blank=True
                    )

                    if (
                        min_price is not None
                        and max_price is not None
                        and min_price > max_price
                    ):
                        print("最低价格不能高于最高价格")
                        continue

                    search_books(
                        db,
                        keyword=keyword,
                        category=category or None,
                        min_price=min_price,
                        max_price=max_price
                    )
                


                elif choice == "4":
                    print("\n========== 添加图书 ==========")

                    isbn = input("请输入ISBN：").strip()
                    title = input("请输入书名：").strip()
                    author = input("请输入作者：").strip()
                    publisher = input("请输入出版社：").strip()
                    category = input("请输入分类：").strip()

                    if not all([isbn, title, author, publisher, category]):
                        print("ISBN、书名、作者、出版社、分类不能为空")
                        continue

                    price = input_float("请输入价格：")
                    if price < 0:
                        print("价格不能为负数")
                        continue

                    stock = input_integer("请输入库存：", 0)

                    while True:
                        rating = input_float("请输入评分（0-5）：")
                        if 0 <= rating <= 5:
                            break
                        print("评分必须在0到5之间")

                    tags_text = input("请输入标签（逗号分隔）：").strip()
                    tags = [
                        t.strip()
                        for t in tags_text.replace("，", ",").split(",")
                        if t.strip()
                    ]

                    while True:
                        date_text = input(
                            "请输入出版日期（YYYY-MM-DD）："
                        ).strip()
                        try:
                            publish_date = datetime.strptime(
                                date_text, "%Y-%m-%d"
                            )
                            break
                        except ValueError:
                            print("日期格式错误，请重新输入")

                    borrow_count = input_integer("请输入借阅量：", 0)

                    book = {
                        "isbn": isbn,
                        "title": title,
                        "author": author,
                        "publisher": publisher,
                        "category": category,
                        "price": price,
                        "stock": stock,
                        "rating": rating,
                        "tags": tags,
                        "publish_date": publish_date,
                        "borrow_count": borrow_count
                    }

                    print("\n========== 添加信息确认 ==========")
                    pprint(book, sort_dicts=False)

                    if confirm("确定添加这本图书吗？"):
                        add_book(db, book)
                    else:
                        print("已取消添加")


                

                elif choice == "5":
                    print("\n========== 修改图书信息 ==========")

                    isbn = input("请输入要修改的图书ISBN：").strip()

                    book = db.books.find_one({"isbn": isbn})

                    if book is None:
                        print("未找到该图书")
                        continue

                    print("\n当前图书信息：")
                    pprint(book, sort_dicts=False)

                    print("\n请选择要修改的字段：")
                    print(" 1. 书名")
                    print(" 2. 作者")
                    print(" 3. 出版社")
                    print(" 4. 分类")
                    print(" 5. 价格")
                    print(" 6. 库存")
                    print(" 7. 评分")
                    print(" 8. 标签")
                    print(" 9. 出版日期")
                    print("10. 借阅量")
                    print(" 0. 返回主菜单")

                    field_map = {
                        "1": ("title", "书名"),
                        "2": ("author", "作者"),
                        "3": ("publisher", "出版社"),
                        "4": ("category", "分类"),
                        "5": ("price", "价格"),
                        "6": ("stock", "库存"),
                        "7": ("rating", "评分"),
                        "8": ("tags", "标签"),
                        "9": ("publish_date", "出版日期"),
                        "10": ("borrow_count", "借阅量")
                    }

                    option = input("请输入字段编号：").strip()

                    if option == "0":
                        continue

                    if option not in field_map:
                        print("无效字段编号")
                        continue

                    field, label = field_map[option]

                    if field in {"price", "rating"}:
                        new_value = input_float(f"请输入新的{label}：")

                        if field == "price" and new_value < 0:
                            print("价格不能为负数")
                            continue

                        if field == "rating" and not 0 <= new_value <= 5:
                            print("评分必须在0到5之间")
                            continue

                    elif field in {"stock", "borrow_count"}:
                        new_value = input_integer(
                            f"请输入新的{label}：", 0
                        )

                    elif field == "tags":
                        text = input("请输入新标签（逗号分隔）：")
                        new_value = [
                            t.strip()
                            for t in text.replace("，", ",").split(",")
                            if t.strip()
                        ]

                    elif field == "publish_date":
                        text = input(
                            "请输入新的出版日期（YYYY-MM-DD）："
                        ).strip()

                        try:
                            new_value = datetime.strptime(
                                text, "%Y-%m-%d"
                            )
                        except ValueError:
                            print("日期格式错误")
                            continue

                    else:
                        new_value = input(f"请输入新的{label}：").strip()

                        if not new_value:
                            print(f"{label}不能为空")
                            continue

                    print(f"\n即将修改：{label}")
                    print("原值：", book.get(field, "未设置"))
                    print("新值：", new_value)

                    if confirm("确定保存修改吗？"):
                        update_book_info(
                            db,
                            isbn,
                            {field: new_value}
                        )
                    else:
                        print("已取消修改")

                elif choice == "6":
                    isbn = input("请输入要删除的图书ISBN：").strip()

                    if not isbn:
                        print("ISBN不能为空")
                        continue

                    book = db.books.find_one({"isbn": isbn})

                    if book is None:
                        print("未找到对应图书")
                        continue

                    print("待删除图书：", book.get("title"))

                    if confirm("确定删除这本图书吗？"):
                        delete_book(db, isbn)
                    else:
                        print("已取消删除")

                elif choice == "7":
                    top_rated_books(db, 5)

                elif choice == "8":
                    list_readers(db)
                    count_readers(db)

                elif choice == "9":
                    card_no = input("请输入借阅证号：").strip()
                    find_reader_by_card(db, card_no)

                elif choice == "10":
                    college = input("请输入学院名称：").strip()
                    if college:
                        search_readers_by_college(db, college)
                    else:
                        print("学院名称不能为空")

                elif choice == "11":
                    college_statistics(db)
                    level_statistics(db)

                elif choice == "12":
                    limit = input_integer(
                        "请输入查看记录数量：", 1
                    )
                    list_borrow_records(db, limit)

                elif choice == "13":
                    print("\n===== 新增借阅登记 =====")

                    reader_card = input("借阅证号：").strip()
                    book_isbn = input("图书ISBN：").strip()

                    if not reader_card or not book_isbn:
                        print("借阅证号和ISBN不能为空")
                        continue

                    print("提示：该功能写入正式借阅流水")
                    print("当前版本不会自动扣减库存")

                    if confirm("确定登记借阅吗？"):
                        register_borrow(
                            db, reader_card, book_isbn
                        )
                    else:
                        print("已取消借阅登记")

                elif choice == "14":
                    find_overdue_records(db)

                elif choice == "15":
                    print("\n===== 归还处理实验 =====")
                    print("该功能仅操作 borrow_return_demo")
                    print("不会修改正式 borrow_logs")

                    if "borrow_return_demo" not in db.list_collection_names():
                        if confirm("创建借阅记录实验副本吗？"):
                            prepare_return_demo(db)
                        else:
                            print("已取消")
                            continue

                    reader_card = input("借阅证号：").strip()
                    book_isbn = input("图书ISBN：").strip()

                    if not reader_card or not book_isbn:
                        print("借阅证号和ISBN不能为空")
                        continue

                    if confirm("确定处理匹配的归还记录吗？"):
                        process_return(
                            db, reader_card, book_isbn
                        )
                    else:
                        print("已取消归还处理")

                elif choice == "16":
                    category_statistics(db)
                    borrow_trend(db)
                    popular_books(db, 5)

                else:
                    print("无效选项，请输入0至16之间的编号")

            except KeyboardInterrupt:
                print("\n当前操作已取消")

            except Exception as e:
                print("当前操作执行失败：", e)

    except KeyboardInterrupt:
        print("\n用户中断程序")

    except Exception as e:
        print("\n系统启动失败：", e)

    finally:
        if client is not None:
            client.close()
            print("\nMongoDB 数据库连接已关闭")

        print("感谢使用图书情报检索与统计平台！")


if __name__ == "__main__":
    main()
