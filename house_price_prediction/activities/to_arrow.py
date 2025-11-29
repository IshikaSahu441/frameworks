import pyarrow as pa
from temporalio import activity
from typing import List

@activity.defn
async def to_arrow(validated: List[dict]) -> bytes:
    table = pa.Table.from_pylist(validated)
    activity.logger.info("Converted to Arrow with %d rows", table.num_rows)
    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_file(sink, table.schema)
    writer.write(table)
    writer.close()
    return sink.getvalue().to_pybytes()
