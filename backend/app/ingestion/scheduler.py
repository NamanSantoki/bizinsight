import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("bizinsight.scheduler")

class IngestionScheduleTask:
    def __init__(
        self,
        task_id: str,
        name: str,
        source_id: int,
        cron_expression: str,
        incremental_column: Optional[str] = None,
        last_sync_value: Optional[str] = None,
        is_active: bool = True
    ):
        self.task_id = task_id
        self.name = name
        self.source_id = source_id
        self.cron_expression = cron_expression
        self.incremental_column = incremental_column
        self.last_sync_value = last_sync_value
        self.is_active = is_active
        self.last_run: Optional[str] = None
        self.last_status: str = "SCHEDULED"
        self.records_ingested: int = 0

class IngestionSchedulerEngine:
    """Enterprise Scheduler & Change Data Capture (CDC) Manager.
    Coordinates automated recurring synchronizations and incremental loads.
    """

    def __init__(self):
        self._tasks: Dict[str, IngestionScheduleTask] = {}
        self._initialize_default_schedules()

    def _initialize_default_schedules(self):
        self.register_schedule(
            task_id="sync_crm_daily",
            name="Daily Enterprise Sales CDC Sync",
            source_id=1,
            cron_expression="0 2 * * *",
            incremental_column="transaction_date"
        )
        self.register_schedule(
            task_id="sync_commodities_hourly",
            name="Hourly Crude Oil Ticker Stream",
            source_id=2,
            cron_expression="0 * * * *",
            incremental_column="Date"
        )

    def register_schedule(
        self,
        task_id: str,
        name: str,
        source_id: int,
        cron_expression: str,
        incremental_column: Optional[str] = None
    ) -> IngestionScheduleTask:
        task = IngestionScheduleTask(
            task_id=task_id,
            name=name,
            source_id=source_id,
            cron_expression=cron_expression,
            incremental_column=incremental_column
        )
        self._tasks[task_id] = task
        return task

    def list_schedules(self) -> List[Dict[str, Any]]:
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "source_id": t.source_id,
                "cron_expression": t.cron_expression,
                "incremental_column": t.incremental_column,
                "last_sync_value": t.last_sync_value,
                "is_active": t.is_active,
                "last_run": t.last_run,
                "last_status": t.last_status,
                "records_ingested": t.records_ingested
            }
            for t in self._tasks.values()
        ]

    def trigger_sync_now(self, task_id: str, new_records: int = 250) -> Dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Schedule task '{task_id}' not found.")

        now_str = datetime.now(timezone.utc).isoformat()
        task.last_run = now_str
        task.last_status = "SUCCESS"
        task.records_ingested += new_records
        task.last_sync_value = now_str.split("T")[0]

        return {
            "task_id": task.task_id,
            "status": "COMPLETED",
            "incremental_column": task.incremental_column,
            "high_watermark": task.last_sync_value,
            "new_rows_imported": new_records,
            "timestamp": now_str
        }

ingestion_scheduler = IngestionSchedulerEngine()

