import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/videos/`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Request failed: " + response.status);
        }
        return response.json();
      })
      .then((data) => setVideos(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h1>CreatorFlow</h1>
      {error && <p>Error: {error}</p>}
      <ul>
        {videos.map((video) => (
          <li key={video.id}>
            {video.title} - {video.file_size_display} - {video.status}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;