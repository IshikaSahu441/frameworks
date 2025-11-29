from temporalio import workflow
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from activities.validate import validate_records
    from activities.preprocess import preprocess
    from activities.train_model import train_model
    from activities.serve_model import serve_model
    from activities.predict import call_prediction

@workflow.defn
class MLTrainingWorkflow:
    @workflow.run
    async def run(self, params: dict):
        """
        params = {
            "dataset_key": str,
            "predict_features": dict   # raw features: yearbuilt, location string, etc.
        }
        """
        workflow.logger.info(f"Workflow received params: {params}")

        dataset_key = params["dataset_key"]
        predict_features = params["predict_features"]

        # --- 1) Validate ---
        validated_key = await workflow.execute_activity(
            validate_records,
            args=[dataset_key],
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        # --- 2) Preprocess ---
        preprocess_out = await workflow.execute_activity(
            preprocess,
            args=[validated_key],
            schedule_to_close_timeout=timedelta(seconds=120),
        )
        processed_key = preprocess_out["processed_key"]
        metadata_key = preprocess_out["metadata_key"]

        # --- 3) Train model ---
        model_key = await workflow.execute_activity(
            train_model,
            args=[processed_key],
            schedule_to_close_timeout=timedelta(seconds=300),
        )

        # --- 4) Serve model ---
        await workflow.execute_activity(
            serve_model,
            args=[model_key, metadata_key],
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        # --- 5) Call prediction ---
        prediction = await workflow.execute_activity(
            call_prediction,
            args=[predict_features],
            schedule_to_close_timeout=timedelta(seconds=30),
        )

        return {
            "input": predict_features,
            "prediction": prediction,
            "dataset_used": processed_key,
        }
