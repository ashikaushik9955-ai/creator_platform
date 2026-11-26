import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // पन्ना खुलने पर videos की सूची लाओ
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

  // token बदलने पर पूछो: "मैं कौन हूँ?"
  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }
    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Session expired");
        }
        return response.json();
      })
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem("token");
        setToken("");
      });
  }, [token]);

  async function handleLogin(event) {
    event.preventDefault();
    setError("");

    const body = new URLSearchParams({ username: email, password: password });

    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body,
    });

    if (!response.ok) {
      setError("Incorrect email or password");
      return;
    }

    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    setPassword("");
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setToken("");
  }

  return (
    <div>
      <h1>CreatorFlow</h1>

      {user ? (
        <p>
          Logged in as {user.email}{" "}
          <button onClick={handleLogout}>Logout</button>
        </p>
      ) : (
        <form onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit">Login</button>
        </form>
      )}

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