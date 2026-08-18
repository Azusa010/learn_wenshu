from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.expression import text


class DwMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name: str) -> dict[str, str]:
        # 定义sql
        sql = f"show columns  from {table_name}"
        # 执行sql
        result = await self.session.execute(text(sql))
        # 解析结果[(),()]
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values(self, table_name: str, column_name: str, limit: int = 10) -> list[str]:
        # 定义sql
        sql = f"select distinct  {column_name} from {table_name} limit {limit}"
        # 执行sql
        result = await self.session.execute(text(sql))
        # 解析结果
        return result.scalars().fetchall();

    async def get_db_info(self):
        """
        查询数据库信息和方言
        :return:
        """
        result = await self.session.execute(text("select version()"))
        version = result.scalar()
        dialect = self.session.bind.dialect.name
        return {"version": version, "dialect": dialect}

    async def validate_sql(self, sql: str):
        await  self.session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql: str):
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]
