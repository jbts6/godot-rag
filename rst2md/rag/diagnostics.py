from pathlib import Path
import sqlite3


def run_diagnostics(db_path: Path, check_model: bool = True) -> dict:
    report = {
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "sqlite_vec_available": False,
        "vec_chunks_exists": False,
        "chunks_count": None,
        "vec_chunks_count": None,
        "row_parity": False,
        "model_available": None,
        "ok": False,
        "errors": [],
    }
    if not db_path.exists():
        report["errors"].append("database_not_found")
        return report

    conn = sqlite3.connect(str(db_path))
    try:
        conn.enable_load_extension(True)
        try:
            import sqlite_vec

            sqlite_vec.load(conn)
            report["sqlite_vec_available"] = True
        except Exception:
            report["errors"].append("sqlite_vec_unavailable")

        try:
            report["chunks_count"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        except sqlite3.OperationalError:
            report["errors"].append("missing_chunks")

        try:
            report["vec_chunks_count"] = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
            report["vec_chunks_exists"] = True
        except sqlite3.OperationalError:
            report["errors"].append("missing_vec_chunks")

        if report["chunks_count"] is not None and report["vec_chunks_count"] is not None:
            report["row_parity"] = report["chunks_count"] == report["vec_chunks_count"]
            if not report["row_parity"]:
                report["errors"].append("vector_row_count_mismatch")

        if check_model:
            try:
                from rag.embeddings import get_embedding_model

                get_embedding_model()
                report["model_available"] = True
            except Exception:
                report["model_available"] = False
                report["errors"].append("model_unavailable")

        report["ok"] = (
            report["db_exists"]
            and report["sqlite_vec_available"]
            and report["vec_chunks_exists"]
            and report["row_parity"]
            and report["model_available"] is not False
        )
        return report
    finally:
        conn.close()
