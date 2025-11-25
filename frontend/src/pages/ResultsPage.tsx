import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchResults } from "../api/podcasts";
import { ResultsResponse, SpeakerTurn } from "../types";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function toAbsoluteUrl(path?: string | null) {
  if (!path) return undefined;
  if (path.startsWith("http")) return path;
  return `${apiBase}${path}`;
}

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

function speakerColor(index: number) {
  const palette = ["#6c5ce7", "#0984e3", "#00b894", "#fdcb6e", "#e17055"];
  return palette[index % palette.length];
}

export default function ResultsPage() {
  const { jobId = "" } = useParams();
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const response = await fetchResults(jobId);
        setResults(response);
      } catch (loadError) {
        const message =
          loadError instanceof Error ? loadError.message : "Unable to load results.";
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [jobId]);

  const uniqueSpeakers = useMemo(() => {
    const turns = results?.transcript?.turns ?? [];
    const names = Array.from(new Set(turns.map((turn) => turn.speaker)));
    return names;
  }, [results]);

  const handleDownload = () => {
    if (!results?.transcript) return;
    const blob = new Blob([JSON.stringify(results.transcript, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `podsummarize-${jobId}-transcript.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    if (!results?.summary) return;
    const shareData = {
      title: "Podcast summary",
      text: `${results.summary.overview}\n\nView more at PodSummarize.`,
    };

    if (navigator.share) {
      await navigator.share(shareData);
    } else {
      await navigator.clipboard.writeText(shareData.text);
      alert("Summary copied to clipboard.");
    }
  };

  if (loading) {
    return (
      <main style={{ padding: "3rem 1.5rem", maxWidth: "720px", margin: "0 auto" }}>
        <p>Loading results…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main style={{ padding: "3rem 1.5rem", maxWidth: "720px", margin: "0 auto" }}>
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
      </main>
    );
  }

  if (!results) {
    return null;
  }

  const { transcript, summary, audio_url: audioUrl, summary_audio_url: summaryAudioUrl } = results;

  return (
    <main
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "2rem",
        maxWidth: "1040px",
        margin: "0 auto",
        padding: "3rem 1.5rem",
      }}
    >
      <section className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div className="tag">Results ready</div>
        <h1 style={{ marginBottom: "0.5rem" }}>Episode summary</h1>
        <p style={{ margin: 0, color: "#636e72" }}>
          Review the diarized transcript, speaker highlights, and summary audio below.
        </p>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <button className="button" type="button" onClick={handleDownload}>
            Download transcript JSON
          </button>
          <button
            className="button"
            type="button"
            style={{ background: "linear-gradient(135deg, #00b894, #55efc4)" }}
            onClick={handleShare}
          >
            Share summary
          </button>
          <Link to="/" className="button" style={{ background: "linear-gradient(135deg, #2d3436, #636e72)" }}>
            Start another
          </Link>
        </div>
      </section>

      {summary && (
        <section className="card" style={{ display: "grid", gap: "1.5rem" }}>
          <div>
            <h2 style={{ margin: 0 }}>Overall summary</h2>
            <p style={{ margin: "0.5rem 0 0 0", color: "#2d3436" }}>{summary.overview}</p>
          </div>

          <div>
            <h3 style={{ marginBottom: "0.5rem" }}>Key points</h3>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              {summary.key_points.map((point) => (
                <li key={point} style={{ marginBottom: "0.5rem" }}>
                  {point}
                </li>
              ))}
            </ul>
          </div>

          <div className="grid">
            {summary.per_speaker.map((section, index) => (
              <div key={section.speaker} className="summary-section">
                <span
                  className="speaker-label"
                  style={{ color: speakerColor(index), display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
                >
                  <span
                    style={{
                      width: "12px",
                      height: "12px",
                      borderRadius: "50%",
                      background: speakerColor(index),
                      display: "inline-block",
                    }}
                  />
                  {section.speaker}
                </span>
                <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
                  {section.highlights.map((highlight) => (
                    <li key={highlight}>{highlight}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card" style={{ display: "grid", gap: "1.5rem" }}>
        <h2 style={{ margin: 0 }}>Listen</h2>
        {audioUrl && (
          <div>
            <h3>Original audio</h3>
            <audio controls src={toAbsoluteUrl(audioUrl)} style={{ width: "100%" }}>
              Your browser does not support the audio element.
            </audio>
          </div>
        )}

        {summaryAudioUrl && (
          <div>
            <h3>Summary audio</h3>
            <audio controls src={toAbsoluteUrl(summaryAudioUrl)} style={{ width: "100%" }}>
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </section>

      {transcript && (
        <section className="card" style={{ display: "grid", gap: "1.25rem" }}>
          <div>
            <h2 style={{ margin: 0 }}>Diarized transcript</h2>
            <p style={{ margin: "0.5rem 0 0 0", color: "#636e72" }}>
              Speaker turns are color coded. Click any segment to copy the quote.
            </p>
          </div>

          <div className="grid">
            {transcript.turns.map((turn: SpeakerTurn, index) => {
              const speakerIndex = uniqueSpeakers.indexOf(turn.speaker);
              const color = speakerColor(speakerIndex === -1 ? index : speakerIndex);

              return (
                <div
                  key={`${turn.start}-${turn.end}-${index}`}
                  className="transcript-turn"
                  style={{ borderLeft: `4px solid ${color}`, cursor: "pointer" }}
                  onClick={() => navigator.clipboard.writeText(`${turn.speaker}: ${turn.text}`)}
                >
                  <div
                    style={{
                      display: "flex",
                      gap: "0.8rem",
                      alignItems: "center",
                      marginBottom: "0.4rem",
                    }}
                  >
                    <strong style={{ color }}>{turn.speaker}</strong>
                    <span style={{ fontSize: "0.85rem", color: "#636e72" }}>
                      {formatTime(turn.start)} - {formatTime(turn.end)}
                    </span>
                  </div>
                  <p style={{ margin: 0, color: "#2d3436" }}>{turn.text}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </main>
  );
}


