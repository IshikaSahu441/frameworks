import pyarrow as pa
from temporalio import activity

@activity.defn
async def to_arrow(validated: list[dict]) -> bytes:
    table = pa.Table.from_pylist(validated)
    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_file(sink, table.schema)
    writer.write(table)
    writer.close()
    return sink.getvalue().to_pybytes()
