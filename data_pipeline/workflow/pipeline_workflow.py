from temporalio import workflow
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from activities.validate import validate_records
    from activities.convert import to_arrow
    from activities.ray_tasks import ray_process
    from activities.daft_tasks import daft_filter

@workflow.defn
class DataPipelineWorkflow:

    @workflow.run
    async def run(self, raw_records: list[dict]):
        val = await workflow.execute_activity(
            validate_records,
            raw_records,
            schedule_to_close_timeout=timedelta(seconds=60)
        )

        arrow_tbl = await workflow.execute_activity(
            to_arrow,
            val,
            schedule_to_close_timeout=timedelta(seconds=60)
        )

        processed = await workflow.execute_activity(
            ray_process,
            arrow_tbl,
            schedule_to_close_timeout=timedelta(seconds=120)
        )

        final = await workflow.execute_activity(
            daft_filter,
            processed,
            schedule_to_close_timeout=timedelta(seconds=60)
        )

        return final
