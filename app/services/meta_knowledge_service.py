import uuid
from pathlib import Path

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.models.value_info_es.value_info_es import ValueInfoEs
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    def __init__(self,
                 meta_mysql_repository: MetaMysqlRepository,
                 dw_mysql_repository: DwMysqlRepository,
                 column_qdrant_repository: ColumnQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 value_es_repository: ValueEsRepository,
                 metric_qdrant_repository: MetricQdrantRepository):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    async def build(self, config_path: Path):
        pass
        # 1.加载配置文件
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
        logger.info("加载配置文件完成")
        if meta_config.tables:
            # 2.处理表信息
            # 2.1 保存表信息到meta数据库
            column_infos: list[ColumnInfoMySQL] = await self._save_table_info_to_meta_db(meta_config)
            logger.info("保存表信息到meta数据库")
            # 2.2 为字段信息建立向量索引
            await self._save_column_info_to_qdrant(column_infos)
            logger.info("为列信息添加向量索引")
            # 2.3 为字段取值建立全文索引
            await self._save_value_info_to_es(column_infos, meta_config)
            logger.info("为值信息添加全文索引")
        # 3.处理指标信息
        if meta_config.metrics:
            # 3.1 保存指标到meta数据库
            metric_infos: list[MetricInfoMySQL] = await self._save_metric_info_to_meta_db(meta_config)
            logger.info("保存指标信息到meta数据库")
            # 3.2为指标信息构建向量索引
            await self._save_metric_info_to_qdrant(metric_infos)
            logger.info("为指标信息添加向量索引")

    async def _save_table_info_to_meta_db(self, meta_config: MetaConfig):
        table_infos: list[TableInfoMySQL] = []
        column_infos: list[ColumnInfoMySQL] = []
        for table in meta_config.tables:
            column_types: dict[str, str] = await self.dw_mysql_repository.get_column_types(table.name)
            table_info = TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description
            )
            table_infos.append(table_info)
            for column in table.columns:
                column_values: list[str] = await self.dw_mysql_repository.get_column_values(table.name, column.name)
                column_info = ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                )
                column_infos.append(column_info)
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_table_infos(table_infos)
            await self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos

    def _convert_column_info_from_mysql_to_qdrant(self, column_info: ColumnInfoMySQL):
        return ColumnInfoQdrant(
            id=column_info.id,
            name=column_info.name,
            type=column_info.type,
            role=column_info.role,
            examples=column_info.examples,
            description=column_info.description,
            alias=column_info.alias,
            table_id=column_info.table_id
        )

    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfoMySQL]):
        await self.column_qdrant_repository.ensure_collection()
        points: list[dict] = []
        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": self._convert_column_info_from_mysql_to_qdrant(column_info)
            })
            # description
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": self._convert_column_info_from_mysql_to_qdrant(column_info)
            })
            # alias
            for alia in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": self._convert_column_info_from_mysql_to_qdrant(column_info)
                })
        embedding_text = [point["embedding_text"] for point in points]
        embeddings = []
        batch_size = 20
        for i in range(0, len(embedding_text), batch_size):
            batch_embedding_text = embedding_text[i:i + batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddings.extend(batch_embeddings)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert_embedding(ids, embeddings, payloads)

    async def _save_value_info_to_es(self, column_infos: list[ColumnInfoMySQL], meta_config: MetaConfig):
        await self.value_es_repository.ensure_index()
        column2sync: dict[str, bool] = {}
        for table in meta_config.tables:
            for column in table.columns:
                column2sync[f"{table.name}.{column.name}"] = column.sync
        value_infos: list[ValueInfoEs] = []
        for column_info in column_infos:
            sync = column2sync[column_info.id]
            if sync:
                values: list[str] = await self.dw_mysql_repository.get_column_values(column_info.table_id,
                                                                                     column_info.name, 10000)
                current_column_values = [ValueInfoEs(
                    id=f"{column_info.id}.{value}",  # 表名.列表.值
                    value=value,
                    type=column_info.type,
                    column_id=column_info.id,
                    column_name=column_info.name,
                    table_id=column_info.table_id,
                    table_name=column_info.table_id

                ) for value in values]
                value_infos.append(current_column_values)
            await self.value_es_repository.upsert_values(value_infos)

    async def _save_metric_info_to_meta_db(self, meta_config: MetaConfig):
        metric_infos: list[MetricInfoMySQL] = []
        column_metric_infos: list[ColumnMetricMySQL] = []
        for metric in meta_config.metrics:
            metric_info = MetricInfoMySQL(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            )
            metric_infos.append(metric_info)
            for relevant_column in metric.relevant_columns:
                relevant_column_info = ColumnMetricMySQL(
                    column_id=relevant_column,
                    metric_id=metric.name
                )
                column_metric_infos.append(relevant_column_info)
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_infos(metric_infos)
            await self.meta_mysql_repository.save_column_metric_infos(column_metric_infos)
        return metric_infos

    def _convert_metric_info_from_mysql_to_qdrant(self, metric_info: MetricInfoMySQL):
        return MetricInfoQdrant(
            id=metric_info.id,
            name=metric_info.name,
            description=metric_info.description,
            relevant_columns=metric_info.relevant_columns,
            alias=metric_info.alias
        )

    async def _save_metric_info_to_qdrant(self, metric_infos: list[MetricInfoMySQL]):
        await self.metric_qdrant_repository.ensure_collection()
        points: list[dict] = []
        for metric_info in metric_infos:
            # name
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": self._convert_metric_info_from_mysql_to_qdrant(metric_info)
            })
            # description
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": self._convert_metric_info_from_mysql_to_qdrant(metric_info)
            })
            # alias
            for alia in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": self._convert_metric_info_from_mysql_to_qdrant(metric_info)
                })
        embedding_text = [point["embedding_text"] for point in points]
        embeddings = []
        batch_size = 20
        for i in range(0, len(embedding_text), batch_size):
            batch_embedding_text = embedding_text[i:i + batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddings.extend(batch_embeddings)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert_embeddings(ids, embeddings, payloads)
