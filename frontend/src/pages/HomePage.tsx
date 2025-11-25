import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { startProcessing, uploadPodcast } from "../api/podcasts";

export default function HomePage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [enableTts, setEnableTts] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!file && !url) {
      setError("Upload an audio file or provide a public URL.");
      return;
    }

    try {
      setIsSubmitting(true);
      const formData = new FormData();
      if (file) {
        formData.append("file", file);
      }
      if (url) {
        formData.append("podcast_url", url);
      }

      const uploadResponse = await uploadPodcast(formData);
      const jobId = uploadResponse.job_id;
      await startProcessing(jobId, enableTts);
      navigate(`/status/${jobId}?tts=${enableTts ? "1" : "0"}`);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Upload failed.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main
      style={{
        maxWidth: "880px",
        margin: "0 auto",
        padding: "3rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "2rem",
      }}
    >
      <section className="card" style={{ gap: "1.5rem", display: "flex", flexDirection: "column" }}>
        <div className="tag">PodSummarize</div>
        <h1 style={{ fontSize: "2.75rem", margin: 0 }}>Transform podcasts into concise insights.</h1>
        <p style={{ margin: 0, maxWidth: "640px", color: "#636e72" }}>
          PodSummarize transcribes, diarizes, and summarizes any podcast episode using state-of-the-art
          speech and language models. Upload your audio or link to a public episode to begin.
        </p>
      </section>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Upload or Link a Podcast</h2>
        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}
        >
          <div className="grid">
            <label style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <span style={{ fontWeight: 600 }}>Upload audio (MP3/WAV)</span>
              <input
                type="file"
                accept="audio/mpeg,audio/wav"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>

            <label style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <span style={{ fontWeight: 600 }}>Or paste a public podcast URL</span>
              <input
                type="url"
                placeholder="https://example.com/episode.mp3"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                style={{
                  padding: "0.75rem 1rem",
                  borderRadius: "12px",
                  border: "1px solid #dfe6e9",
                  fontSize: "1rem",
                }}
              />
            </label>
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <input
              type="checkbox"
              checked={enableTts}
              onChange={(event) => setEnableTts(event.target.checked)}
            />
            <span>Generate an audio summary (TTS)</span>
          </label>

          {error && (
            <div
              style={{
                padding: "0.75rem 1rem",
                borderRadius: "12px",
                background: "rgba(214, 48, 49, 0.12)",
                color: "#d63031",
              }}
            >
              {error}
            </div>
          )}

          <button className="button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Uploading..." : "Start Processing"}
          </button>
        </form>
      </section>
    </main>
  );
}


