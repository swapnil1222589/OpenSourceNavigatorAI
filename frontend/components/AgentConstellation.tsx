'use client';

import React from 'react';
import {
  AgentMetadata,
  AgentRunStatus,
  AgentExecutionRecord,
} from '../lib/types';
import {
  Compass,
  FileSearch,
  FolderGit2,
  GraduationCap,
  ListTodo,
  CheckCircle2,
  GitPullRequest,
  Workflow,
  Clock,
} from 'lucide-react';

interface AgentConstellationProps {
  agents: AgentMetadata[];
  activeAgentId: string | null;
  onSelectAgent: (agentIdOrName: string) => void;
  executions: AgentExecutionRecord[];
  isWorkflowRunning: boolean;
}

export const AgentConstellation: React.FC<AgentConstellationProps> = ({
  agents,
  activeAgentId,
  onSelectAgent,
  executions,
  isWorkflowRunning,
}) => {
  // Map execution status by agent id and name
  const statusMap = new Map<string, { status: AgentRunStatus; duration?: number | null }>();
  (executions || []).forEach((e) => {
    if (e.agent_id) {
      statusMap.set(e.agent_id, { status: e.status, duration: e.duration_ms });
    }
    if (e.agent_name) {
      statusMap.set(e.agent_name, { status: e.status, duration: e.duration_ms });
    }
  });

  const getAgentIcon = (idOrName: string) => {
    const key = (idOrName || '').toLowerCase();
    if (key.includes('orchestrat')) return Workflow;
    if (key.includes('discovery')) return Compass;
    if (key.includes('understanding')) return FileSearch;
    if (key.includes('repo') || key.includes('context')) return FolderGit2;
    if (key.includes('skill')) return GraduationCap;
    if (key.includes('plan')) return ListTodo;
    if (key.includes('test')) return CheckCircle2;
    if (key.includes('pr') || key.includes('readiness')) return GitPullRequest;
    return Compass;
  };

  const centerX = 320;
  const centerY = 270;
  const radius = 190;

  const orchestrator =
    agents.find((a) => a.id === 'orchestrator' || a.name?.toLowerCase().includes('orchestrat')) ||
    agents[0];
  const specialistAgents = agents.filter((a) => a !== orchestrator);

  const nodes = specialistAgents.map((agent, i) => {
    const total = Math.max(1, specialistAgents.length);
    const angle = (i * 2 * Math.PI) / total - Math.PI / 2;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    return { agent, x, y };
  });

  return (
    <div className="relative w-full h-[580px] rounded-3xl border border-slate-800 bg-gradient-to-b from-slate-950 via-[#070b12] to-slate-950 overflow-hidden select-none shadow-inner flex items-center justify-center">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:32px_32px]" />

      {/* Ambient glow */}
      <div
        className={`absolute w-96 h-96 rounded-full blur-3xl pointer-events-none transition-all duration-700 ${
          isWorkflowRunning ? 'bg-emerald-500/15 animate-pulse' : 'bg-indigo-500/10'
        }`}
      />

      {/* SVG Connection Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="#1e293b"
          strokeWidth="1.5"
          strokeDasharray="4 6"
          className="opacity-70"
        />

        {nodes.map(({ agent, x, y }) => {
          const agentKey = agent.id || agent.name;
          const info = statusMap.get(agentKey) || (agent.id ? statusMap.get(agent.id) : undefined);
          const isSelected = activeAgentId === agentKey || (agent.id && activeAgentId === agent.id);
          const isRunning = info?.status === 'running';
          const isCompleted = info?.status === 'completed';

          return (
            <line
              key={agentKey}
              x1={centerX}
              y1={centerY}
              x2={x}
              y2={y}
              stroke={
                isRunning
                  ? '#f59e0b'
                  : isCompleted
                  ? '#10b981'
                  : isSelected
                  ? '#38bdf8'
                  : '#334155'
              }
              strokeWidth={isRunning || isSelected ? 2.5 : 1.2}
              strokeDasharray={isRunning ? '4 4' : 'none'}
              className={isRunning ? 'animate-pulse' : 'transition-colors duration-300'}
            />
          );
        })}
      </svg>

      {/* Center Orchestrator Node */}
      {orchestrator && (
        <div
          onClick={() => onSelectAgent(orchestrator.id || orchestrator.name)}
          style={{ left: `${centerX}px`, top: `${centerY}px` }}
          className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center justify-center p-3.5 rounded-2xl cursor-pointer transition-all duration-300 z-20 ${
            activeAgentId === (orchestrator.id || orchestrator.name) || activeAgentId === 'orchestrator'
              ? 'ring-2 ring-emerald-400 bg-slate-900 shadow-xl shadow-emerald-500/30 scale-105'
              : 'bg-slate-900/90 border border-slate-700 hover:border-emerald-500/60 shadow-lg'
          }`}
        >
          <div className="relative">
            <div
              className={`p-3 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white ${
                isWorkflowRunning ? 'animate-spin-slow' : ''
              }`}
            >
              <Workflow className="h-6 w-6" />
            </div>
            {isWorkflowRunning && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
              </span>
            )}
          </div>
          <span className="mt-2 text-xs font-bold text-white tracking-wide">
            {orchestrator.display_name || orchestrator.name || 'Orchestrator'}
          </span>
          <span className="text-[10px] text-emerald-400 font-mono">
            {isWorkflowRunning ? 'COORDINATING' : 'READY'}
          </span>
        </div>
      )}

      {/* Satellite Specialist Nodes */}
      {nodes.map(({ agent, x, y }) => {
        const agentKey = agent.id || agent.name;
        const Icon = getAgentIcon(agentKey);
        const info = statusMap.get(agentKey) || (agent.id ? statusMap.get(agent.id) : undefined);
        const isSelected = activeAgentId === agentKey || (agent.id && activeAgentId === agent.id);
        const status = info?.status || 'idle';

        let statusBorder = 'border-slate-800 bg-slate-900/90';
        let statusGlow = '';
        let badgeColor = 'bg-slate-800 text-slate-400';

        if (status === 'running') {
          statusBorder = 'border-amber-400 bg-slate-900 animate-pulse';
          statusGlow = 'shadow-lg shadow-amber-500/30 ring-2 ring-amber-400/50';
          badgeColor = 'bg-amber-500/20 text-amber-300 border border-amber-500/30';
        } else if (status === 'completed') {
          statusBorder = 'border-emerald-500 bg-slate-900';
          statusGlow = 'shadow-md shadow-emerald-500/20';
          badgeColor = 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        } else if (status === 'failed') {
          statusBorder = 'border-rose-500 bg-slate-900';
          statusGlow = 'shadow-md shadow-rose-500/20';
          badgeColor = 'bg-rose-500/20 text-rose-300 border border-rose-500/30';
        } else if (isSelected) {
          statusBorder = 'border-sky-400 bg-slate-900 ring-2 ring-sky-400/40';
        }

        return (
          <div
            key={agentKey}
            onClick={() => onSelectAgent(agentKey)}
            style={{ left: `${x}px`, top: `${y}px` }}
            className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center p-2.5 rounded-2xl cursor-pointer transition-all duration-200 z-10 w-36 text-center ${statusBorder} ${statusGlow} hover:scale-105`}
          >
            <div className="relative mb-1">
              <div
                className={`p-2 rounded-xl ${
                  status === 'running'
                    ? 'bg-amber-500/20 text-amber-300'
                    : status === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : status === 'failed'
                    ? 'bg-rose-500/20 text-rose-400'
                    : 'bg-slate-800 text-slate-300'
                }`}
              >
                <Icon className="h-4 w-4" />
              </div>

              {status === 'running' && (
                <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500" />
                </span>
              )}
            </div>

            <span className="text-[11px] font-semibold text-slate-100 truncate w-full px-1">
              {agent.display_name || agent.name}
            </span>

            <div className="mt-1 flex items-center justify-center gap-1 w-full">
              <span className={`text-[9px] uppercase font-mono px-1.5 py-0.2 rounded-md ${badgeColor}`}>
                {status}
              </span>
              {info?.duration && (
                <span className="text-[9px] text-slate-500 font-mono flex items-center gap-0.5">
                  <Clock className="h-2.5 w-2.5" />
                  {(info.duration / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          </div>
        );
      })}

      {/* Legend */}
      <div className="absolute bottom-3 left-4 flex items-center gap-3 text-[11px] font-mono text-slate-400 bg-slate-950/70 border border-slate-800 px-3 py-1.5 rounded-xl backdrop-blur-md">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-slate-600" /> Idle
        </span>
        <span className="flex items-center gap-1.5 text-amber-400">
          <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" /> Running
        </span>
        <span className="flex items-center gap-1.5 text-emerald-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400" /> Completed
        </span>
        <span className="flex items-center gap-1.5 text-rose-400">
          <span className="h-2 w-2 rounded-full bg-rose-400" /> Failed
        </span>
      </div>

      <div className="absolute top-3 right-4 text-[11px] text-slate-500 font-mono">
        Click any agent node to inspect typed I/O & details
      </div>
    </div>
  );
};
