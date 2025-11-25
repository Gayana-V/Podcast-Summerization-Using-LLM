import { api } from "./client";
import {
  ProcessResponse,
  ResultsResponse,
  UploadResponse,
} from "../types";

export async function uploadPodcast(formData: FormData): Promise<UploadResponse> {
  const { data } = await api.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function startProcessing(
  jobId: string,
  enableTts: boolean,
): Promise<ProcessResponse> {
  const { data } = await api.post<ProcessResponse>("/process", {
    job_id: jobId,
    enable_tts: enableTts,
  });
  return data;
}

export async function fetchResults(jobId: string): Promise<ResultsResponse> {
  const { data } = await api.get<ResultsResponse>(`/results/${jobId}`);
  return data;
}


