from temporalio import workflow
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from activities.validate import validate_records
    from activities.to_arrow import to_arrow
    from activities.preprocess import preprocess
    from activities.train_model import train_model
    from activities.serve_model import serve_model
    from activities.predict import call_prediction


@workflow.defn
class TrainingPipelineWorkflow:
    @workflow.run
    async def run(self, records: list[dict], pred_age: int, pred_income: float):

        validated = await workflow.execute_activity(
            validate_records,
            records,
            schedule_to_close_timeout=timedelta(seconds=30),
        )

        arrow_bytes = await workflow.execute_activity(
            to_arrow,
            validated,
            schedule_to_close_timeout=timedelta(seconds=30),
        )

        processed = await workflow.execute_activity(
            preprocess,
            arrow_bytes,
            schedule_to_close_timeout=timedelta(seconds=30),
        )

        model_bytes = await workflow.execute_activity(
            train_model,
            processed,
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            serve_model,
            model_bytes,
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        result = await workflow.execute_activity(
            call_prediction,
            args=[pred_age, pred_income],
            schedule_to_close_timeout=timedelta(seconds=15),
        )

        return {
            "age": pred_age,
            "income": pred_income,
            "prediction": result,
        }
