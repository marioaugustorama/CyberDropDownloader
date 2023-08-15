from dataclasses import field
from pathlib import Path

import aiosqlite

from cyberdrop_dl.db.tables.cache_table import CacheTable
from cyberdrop_dl.db.tables.history_table import HistoryTable
from cyberdrop_dl.db.tables.temp_table import TempTable


class DBManager:
    def __init__(self, db_path: Path):
        self.db_conn: aiosqlite.Connection = field(init=False)
        self.db_path: Path = db_path

        self.cache_table: CacheTable = field(init=False)
        self.history_table: HistoryTable = field(init=False)
        self.temp_table: TempTable = field(init=False)

    async def startup(self) -> None:
        """Startup process for the DBManager"""
        self.db_conn = await aiosqlite.connect(self.db_path)

        self.cache_table = CacheTable(self.db_conn)
        self.history_table = HistoryTable(self.db_conn)
        self.temp_table = TempTable(self.db_conn)

        await self._pre_allocate()

        await self.cache_table.startup()
        await self.history_table.startup()
        await self.temp_table.startup()

    async def _pre_allocate(self) -> None:
        """We pre-allocate 100MB of space to the SQL file just in case the user runs out of disk space"""
        create_pre_allocation_table = "CREATE TABLE IF NOT EXISTS t(x);"
        drop_pre_allocation_table = "DROP TABLE t;"

        fill_pre_allocation = "INSERT INTO t VALUES(zeroblob(100*1024*1024));"  # 100 mb
        check_pre_allocation = "PRAGMA freelist_count;"

        result = await self.db_conn.execute(check_pre_allocation)
        free_space = await result.fetchone()

        if free_space[0] <= 1024:
            await self.db_conn.execute(create_pre_allocation_table)
            await self.db_conn.commit()
            await self.db_conn.execute(fill_pre_allocation)
            await self.db_conn.commit()
            await self.db_conn.execute(drop_pre_allocation_table)
            await self.db_conn.commit()
