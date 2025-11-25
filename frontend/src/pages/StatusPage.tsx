import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { fetchResults } from "../api/podcasts";
import { ProcessingStage, ResultsResponse } from "../types";

const stageOrder: ProcessingStage[] = [
  "uploaded",
  "transcribing",
  "diarizing",
  "summarizing",
  "tts",
  "completed",
];

const stageLabels: Record<ProcessingStage, string> = {
  uploaded: "Upload complete",
  transcribing: "Transcribing audio",
  diarizing: "Running diarization",
  summarizing: "Creating summary",
  tts: "Generating summary audio",
  completed: "All done",
  failed: "Failed",
};

export default function StatusPage() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const includeTts = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("tts") !== "0";
  }, [location.search]);

  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filteredStages = useMemo(() => {
    if (includeTts) {
      return stageOrder;
    }
    return stageOrder.filter((stage) => stage !== "tts");
  }, [includeTts]);

  const activeIndex = useMemo(() => {
    const stage = results?.status.stage ?? "uploaded";
    const index = filteredStages.indexOf(stage);
    return index === -1 ? filteredStages.length - 1 : index;
  }, [results, filteredStages]);

  useEffect(() => {
    let interval: number;

    async function poll() {
      try {
        const response = await fetchResults(jobId);
        setResults(response);

        if (response.status.stage === "completed") {
          window.clearInterval(interval);
          navigate(`/results/${jobId}`, { replace: true });
        } else if (response.status.stage === "failed") {
          window.clearInterval(interval);
        }
      } catch (pollError) {
        const message =
          pollError instanceof Error ? pollError.message : "Unable to fetch status.";
        setError(message);
        window.clearInterval(interval);
      }
    }

    poll();
    interval = window.setInterval(poll, 3500);

    return () => window.clearInterval(interval);
  }, [jobId, navigate]);

  const stage = results?.status.stage ?? "uploaded";
  const errors = results?.status.errors ?? [];

  return (
    <main
      style={{
        maxWidth: "720px",
        margin: "0 auto",
        padding: "3rem 1.5rem",
      }}
    >
      <section className="card" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <div>
          <div className="tag">Processing status</div>
          <h1 style={{ marginBottom: "0.4rem" }}>We&apos;re summarizing your podcast</h1>
          <p style={{ margin: 0, color: "#636e72" }}>
            Keep this page open — we&apos;ll move you to the results automatically once the pipeline
            finishes.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gap: "1rem",
          }}
        >
          {filteredStages.map((item, index) => {
            const isActive = index <= activeIndex;
            const isCurrent = stage === item;

            return (
              <div
                key={item}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "1rem",
                }}
              >
                <span className={`progress-dot ${isActive ? "active" : ""}`} />
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                  <strong>{stageLabels[item]}</strong>
                  {isCurrent && results?.status.detail && (
                    <span style={{ color: "#636e72" }}>{results.status.detail}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {stage === "failed" && errors.length > 0 && (
          <div
            style={{
              background: "rgba(214, 48, 49, 0.12)",
              color: "#d63031",
              padding: "1rem",
              borderRadius: "12px",
            }}
          >
            <strong>We ran into a problem:</strong>
            <ul>
              {errors.map((msg) => (
                <li key={msg}>{msg}</li>
              ))}
            </ul>
          </div>
        )}

        {error && (
          <div
            style={{
              background: "rgba(214, 48, 49, 0.12)",
              color: "#d63031",
              padding: "1rem",
              borderRadius: "12px",
            }}
          >
            {error}
          </div>
        )}
      </section>
    </main>
  );
}


