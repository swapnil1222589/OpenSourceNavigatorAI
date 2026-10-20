'use client';

import React from 'react';
import {
  Compass,
  Cpu,
  GitBranch,
  ShieldCheck,
  Award,
  Terminal,
  Layers,
  Sparkles,
} from 'lucide-react';

export const AboutView: React.FC = () => {
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Hero Banner */}
      <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-slate-900/80 to-slate-950 p-8 shadow-2xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 mb-4">
            <Award className="h-3.5 w-3.5" />
            <span>Hacktoberfest Hack Day Pune × NIAT–ADYPU</span>
          </div>

          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            OpenSource Navigator <span className="text-emerald-400">AI</span>
          </h2>
          <p className="mt-2 text-base text-slate-300 font-medium">
            Your AI guide to your first open-source contribution.
          </p>
          <p className="mt-4 text-xs sm:text-sm text-slate-400 leading-relaxed max-w-2xl">
            Designed for students and early-career developers venturing into open source.
            Rather than feeling overwhelmed by unfamiliar enterprise codebases and cryptic issue trackers,
            OpenSource Navigator AI transforms complex public GitHub issues into structured, approachable,
            and step-by-step contribution roadmaps powered by local open-weight AI.
          </p>
        </div>
      </div>

      {/* Prize Category & Mission */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <div className="flex items-center gap-3 mb-3 text-emerald-400">
            <Award className="h-5 w-5" />
            <h3 className="font-bold text-white text-base">Prize Category</h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Targeting the <strong className="text-emerald-400">Best Open-Source AI Project</strong> prize category. Built strictly with open standards, zero commercial vendor lock-in, and full local execution on consumer hardware.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <div className="flex items-center gap-3 mb-3 text-purple-400">
            <Sparkles className="h-5 w-5" />
            <h3 className="font-bold text-white text-base">Open-Weight AI</h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Uses locally running open-weight language models via <strong className="text-purple-400">Ollama</strong> (e.g. Qwen / DeepSeek). No paid proprietary API keys or external telemetry required.
          </p>
        </div>
      </div>

      {/* Architecture Overview */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center gap-3 mb-4 text-sky-400">
          <Layers className="h-5 w-5" />
          <h3 className="font-bold text-white text-base">System Architecture</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <div className="font-bold text-emerald-400 mb-1 flex items-center gap-1.5">
              <Compass className="h-4 w-4" />
              <span>Frontend (Next.js)</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Next.js App Router, TypeScript, Tailwind CSS, Lucide icons. Responsive developer dashboard with real-time issue search, filtering, and local roadmap persistence.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <div className="font-bold text-purple-400 mb-1 flex items-center gap-1.5">
              <Terminal className="h-4 w-4" />
              <span>Backend (FastAPI)</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Python 3, FastAPI, Pydantic data schemas, HTTPX async clients. Query builders for GitHub REST API, rate-limit caching, and prompt sanitizers for AI inference.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <div className="font-bold text-amber-400 mb-1 flex items-center gap-1.5">
              <Cpu className="h-4 w-4" />
              <span>Inference Engine</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Ollama local HTTP API running open-weight models. Generates deterministic JSON responses with strict validation and safe hypothesis framing.
            </p>
          </div>
        </div>
      </div>

      {/* Security & Safety Posture */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center gap-3 mb-4 text-rose-400">
          <ShieldCheck className="h-5 w-5" />
          <h3 className="font-bold text-white text-base">Security & Guardrails</h3>
        </div>

        <ul className="space-y-3 text-xs sm:text-sm text-slate-300">
          <li className="flex items-start gap-2.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-2 shrink-0" />
            <span>
              <strong>Untrusted Input Sanitization:</strong> Public GitHub issue text is treated strictly as untrusted external data and never concatenated as raw system instructions.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-2 shrink-0" />
            <span>
              <strong>Zero Token Leakage:</strong> Optional GitHub API tokens are kept strictly inside the server environment and are never returned to the browser or committed to version control.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-2 shrink-0" />
            <span>
              <strong>Explicit Hypotheses:</strong> Because the AI model analyzes issue text rather than scanning entire private git repos, all suggested files and directories are explicitly designated as hypotheses.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-2 shrink-0" />
            <span>
              <strong>Zero Unattended Actions:</strong> The application does not automatically clone untrusted repos, execute code, or submit unauthorized pull requests.
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
};
