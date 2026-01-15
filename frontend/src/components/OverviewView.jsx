import { useState } from "react";
import { safeFetch, pretty, API_BASE } from "../utils/api";

export default function OverviewView() {
  const [healthOutput, setHealthOutput] = useState("");

  const runHealthCheck = async () => {
    setHealthOutput("Checking /health ...");
    try {
      const res = await safeFetch("/health");
      setHealthOutput(`Status ${res.status}\n${pretty(res.data)}`);
    } catch (err) {
      setHealthOutput(`Error: ${err}`);
    }
  };

  return (
    <section className="view is-visible">
      <div className="grid-2">
        <div className="card">
          <h2>Welcome</h2>
          <p>
            This React UI lets you explore the <strong>NBA Analytics API</strong> without
            touching Swagger or curl.
          </p>
          <ul className="bullet-list">
            <li>Run quick health checks</li>
            <li>Browse players and teams</li>
            <li>Inspect games</li>
          </ul>
          <button type="button" className="btn primary" onClick={runHealthCheck}>
            Run Health Check
          </button>
          <pre className="code-block small muted">{healthOutput}</pre>
        </div>
        <div className="card">
          <h2>API Base</h2>
          <p className="hint">
            Current API base URL:
            <br />
            <code>{API_BASE}</code>
          </p>
          <p className="hint">
            Change via <code>VITE_API_BASE_URL</code> env var when running Vite.
          </p>
        </div>
      </div>
    </section>
  );
}



