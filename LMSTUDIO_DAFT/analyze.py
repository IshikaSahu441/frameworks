"""
Code analyzer that uses LM Studio embeddings to:
1. Find similar code blocks
2. Analyze code patterns
3. Suggest potential improvements
"""
import os
import json
import numpy as np
from pathlib import Path
from openai import OpenAI
from typing import List, Dict, Any
import textwrap
from scipy.spatial.distance import cosine

class CodeAnalyzer:
    def __init__(self, embeddings_path: str):
        """Initialize with path to embeddings.json"""
        self.data = self._load_embeddings(embeddings_path)
        self.client = OpenAI(
            base_url=os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio")
        )
    
    def _load_embeddings(self, path: str) -> List[Dict[str, Any]]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def find_similar_code(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        similarities = []
        for i, file1 in enumerate(self.data):
            for j, file2 in enumerate(self.data[i+1:], i+1):
                sim = 1 - cosine(file1['embedding'], file2['embedding'])
                if sim > threshold:
                    similarities.append({
                        'file1': file1['filename'],
                        'file2': file2['filename'],
                        'similarity': sim,
                        'code1': file1['code'],
                        'code2': file2['code']
                    })
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)
    
    def get_code_stats(self) -> List[Dict[str, Any]]:
        stats = []
        for file_data in self.data:
            code = file_data['code']
            lines = code.split('\n')
            stats.append({
                'filename': file_data['filename'],
                'total_lines': len(lines),
                'code_lines': sum(1 for l in lines if l.strip() and not l.strip().startswith('#')),
                'comment_lines': sum(1 for l in lines if l.strip().startswith('#')),
                'empty_lines': sum(1 for l in lines if not l.strip()),
                'functions': len([l for l in lines if l.strip().startswith('def ')]),
                'classes': len([l for l in lines if l.strip().startswith('class ')])
            })
        return stats

def main():
    embeddings_path = Path('output/embeddings.json')
    if not embeddings_path.exists():
        print(" No embeddings found. Run main.py first to generate embeddings.")
        return
    
    analyzer = CodeAnalyzer(str(embeddings_path))
    
    # Print header
    print("\n" + "="*60)
    print(" Code Analysis Report")
    print("="*60)
    
    # Show code statistics
    print("\n📊 Code Statistics:")
    print("-"*60)
    stats = analyzer.get_code_stats()
    for stat in stats:
        print(f"\n {stat['filename']}:")
        print(f"  • Total lines: {stat['total_lines']}")
        print(f"  • Code lines: {stat['code_lines']}")
        print(f"  • Comment lines: {stat['comment_lines']}")
        print(f"  • Empty lines: {stat['empty_lines']}")
        print(f"  • Functions: {stat['functions']}")
        print(f"  • Classes: {stat['classes']}")
    
    # Find similar code
    print("\nSimilar Code Blocks:")
    print("-"*60)
    similar = analyzer.find_similar_code(threshold=0.8)
    if similar:
        for idx, match in enumerate(similar, 1):
            print(f"\nMatch #{idx} (Similarity: {match['similarity']:.2%})")
            print(f"Files: {match['file1']} ↔️ {match['file2']}")
            print("\nFile 1 preview:")
            print(textwrap.indent(match['code1'][:200] + "...", "  "))
            print("\nFile 2 preview:")
            print(textwrap.indent(match['code2'][:200] + "...", "  "))
    else:
        print("No significantly similar code blocks found.")

if __name__ == '__main__':
    main()