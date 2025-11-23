import daft
import pyarrow as pa
from temporalio import activity

@activity.defn
async def daft_filter(arrow_bytes: bytes) -> list[dict]:
    reader = pa.ipc.open_file(pa.BufferReader(arrow_bytes))
    table = reader.read_all()

    df = daft.from_arrow(table)
    df = df.where(df["age"] > 30)

    result = df.to_arrow().to_pylist()
    return result
