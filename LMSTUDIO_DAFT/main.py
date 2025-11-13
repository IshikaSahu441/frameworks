"""
Parallel Code Embedding Generator using Daft + LM Studio

This script reads Python code files from the 'code_samples' directory,
and uses Daft's parallel processing capabilities to generate embeddings
via LM Studio's OpenAI-compatible API.

Key Features:
- True parallel processing with Daft UDFs
- Automatic batching and error handling
- Memory-efficient DataFrame operations
- Vectorized embedding generation
"""

import os
import json
import daft
from typing import List
from openai import OpenAI
from daft.datatype import DataType
from daft.expressions import col, Expression
from daft.ai.provider import load_provider
from daft.functions.ai import embed_text
import argparse

# --- Configuration ---
INPUT_DIR = "code_samples"
OUTPUT_DIR = "output"
MODEL_NAME = "text-embedding-nomic-embed-text-v1.5"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Step 1: Create sample code file if none exist ---
if not any(f.endswith('.py') for f in os.listdir(INPUT_DIR)):
    print("Creating a sample code file since none exist...")
    with open(os.path.join(INPUT_DIR, "example.py"), "w", encoding="utf-8") as f:
        f.write('''def greet(name):
    """Say hello to someone."""
    return f"Hello, {name}!"

def add(a, b):
    """Add two numbers."""
    return a + b
''')

files_data = []
for fname in os.listdir(INPUT_DIR):
    if fname.endswith(".py"):
        with open(os.path.join(INPUT_DIR, fname), "r", encoding="utf-8") as f:
            files_data.append({
                "filename": fname,
                "code": f.read()
            })

if not files_data:
    print("No Python files found in 'code_samples' directory!")
    exit(1)

df = daft.from_pydict({
    "filename": [f["filename"] for f in files_data],
    "code": [f["code"] for f in files_data]
})

print(f"\nFound {len(df)} Python files to analyze.")
df = df.repartition(os.cpu_count() or 2) 
parser = argparse.ArgumentParser()
parser.add_argument("--runner", choices=["threads", "ray", "daft"], default="threads",
                    help="Execution mode: 'threads' for threaded HTTP calls (safe on Windows), 'ray' to use Ray runner for Daft native parallelism, 'daft' to attempt native Daft embed_text on current runner.")
args = parser.parse_args()

if args.runner == "ray":
    try:
        daft.set_runner_ray()
        print(" Daft runner set to Ray (native parallelism enabled)")
    except Exception as e:
        print(f"Could not set Daft Ray runner: {e}")

print(f"\nGenerating embeddings using runner='{args.runner}'...")

rows = df.collect().to_pylist()

def generate_embedding_for_row(row):
    text = row.get("code", "")
    filename = row.get("filename")
    try:
        client = OpenAI(
            base_url=os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio")
        )
        response = client.embeddings.create(
            model=MODEL_NAME,
            input=text
        )
        emb = response.data[0].embedding
        print(f"Generated embedding for {filename}")
        return {"filename": filename, "code": text, "embedding": emb}
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        return {"filename": filename, "code": text, "embedding": []}

results = []
if args.runner == "threads":
    from concurrent.futures import ThreadPoolExecutor
    max_workers = min(32, (os.cpu_count() or 1) * 5)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for res in ex.map(generate_embedding_for_row, rows):
            results.append(res)

elif args.runner in ("ray", "daft"):
    try:
        if args.runner == "ray":
            try:
                daft.context.set_runner_ray()
            except Exception:
                raise
        provider = load_provider("lm_studio")
        df = df.with_column("embedding", embed_text(col("code"), provider=provider, model=MODEL_NAME))
        res_rows = df.collect().to_pylist()
        for r in res_rows:
            results.append({"filename": r["filename"], "code": r["code"], "embedding": r.get("embedding", [])})

    except Exception as e:
        print(f"Daft native embed_text failed ({str(e)}). Falling back to threaded mode.")
        from concurrent.futures import ThreadPoolExecutor
        max_workers = min(32, (os.cpu_count() or 1) * 5)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for res in ex.map(generate_embedding_for_row, rows):
                results.append(res)

else:
    raise ValueError(f"Unknown runner: {args.runner}")

output_path = os.path.join(OUTPUT_DIR, "embeddings.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nEmbeddings successfully generated and saved to: {output_path}")
print("\nSample Embeddings (first 5 dimensions):")
for item in results:
    print(f"\n {item['filename']}:")
    print("  ", item["embedding"][:5], "...")

# --- Daft Usage ---

# Daft DataFrame creation:
# Convert Python file data into a Daft DataFrame for parallel + distributed processing.
# (Daft works like a parallel Pandas but optimized for scalable data workflows.)

# Repartitioning step:
# Split the DataFrame into multiple partitions equal to the number of CPU cores.
# Each partition can be processed in parallel by Daft’s execution engine.

# 3Embedding generation (when runner='daft' or 'ray'):
# Daft’s embed_text() is a vectorized UDF that applies the LM Studio embedding model
# across all rows in parallel — no manual threading required.

# Provider abstraction:
# Daft integrates with external AI providers (here LM Studio via load_provider)
# to handle inference calls efficiently and in parallel.

# Runner selection:
# Daft can run using:
#   - Its own native thread/process runner (default)
#   - A Ray backend for distributed multi-node execution

# Collecting results:
# df.collect() triggers Daft’s lazy execution plan — executing all transformations
# (reading, repartitioning, embedding) in a parallel, batched manner before returning results.

# Batch inference pipeline:
# Daft manages memory-efficient, batched inference by automatically chunking
# large text/code data and distributing it across available resources.

# Error handling + fallback:
# If Daft or Ray embedding fails, the script falls back to a ThreadPool-based
# parallel embedding mode, ensuring robustness across systems.

# Short Summary:
# Daft is handling data orchestration, partitioning, parallel execution,
# and vectorized batch inference — leaving you to write simple, declarative code.
