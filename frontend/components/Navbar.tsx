'use client';

import React from 'react';
import { Compass, Sparkles, Cpu, GitBranch, CheckCircle2, AlertCircle } from 'lucide-react';
import { HealthStatus } from '../lib/types';

interface NavbarProps {
  health: HealthStatus | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  healthLoading,
  onRefreshHealth,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 shadow-lg shadow-emerald-500/20">
            <Compass className="h-6 w-6 text-white animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">
                OpenSource Navigator <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">AI</span>
              </span>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
                Hack Day Pune
              </span>
            </div>
            <p className="hidden text-xs text-slate-400 sm:block">
              Your AI guide to your first open-source contribution
            </p>
          </div>
        </div>

        {/* System Health Indicators */}
        <div className="flex items-center gap-3">
          {/* Ollama Status Pill */}
          <button
            onClick={onRefreshHealth}
            title="Click to refresh system health status"
            className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-700 hover:bg-slate-800/80 transition-all cursor-pointer"
          >
            <Cpu className="h-3.5 w-3.5 text-purple-400" />
            <span className="hidden md:inline font-mono">Ollama:</span>
            {healthLoading ? (
              <span className="inline-block h-2 w-2 rounded-full bg-amber-400 animate-ping" />
            ) : health?.ollama.connected ? (
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span className="font-semibold text-emerald-400 truncate max-w-[120px]">
                  {health.ollama.configured_model}
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-rose-400">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                <span>Offline</span>
              </div>
            )}
          </button>

          {/* GitHub API Status Pill */}
          <div className="hidden sm:flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 text-xs text-slate-300">
            <GitBranch className="h-3.5 w-3.5 text-slate-400" />
            <span>GitHub:</span>
            {health?.github.token_configured ? (
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <CheckCircle2 className="h-3 w-3" /> Auth (5k req/h)
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-400" title="Unauthenticated limit: 60 req/h">
                <AlertCircle className="h-3 w-3" /> Public (60/h)
              </span>
            )}
          </div>

          {/* Source badge */}
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/30 px-3 py-1.5 text-xs font-medium text-emerald-300 hover:bg-emerald-600/30 transition-all"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Open-Weight AI</span>
          </a>
        </div>
      </div>
    </header>
  );
};
