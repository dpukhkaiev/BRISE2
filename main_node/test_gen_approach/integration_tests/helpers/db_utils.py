from traceback import print_stack
from tools.restore_db import RestoreDB

_rdb_instance = None


def get_restore_db_instance() -> RestoreDB:
    global _rdb_instance
    if _rdb_instance is None:
        _rdb_instance = RestoreDB()
    return _rdb_instance


def reset_database() -> bool:
    try:
        rdb = get_restore_db_instance()
        rdb.cleanup()
        rdb.restore()
        return True
    except Exception as e:
        print(f"Database reset failed: {e}")
        print_stack()
        return False


def cleanup_database() -> bool:
    try:
        rdb = get_restore_db_instance()
        rdb.cleanup()
        return True
    except Exception as e:
        print(f"Database cleanup failed: {e}")
        print_stack()
        return False
