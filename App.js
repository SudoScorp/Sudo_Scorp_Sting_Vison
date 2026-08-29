import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageChange = (event) => {
    setImage(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!image) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', image);

    try {
      const response = await axios.post('http://localhost:8000/api/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResults(response.data);
    } catch (error) {
      console.error("Detection failed:", error);
      alert("Error analyzing image. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>AI Image Detector</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleImageChange} accept="image/*" />
        <button type="submit" disabled={loading || !image}>
          {loading ? 'Analyzing...' : 'Upload Image'}
        </button>
      </form>
      
      {results && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ccc' }}>
          <h2>Results:</h2>
          <p><strong>AI Generated:</strong> {results.aiGenerated ? 'Yes' : 'No'}</p>
          <p><strong>Confidence:</strong> {(results.confidence * 100).toFixed(2)}%</p>
          {results.aiGenerated && <p><strong>Generator:</strong> {results.generator}</p>}
          <p><strong>Policy Status:</strong> {results.policyCheck}</p>
        </div>
      )}
    </div>
  );
}

export default App;
