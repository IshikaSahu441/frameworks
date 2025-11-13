import os
import json
import daft
import numpy as np
from pathlib import Path
from openai import OpenAI
from daft.ai.provider import load_provider
from daft.functions.ai import embed_text
from daft.expressions import col, lit
from daft import udf
from typing import List, Dict, Any
from argparse import ArgumentParser


MODEL_NAME = "text-embedding-nomic-embed-text-v1.5"
EMBEDDING_PATH = Path("output/embeddings.json")
OUTPUT_PATH = Path("output/enhanced_analysis.json")

@udf(return_dtype=daft.DataType.float64())
def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vectors (executed in parallel batches)."""
    v1, v2 = np.array(v1), np.array(v2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def analyze_code(client: OpenAI, code: str) -> str:
    """Use LM Studio (local OpenAI API) to analyze a Python code snippet."""
    prompt = f"""Analyze this Python code and return a JSON object with the following keys:
1. "what" - a short description of what the code does
2. "key_functions" - list or short summary of key functions or logic patterns
3. "improvements" - suggested improvements or optimizations
4. "complexity" - complexity or maintainability concerns

Return only valid JSON. Example format:
{{
    "what": "...",
    "key_functions": ["...", "..."],
    "improvements": "...",
    "complexity": "..."
}}

Code:
```python
{code}
```"""
    try:
        response = client.chat.completions.create(
            model="codellama-7b-instruct",
            messages=[
                {"role": "system", "content": "You are a Python code analysis expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        text = response.choices[0].message.content
        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            return {"raw": text}
    except Exception as e:
        return {"raw": f"Error analyzing code: {str(e)}"}

def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--runner",
        choices=["local", "ray"],
        default="local",
        help="Execution mode: 'local' for standard, 'ray' for distributed Daft execution",
    )
    args = parser.parse_args()
    if args.runner == "ray":
        try:
            import ray
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)
            daft.context.set_runner_ray()
            print("Using Ray as Daft execution backend.")
        except Exception as e:
            print(f"Failed to initialize Ray: {e}. Falling back to local runner.")
    else:
        print("Using local Daft runner (multi-threaded parallelism).")

    client = OpenAI(
        base_url=os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
        api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
    )
    provider = load_provider("lm_studio")

    if not EMBEDDING_PATH.exists():
        print(" No embeddings found. Please run the Daft embedding generator first.")
        return

    with open(EMBEDDING_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    filenames = [d["filename"] for d in data]
    codes = [d["code"] for d in data]
    embeddings = [d["embedding"] for d in data]

    print(f"\nLoaded {len(filenames)} Python files into Daft DataFrame...")

    df = daft.from_pydict({
        "filename": filenames,
        "code": codes,
        "embedding": embeddings,
    })

    print("\n Generating / refreshing embeddings using Daft + LM Studio...")
    df = df.with_column("embedding_refreshed", embed_text(col("code"), provider=provider, model=MODEL_NAME))

    print("\nPerforming similarity computation (in-process)...")
    similar_pairs = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            v1 = np.array(embeddings[i])
            v2 = np.array(embeddings[j])
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                sim = 0.0
            else:
                sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            if sim > 0.8:
                similar_pairs.append({
                    "file1": filenames[i],
                    "file2": filenames[j],
                    "similarity": sim,
                })

    print("\nGenerating explainability reports...")
    analyses = {}
    for fname, code in zip(filenames, codes):
        result = analyze_code(client, code)
        analyses[fname] = result
        print(f"\nAnalyzing: {fname}")
        if isinstance(result, dict) and "raw" not in result:
            what = result.get("what", "")
            key_funcs = result.get("key_functions", "")
            improvements = result.get("improvements", "")
            complexity = result.get("complexity", "")
            if isinstance(key_funcs, list):
                key_funcs_str = "\n".join([f"- {k}" for k in key_funcs])
            else:
                key_funcs_str = str(key_funcs)

            print("1. What the code does")
            print(what)
            print("\n2. Key functions or logic patterns")
            print(key_funcs_str)
            print("\n3. Any improvements or optimizations")
            print(improvements)
            print("\n4. Complexity or maintainability concerns")
            print(complexity)
        else:
            raw_text = result.get("raw") if isinstance(result, dict) else str(result)
            print("1. What the code does")
            print(raw_text)
            print("\n2. Key functions or logic patterns")
            print("N/A")
            print("\n3. Any improvements or optimizations")
            print("N/A")
            print("\n4. Complexity or maintainability concerns")
            print("N/A")
    output_data = {
        "runner": args.runner,
        "similar_pairs": similar_pairs,
        "analyses": analyses,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n Enhanced analysis saved to: {OUTPUT_PATH}")
    print(f"Found {len(similar_pairs)} similar code pairs.")


if __name__ == "__main__":
    main()