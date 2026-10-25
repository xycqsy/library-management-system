
from pathlib import Path
from bson import json_util
from mongodb_connect import get_database


def export_collection(db, name, output_dir):
    """将 MongoDB 集合导出为 JSON 文件"""

    documents = list(db[name].find({}))

    output_file = output_dir / f"{name}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            json_util.dumps(
                documents,
                ensure_ascii=False,
                indent=2
            )
        )

    print(f"导出成功：{output_file}")
    print(f"文档数量：{len(documents)}")

    return output_file


def main():
    client = None

    try:
        client, db = get_database()

        # 在当前项目目录下创建 exports 文件夹
        output_dir = Path(__file__).resolve().parent / "exports"
        output_dir.mkdir(exist_ok=True)

        print("\n========== MongoDB 数据导出 ==========")

        export_collection(db, "books", output_dir)
        export_collection(db, "category_stats", output_dir)

        print("\n所有数据导出完成！")

    except Exception as e:
        print("数据导出失败：", e)

    finally:
        if client is not None:
            client.close()
            print("MongoDB 数据库连接已关闭")


if __name__ == "__main__":
    main()
