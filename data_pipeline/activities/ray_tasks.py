import ray
import pyarrow as pa
from temporalio import activity
import pyarrow.compute as pc

ray.init()

@ray.remote
def increment_age(batch):
    age_array = batch["age"]
    # Vectorized addition
    new_age = pc.add(age_array, pa.scalar(1, pa.int64()))
    batch = batch.set_column(
        batch.schema.get_field_index("age"),
        "age",
        new_age,
    )
    return batch
@activity.defn
async def ray_process(arrow_bytes: bytes) -> bytes:
    reader = pa.ipc.open_file(pa.BufferReader(arrow_bytes))
    table = reader.read_all()

    batches = [table.slice(i, 1000).to_batches()[0] 
               for i in range(0, table.num_rows, 1000)]

    results = ray.get([increment_age.remote(b) for b in batches])
    new_table = pa.Table.from_batches(results)

    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_file(sink, new_table.schema)
    writer.write(new_table)
    writer.close()
    
    return sink.getvalue().to_pybytes()
