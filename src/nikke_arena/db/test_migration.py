from .migration import migrate_database


def test_migration():
    migrate_database()