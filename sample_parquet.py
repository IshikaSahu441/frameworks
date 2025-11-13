import pandas as pd
df = pd.DataFrame({
    "id": range(1,11),
    "group": ["A","B","A","C","B","A","C","C","B","A"],
    "value1": [0.1*i for i in range(10)],
    "value2": [i*2 for i in range(10)]
})
df.to_parquet("large_dataset.parquet", index=False)
