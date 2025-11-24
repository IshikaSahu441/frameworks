import pyarrow as pa
import daft
from temporalio import activity


@activity.defn
async def preprocess(arrow_bytes: bytes) -> bytes:
    reader = pa.ipc.open_file(pa.BufferReader(arrow_bytes))
    table = reader.read_all()


    df = daft.from_arrow(table)


    # Example feature: is_high_income
    df = df.with_column("is_high_income", df["income"] > 50000)


    out_table = df.to_arrow()
    activity.logger.info("Preprocessed table rows=%d", out_table.num_rows)


    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_file(sink, out_table.schema)
    writer.write(out_table)
    writer.close()
    return sink.getvalue().to_pybytes()