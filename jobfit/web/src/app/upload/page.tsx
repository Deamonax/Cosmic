"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import { postForm } from "../../lib/api";

type CVSection = {
  name: string;
  bullets: string[];
};

type CVUploadResponse = {
  source_id: string;
  cv_preview: { sections: CVSection[] };
  saved: boolean;
};

type ContextSource = {
  id: string;
  filename: string;
};

type ContextUploadResponse = {
  sources: ContextSource[];
  paragraph_counts: number[];
  saved: boolean;
};

const docxMime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

export default function UploadPage() {
  const [candidateId, setCandidateId] = useState("demo");
  const [notes, setNotes] = useState("");
  const [cvError, setCvError] = useState<string | null>(null);
  const [contextError, setContextError] = useState<string | null>(null);
  const [cvUploading, setCvUploading] = useState(false);
  const [contextUploading, setContextUploading] = useState(false);
  const [cvResult, setCvResult] = useState<CVUploadResponse | null>(null);
  const [contextResult, setContextResult] = useState<ContextUploadResponse | null>(null);

  const normalizedCandidateId = candidateId.trim() || "demo";

  const handleCvSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCvError(null);
    setCvUploading(true);

    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("cv_file") as HTMLInputElement | null;
    const files = fileInput?.files ?? null;

    if (!files || files.length === 0) {
      setCvUploading(false);
      setCvError("Select a CV file to upload.");
      return;
    }

    const file = files[0];
    if (![
      "application/pdf",
      docxMime,
    ].includes(file.type)) {
      setCvUploading(false);
      setCvError("Please upload a PDF or DOCX file.");
      return;
    }

    const formData = new FormData();
    formData.append("candidate_id", normalizedCandidateId);
    formData.append("cv_file", file);

    try {
      const response = await postForm<CVUploadResponse>("/upload/cv", formData);
      setCvResult(response);
      setCvError(null);
      form.reset();
    } catch (error) {
      setCvResult(null);
      setCvError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setCvUploading(false);
    }
  };

  const handleContextSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setContextError(null);
    setContextUploading(true);

    const form = event.currentTarget;
    const transcriptInput = form.elements.namedItem("transcripts") as HTMLInputElement | null;
    const transcriptFiles = transcriptInput?.files ? Array.from(transcriptInput.files) : [];
    const trimmedNotes = notes.trim();

    if (transcriptFiles.length === 0 && trimmedNotes.length === 0) {
      setContextError("Add files or notes before uploading.");
      setContextUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append("candidate_id", normalizedCandidateId);

    transcriptFiles.forEach((file) => {
      formData.append("transcripts", file);
    });

    if (trimmedNotes) {
      formData.append("notes", trimmedNotes);
    }

    try {
      const response = await postForm<ContextUploadResponse>("/upload/context", formData);
      setContextResult(response);
      setContextError(null);
      form.reset();
      setNotes("");
    } catch (error) {
      setContextResult(null);
      setContextError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setContextUploading(false);
    }
  };

  const contextRows = contextResult
    ? contextResult.sources.map((source, index) => ({
        ...source,
        paragraphCount: contextResult.paragraph_counts[index] ?? 0,
      }))
    : [];

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 p-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">Upload candidate context</h1>
        <p className="text-sm text-slate-400">Uploads stay on this machine.</p>
      </header>

      <div className="flex flex-col gap-4 md:flex-row md:items-end md:gap-6">
        <label className="flex w-full flex-col gap-2 md:max-w-xs">
          <span className="text-sm font-medium text-slate-300">Candidate ID</span>
          <input
            type="text"
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="demo"
          />
        </label>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-lg border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="text-xl font-semibold">CV</h2>
          <p className="mt-1 text-sm text-slate-400">Supported types: PDF, DOCX.</p>
          <form onSubmit={handleCvSubmit} className="mt-4 space-y-4">
            <input
              type="file"
              name="cv_file"
              accept=".pdf,.docx"
              className="block w-full text-sm text-slate-200 file:mr-4 file:rounded-md file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-indigo-500"
            />
            {cvError && <p className="text-sm text-red-400">{cvError}</p>}
            <button
              type="submit"
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-700"
              disabled={cvUploading}
            >
              {cvUploading ? "Uploading..." : "Upload CV"}
            </button>
          </form>
        </section>

        <section className="rounded-lg border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="text-xl font-semibold">Context</h2>
          <p className="mt-1 text-sm text-slate-400">Upload transcripts or add quick notes.</p>
          <form onSubmit={handleContextSubmit} className="mt-4 space-y-4">
            <input
              type="file"
              name="transcripts"
              multiple
              accept=".pdf,.docx,.txt"
              className="block w-full text-sm text-slate-200 file:mr-4 file:rounded-md file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-indigo-500"
            />
            <label className="flex flex-col gap-2 text-sm">
              <span className="text-sm font-medium text-slate-300">Notes</span>
              <textarea
                name="notes"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={4}
                className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Add a quick summary or reminder"
              />
            </label>
            {contextError && <p className="text-sm text-red-400">{contextError}</p>}
            <button
              type="submit"
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-700"
              disabled={contextUploading}
            >
              {contextUploading ? "Uploading..." : "Upload context"}
            </button>
          </form>
        </section>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-6">
          <h3 className="text-lg font-semibold">CV preview</h3>
          {!cvResult ? (
            <p className="mt-2 text-sm text-slate-400">Upload a CV to see the parsed sections.</p>
          ) : cvResult.cv_preview.sections.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">No sections detected in this CV.</p>
          ) : (
            <ul className="mt-4 space-y-4 text-sm">
              {cvResult.cv_preview.sections.map((section, sectionIndex) => (
                <li key={`${section.name}-${sectionIndex}`} className="space-y-2">
                  <p className="font-medium text-slate-100">{section.name}</p>
                  <ul className="space-y-1 text-slate-300">
                    {section.bullets.map((bullet, index) => (
                      <li key={`${section.name}-${index}`}>• {bullet}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-6">
          <h3 className="text-lg font-semibold">Context result</h3>
          {!contextResult ? (
            <p className="mt-2 text-sm text-slate-400">Upload transcripts or notes to preview paragraphs.</p>
          ) : contextRows.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">No transcripts processed yet.</p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-slate-300">
                  <tr>
                    <th className="px-2 py-1">Filename</th>
                    <th className="px-2 py-1 text-right">Paragraphs</th>
                  </tr>
                </thead>
                <tbody>
                  {contextRows.map((row) => (
                    <tr key={row.id} className="border-t border-slate-800 text-slate-200">
                      <td className="px-2 py-2">{row.filename}</td>
                      <td className="px-2 py-2 text-right">{row.paragraphCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
