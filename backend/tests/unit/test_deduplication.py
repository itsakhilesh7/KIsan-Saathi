"""Unit tests for SQLiteDeduplicationRepository."""

from backend.app.repositories.deduplication import SQLiteDeduplicationRepository


def test_sqlite_deduplication_lifecycle_and_persistence(tmp_path):
    """Test deduplication semantics and persistence across repository instances."""
    db_file = tmp_path / "test_dedup.sqlite3"
    repo1 = SQLiteDeduplicationRepository(db_path=str(db_file))

    # 1. First call on fresh message ID should return False (not seen before)
    assert repo1.is_duplicate("msg_1001") is False

    # 2. Second call with same message ID should return True (duplicate detected)
    assert repo1.is_duplicate("msg_1001") is True

    # 3. None or empty message ID returns False
    assert repo1.is_duplicate(None) is False
    assert repo1.is_duplicate("") is False

    # 4. Simulate process restart: create a new instance pointing to the same file
    repo2 = SQLiteDeduplicationRepository(db_path=str(db_file))

    # 5. Must still return True for msg_1001 (restart persistence confirmed)
    assert repo2.is_duplicate("msg_1001") is True

    # 6. A new message on the second instance returns False
    assert repo2.is_duplicate("msg_1002") is False
    assert repo2.is_duplicate("msg_1002") is True

    # 7. Clear table
    repo2.clear()
    assert repo2.is_duplicate("msg_1001") is False
