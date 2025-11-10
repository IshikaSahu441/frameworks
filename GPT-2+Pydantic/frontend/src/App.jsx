import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [prompt, setPrompt] = useState('');
  const [maxLength, setMaxLength] = useState(100);
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(0.9);
  const [generatedText, setGeneratedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);

  const generateText = async () => {
    setLoading(true);
    setError('');
    setGeneratedText('');
    setStats(null);

    try {
      const response = await axios.post(`${API_BASE}/generate`, {
        prompt,
        max_length: parseInt(maxLength),
        temperature: parseFloat(temperature),
        top_p: parseFloat(topP)
      });

      setGeneratedText(response.data.generated_text);
      setStats({
        processingTime: response.data.processing_time.toFixed(2),
        modelUsed: response.data.model_used
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate text');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim()) {
      generateText();
    }
  };

  return (
    <div className="app">
      <div className="header">
        <h1>Storyteller GPT-2</h1>
        <p>Transform your ideas with AI-powered text generation</p>
      </div>

      <div className="container">
        <div className="input-section">
          <h2 className="section-title">Your Inspiration</h2>
          <form onSubmit={handleSubmit}>
            <textarea
              className="prompt-input"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your creative prompt here... ✨"
              maxLength={500}
            />
            
            <div className="controls">
              <div className="control-group">
                <label className="control-label">Max Length</label>
                <input
                  type="number"
                  className="control-input"
                  value={maxLength}
                  onChange={(e) => setMaxLength(e.target.value)}
                  min="20"
                  max="500"
                />
              </div>
              
              <div className="control-group">
                <label className="control-label">Temperature</label>
                <input
                  type="number"
                  className="control-input"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  min="0.1"
                  max="2.0"
                  step="0.1"
                />
              </div>
              
              <div className="control-group">
                <label className="control-label">Top P</label>
                <input
                  type="number"
                  className="control-input"
                  value={topP}
                  onChange={(e) => setTopP(e.target.value)}
                  min="0.1"
                  max="1.0"
                  step="0.1"
                />
              </div>
              
              <div className="control-group">
                <label className="control-label">Characters: {prompt.length}/500</label>
                <button 
                  type="submit" 
                  className="generate-btn"
                  disabled={loading || !prompt.trim()}
                >
                  {loading ? (
                    <div className="loading">
                      <div className="spinner"></div>
                      Generating...
                    </div>
                  ) : (
                    'Generate Magic 🚀'
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>

        <div className="output-section">
          <h2 className="section-title">AI Creation</h2>
          <div className="output-content">
            {error ? (
              <div className="error">{error}</div>
            ) : generatedText ? (
              generatedText
            ) : (
              <div style={{ color: 'black', textAlign: 'center', padding: '3rem' }}>
                Your generated text will appear here...
              </div>
            )}
          </div>
          
          {stats && (
            <div className="stats">
              <span>Model: {stats.modelUsed}</span>
              <span>Time: {stats.processingTime}s</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;