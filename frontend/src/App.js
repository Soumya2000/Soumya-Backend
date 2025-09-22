import React, { useState } from "react";
import { createRoot } from "react-dom/client";

function App() {
  const [preference, setPreference] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleRecommend = async () => {
    setLoading(true);
    try {
      const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";
      const response = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preference }),
      });
      const data = await response.json();
      setRecommendations(data);
    } catch (err) {
      console.error(err);
      setRecommendations([]);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 20, maxWidth: 600, margin: "0 auto", fontFamily: "Arial" }}>
      <h1>AI Product Recommender</h1>
      <input
        type="text"
        placeholder="e.g. I want mobile phones under $500"
        value={preference}
        onChange={(e) => setPreference(e.target.value)}
        style={{ width: "100%", padding: 10, marginBottom: 10 }}
      />
      <button onClick={handleRecommend} style={{ width: "100%", padding: 10 }}>
        Get Recommendations
      </button>

      <h2>Recommended Products:</h2>
      {loading ? <p>Loading...</p> : null}
      <ul>
        {recommendations.length > 0 ? (
          recommendations.map((p) => (
            <li key={p.id}>
              {p.name} - ${p.price} [{p.category}]
            </li>
          ))
        ) : (
          <li>No recommendations yet.</li>
        )}
      </ul>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
export default App;
