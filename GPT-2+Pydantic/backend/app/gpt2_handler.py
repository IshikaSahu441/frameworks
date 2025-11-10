import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import time
import os
import pathlib
from pathlib import Path

class GPT2Generator:
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Prefer repository layout: backend/gpt2-storyteller
            repo_root = Path(__file__).resolve().parents[2]
            backend_dir = Path(__file__).resolve().parents[1]
            candidate_primary = backend_dir.parent / "gpt2-storyteller"  # repo_root/gpt2-storyteller
            candidate_backend = backend_dir / "gpt2-storyteller"        # backend/gpt2-storyteller

            if candidate_backend.exists():
                model_path = candidate_backend
            elif candidate_primary.exists():
                model_path = candidate_primary
            else:
                model_path = backend_dir / "gpt2-storyteller"  # best guess
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.model_path = model_path
        self.load_model()
    
    def load_model(self):
        try:
            print("Loading fine-tuned GPT-2 model...")
            self.model = GPT2LMHeadModel.from_pretrained(self.model_path)
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_path)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model.to(self.device)
            self.model.eval()
            print("Model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to base GPT-2 if fine-tuned model fails
            print("Loading base GPT-2 model as fallback...")
            self.model = GPT2LMHeadModel.from_pretrained("gpt2")
            self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.to(self.device)
            self.model.eval()
    
    def generate_text(self, prompt: str, max_length: int = 100, 
                     temperature: float = 0.7, top_p: float = 0.9) -> str:
        """Generate text using the fine-tuned GPT-2 model"""
        start_time = time.time()
        
        try:
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,
                    num_return_sequences=1
                )
            
            # Decode generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the original prompt from the generated text
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            processing_time = time.time() - start_time
            
            return generated_text, processing_time
            
        except Exception as e:
            print(f"Error during generation: {e}")
            return f"Error generating text: {str(e)}", time.time() - start_time

# Global instance
generator = GPT2Generator()