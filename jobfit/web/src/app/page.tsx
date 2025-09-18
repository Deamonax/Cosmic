"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type HealthResponse = {
  ok: boolean;
};

export default function HomePage() {
  const [status, setStatus] = useState<string>("Checking API...");

  useEffect(() => {
    let isMounted = true;

    apiFetch<HealthResponse>("/healthz")
      .then((data) => {
        if (!isMounted) return;
        setStatus(data.ok ? "API is reachable" : "API responded but not OK");
      })
      .catch(() => {
        if (!isMounted) return;
        setStatus("API is not reachable");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
      <h1 className="text-4xl font-bold">JobFit MVP</h1>
      <p className="max-w-xl text-lg text-slate-300">
        JobFit showcases a fully mocked job search assistant. The frontend calls
        the FastAPI backend, which responds using local JSON fixtures.
      </p>
      <div className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-base">
        {status}
      </div>
      <Link
        href="/upload"
        className="text-sm font-medium text-indigo-400 hover:text-indigo-300"
      >
        Upload candidate context
      </Link>
    </main>
  );
}
