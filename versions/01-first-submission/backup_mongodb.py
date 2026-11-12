"""Backup every non-system collection in the configured MongoDB database.

This is a dependency-light fallback when MongoDB Database Tools are not
installed.  BSON-aware JSON keeps ObjectId and datetime values reversible.
For a full native backup, prefer mongodump (see the usage message below).
"""

from datetime import datetime, timezone
import json
from pathlib import Path

from bson import json_util

from mongodb_connect import get_database


def backup_database(output_root: Path) -> Path:
    """Export all readable, non-system collections into a timestamped folder."""
    client = None
    backup_dir = output_root / datetime.now().strftime("mongodb_%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": None,
        "collections": [],
        "errors": [],
        "format": "MongoDB Extended JSON (bson.json_util)",
    }

    try:
        client, db = get_database()
        manifest["database"] = db.name

        # system.buckets.* and system.views are internal MongoDB collections.
        # listCollections also tells us which names are views, which cannot be
        # read with find() and must be backed up as their definition.
        collection_metadata = {
            item["name"]: item
            for item in db.command("listCollections", nameOnly=False)["cursor"]["firstBatch"]
            if not item["name"].startswith("system.")
        }

        for name in sorted(collection_metadata):
            try:
                metadata = collection_metadata[name]
                if metadata.get("type") == "view":
                    output_file = backup_dir / f"{name}.view.json"
                    output_file.write_text(
                        json_util.dumps(metadata, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    manifest["collections"].append({
                        "name": name,
                        "type": "view",
                        "file": output_file.name,
                    })
                    print(f"已备份视图 {name}")
                    continue

                collection = db[name]
                documents = list(collection.find({}))
                output_file = backup_dir / f"{name}.json"
                output_file.write_text(
                    json_util.dumps(documents, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                indexes = collection.index_information()
                (backup_dir / f"{name}.indexes.json").write_text(
                    json_util.dumps(indexes, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                manifest["collections"].append({
                    "name": name,
                    "type": "collection",
                    "documents": len(documents),
                    "file": output_file.name,
                    "indexes_file": f"{name}.indexes.json",
                })
                print(f"已备份 {name}: {len(documents)} 条")
            except Exception as exc:  # keep other collections exportable
                message = f"{name}: {type(exc).__name__}: {exc}"
                manifest["errors"].append(message)
                print(f"备份失败 {message}")

    finally:
        if client is not None:
            client.close()

    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n备份目录: {backup_dir.resolve()}")
    print(f"集合数量: {len(manifest['collections'])}")
    if manifest["errors"]:
        print(f"失败集合数量: {len(manifest['errors'])}，详见 manifest.json")
    return backup_dir


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent
    backup_database(project_dir / "backups")
