"use client";

import { useState } from "react";
import { apiFetch } from "../../lib/api";

const defaultJobJson = {
  title: "Senior Frontend Engineer",
  location: "Remote",
  responsibilities: [
    "Build accessible user interfaces",
    "Collaborate with product and design",
    "Improve performance metrics",
  ],
};

const defaultCandidateChunks = [
  {
    id: "chunk-1",
    heading: "Experience",
    content: "Led frontend teams using React and TypeScript.",
  },
];

export default function DemoPage() {
  const [jdText, setJdText] = useState(
    "We are hiring a Senior Frontend Engineer with strong React experience."
  );
  const [result, setResult] = useState<string>("Results will appear here.");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAction(action: "analyze" | "assess" | "rewrite" | "qa") {
    setIsLoading(true);
    setError(null);

    try {
      let data: unknown;
      if (action === "analyze") {
        data = await apiFetch("/analyze_jd", {
          method: "POST",
          body: JSON.stringify({ jd_text: jdText }),
        });
      } else if (action === "assess") {
        data = await apiFetch("/assess", {
          method: "POST",
          body: JSON.stringify({
            jd_json: defaultJobJson,
            candidate_chunks: defaultCandidateChunks,
          }),
        });
      } else if (action === "rewrite") {
        data = await apiFetch("/rewrite_cv", {
          method: "POST",
          body: JSON.stringify({ project_id: "demo-project", mode: "conservative" }),
        });
      } else {
        data = await apiFetch("/qa", {
          method: "POST",
          body: JSON.stringify({
            jd_json: defaultJobJson,
            candidate_chunks: defaultCandidateChunks,
          }),
        });
      }

      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-6">
      <section>
        <h1 className="text-3xl font-semibold">JobFit Demo</h1>
        <p className="mt-2 text-slate-300">
          Use the controls below to call the mocked AI endpoints.
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <label className="text-sm font-medium text-slate-200" htmlFor="jd">
          Job description text
        </label>
        <textarea
          id="jd"
          className="min-h-[160px] rounded-md border border-slate-700 bg-slate-900 p-3 text-slate-100"
          value={jdText}
          onChange={(event) => setJdText(event.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => handleAction("analyze")}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500"
            disabled={isLoading}
          >
            Analyze JD
          </button>
          <button
            type="button"
            onClick={() => handleAction("assess")}
            className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-500"
            disabled={isLoading}
          >
            Assess Fit
          </button>
          <button
            type="button"
            onClick={() => handleAction("rewrite")}
            className="rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-purple-500"
            disabled={isLoading}
          >
            Rewrite CV
          </button>
          <button
            type="button"
            onClick={() => handleAction("qa")}
            className="rounded-md bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-500"
            disabled={isLoading}
          >
            QA Suggestions
          </button>
        </div>
        {error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : (
          <p className="text-sm text-slate-400">
            {isLoading ? "Loading..." : "Results show below."}
          </p>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-lg font-semibold">Response</h2>
        <pre className="overflow-auto rounded-md border border-slate-700 bg-slate-950 p-4 text-sm text-slate-200">
          {result}
        </pre>
      </section>
    </main>
  );
}
