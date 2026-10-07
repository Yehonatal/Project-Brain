import React, { useState, useEffect } from 'react';
import { Project, Conversation, Episode, Rule, Skill, ADR, SystemStats } from './types';

// Crisp Vector SVG Icons
const Icons = {
  logo: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.5V11a2 2 0 0 0 2 2h1.5a3.5 3.5 0 1 1 0 7H16a2 2 0 0 0-2 2v.5a1.5 1.5 0 0 1-3 0V22a2 2 0 0 0-2-2H6.5a3.5 3.5 0 0 1 0-7H8a2 2 0 0 0 2-2V9.5C8.8 8.8 8 7.5 8 6a4 4 0 0 1 4-4z"/>
    </svg>
  ),
  overview: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect>
    </svg>
  ),
  terminal: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line>
    </svg>
  ),
  search: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>
  ),
  shield: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    </svg>
  ),
  wrench: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
    </svg>
  ),
  book: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
    </svg>
  ),
  copy: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
  ),
  check: (
    <svg className="w-3.5 h-3.5 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  ),
  sun: (
    <svg className="w-4 h-4 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    </svg>
  ),
  moon: (
    <svg className="w-4 h-4 text-slate-700 dark:text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>
  ),
  refresh: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
    </svg>
  ),
  alertCircle: (
    <svg className="w-4 h-4 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>
    </svg>
  ),
};

// Clean text formatting helpers
function cleanText(str: string): string {
  if (!str) return '';
  return String(str)
    .replace(/\\n/g, '\n')
    .replace(/\\r/g, '')
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\?\$?\\rightarrow\\?\$?/g, '→');
}

function parseRuleContent(raw: string) {
  const text = cleanText(raw);
  let title = '';
  let directive = '';
  let guidance = '';

  const titleMatch = text.match(/#\s+(.+)/);
  if (titleMatch) title = titleMatch[1].replace(/^Guideline:\s*/i, '');

  const directiveMatch = text.match(/## Directive\s*\n+>\s*([^\n#]+(?:\n>[^\n#]+)*)/i);
  if (directiveMatch) {
    directive = directiveMatch[1].replace(/^>\s*/gm, '').trim();
  } else {
    const quoteMatch = text.match(/>\s*([^\n#]+)/);
    if (quoteMatch) directive = quoteMatch[1].trim();
  }

  const guidanceMatch = text.match(/## Practical Guidance\s*\n+([\s\S]+)/i);
  if (guidanceMatch) {
    guidance = guidanceMatch[1].trim();
  }

  if (!directive) directive = text;
  return { title, directive, guidance };
}

function parseSkillInstructions(raw: string) {
  const text = cleanText(raw);
  const commands: string[] = [];
  const codeMatches = text.matchAll(/```bash\s*\n([\s\S]*?)```/g);
  for (const m of codeMatches) {
    const lines = m[1].trim().split('\n');
    lines.forEach((l) => {
      if (l.trim()) commands.push(l.trim());
    });
  }

  let guidelines = '';
  const guideMatch = text.match(/## (?:Best Practices|Guidelines)\s*\n+([\s\S]+)/i);
  if (guideMatch) {
    guidelines = guideMatch[1].trim();
  }

  return { commands, guidelines };
}

export function App() {
  const [tab, setTab] = useState<'overview' | 'replayer' | 'memex' | 'rules' | 'skills' | 'adrs'>('overview');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string>('');
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({});

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Episode[]>([]);

  const [rules, setRules] = useState<Rule[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [adrs, setAdrs] = useState<ADR[]>([]);

  const [copyNotice, setCopyNotice] = useState<string>('');
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    }
  }, [theme]);

  useEffect(() => {
    fetchStats();
    fetchProjects();
    fetchConversations();
    fetchRules();
    fetchSkills();
    fetchADRs();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats');
      if (res.ok) setStats(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchProjects = async () => {
    try {
      const res = await fetch('/api/projects');
      if (res.ok) setProjects(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchConversations = async () => {
    try {
      const pId = selectedProject ? `?project_id=${selectedProject}` : '';
      const res = await fetch(`/api/conversations${pId}`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
        if (data.length > 0 && !selectedConvId) {
          loadConversation(data[0].id);
        }
      }
    } catch (e) { console.error(e); }
  };

  const loadConversation = async (id: string) => {
    setSelectedConvId(id);
    try {
      const res = await fetch(`/api/conversations/${id}`);
      if (res.ok) setActiveConv(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchRules = async () => {
    try {
      const pId = selectedProject ? `?project_id=${selectedProject}` : '';
      const res = await fetch(`/api/rules${pId}`);
      if (res.ok) setRules(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchSkills = async () => {
    try {
      const res = await fetch('/api/skills');
      if (res.ok) setSkills(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchADRs = async () => {
    try {
      const pId = selectedProject ? `?project_id=${selectedProject}` : '';
      const res = await fetch(`/api/adrs${pId}`);
      if (res.ok) setAdrs(await res.json());
    } catch (e) { console.error(e); }
  };

  const triggerScan = async () => {
    setScanning(true);
    try {
      await fetch('/api/scan', { method: 'POST' });
      await fetch('/api/distill-rules', { method: 'POST' });
      await fetch('/api/mine-skills', { method: 'POST' });
      await fetchStats();
      await fetchConversations();
      await fetchRules();
      await fetchSkills();
      await fetchADRs();
    } finally {
      setScanning(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      const pParam = selectedProject ? `&project_id=${selectedProject}` : '';
      const res = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}${pParam}`);
      if (res.ok) setSearchResults(await res.json());
    } catch (e) { console.error(e); }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopyNotice(`Copied ${label}`);
    setTimeout(() => setCopyNotice(''), 2200);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-150">
      {/* Top Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 py-3.5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 dark:bg-blue-500 text-white flex items-center justify-center shadow-sm">
            {Icons.logo}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100">Project Brain</h1>
              <span className="text-[10px] font-medium tracking-wide uppercase px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60">
                Local Core
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Autonomous Agent Intelligence & Memory Platform</p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center space-x-3">
          {copyNotice && (
            <div className="text-xs bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-3 py-1 rounded-full flex items-center space-x-1.5 shadow-sm">
              {Icons.check}
              <span>{copyNotice}</span>
            </div>
          )}

          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg pl-3 pr-8 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Projects ({projects.length})</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <button
            onClick={triggerScan}
            disabled={scanning}
            className="flex items-center space-x-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg transition text-slate-700 dark:text-slate-200 shadow-sm"
          >
            <span className={scanning ? 'animate-spin' : ''}>{Icons.refresh}</span>
            <span>{scanning ? 'Syncing...' : 'Sync'}</span>
          </button>

          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Toggle Light / Dark Mode"
            className="p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition shadow-sm"
          >
            {theme === 'dark' ? Icons.sun : Icons.moon}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 flex space-x-4">
        {[
          { id: 'overview', label: 'Overview', icon: Icons.overview },
          { id: 'replayer', label: 'Trajectory Replayer', icon: Icons.terminal },
          { id: 'memex', label: 'Memex Search', icon: Icons.search },
          { id: 'rules', label: 'Distilled Rules', icon: Icons.shield, count: stats?.rules_count },
          { id: 'skills', label: 'Candidate Skills', icon: Icons.wrench, count: stats?.skills_count },
          { id: 'adrs', label: 'ADR Hub', icon: Icons.book, count: stats?.adrs_count },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as any)}
            className={`py-3 px-3 text-xs font-medium border-b-2 flex items-center space-x-2 transition ${
              tab === t.id
                ? 'border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <span>{t.icon}</span>
            <span>{t.label}</span>
            {t.count !== undefined && t.count > 0 && (
              <span className="ml-1.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 text-[10px] font-semibold px-1.5 py-0.2 rounded-full">
                {t.count}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* View Container */}
      <main className="flex-1 p-6 overflow-y-auto">
        {/* OVERVIEW */}
        {tab === 'overview' && stats && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-xl shadow-sm">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Problem Episodes</span>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">{stats.episodes_count}</p>
                <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 flex items-center space-x-1">
                  {Icons.check}
                  <span>{stats.successful_episodes} verified resolutions</span>
                </p>
              </div>

              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-xl shadow-sm">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Projects</span>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">{stats.projects_count}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">From ~/.gemini config</p>
              </div>

              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-xl shadow-sm">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Distilled Rules</span>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">{stats.rules_count}</p>
                <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">From user feedback & fixes</p>
              </div>

              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-xl shadow-sm">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Tool Invocations</span>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">{stats.tools_count}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{stats.steps_count} steps indexed</p>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Model Context Protocol (MCP) Integration</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Register Project Brain as a local stdio MCP server in Antigravity or Gemini CLI to provide agents with pre-flight repository intelligence.
              </p>

              <div className="bg-slate-900 text-slate-100 dark:bg-black dark:text-slate-200 border border-slate-800 rounded-lg p-4 font-mono text-xs relative">
                <button
                  onClick={() => copyToClipboard('python3 -m brain.cli mcp', 'MCP Command')}
                  className="absolute right-3 top-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-2.5 py-1 rounded flex items-center space-x-1.5 transition"
                >
                  {Icons.copy} <span>Copy</span>
                </button>
                <p className="text-blue-400 mb-1.5"># Command for ~/.gemini/antigravity/mcp_servers.json</p>
                <p className="text-emerald-400 font-semibold text-sm">python3 -m brain.cli mcp</p>
              </div>
            </div>
          </div>
        )}

        {/* REPLAYER */}
        {tab === 'replayer' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
            <div className="lg:col-span-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 h-[780px] flex flex-col shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Sessions</span>
                <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded-full font-mono">{conversations.length}</span>
              </div>
              <div className="overflow-y-auto space-y-2 flex-1 pr-1 mt-3">
                {conversations.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => loadConversation(c.id)}
                    className={`w-full text-left p-3 rounded-lg text-xs transition border ${
                      selectedConvId === c.id
                        ? 'bg-blue-50/60 dark:bg-slate-800 border-blue-500 text-slate-900 dark:text-slate-100 shadow-sm'
                        : 'border-transparent hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    <p className="font-medium truncate text-slate-900 dark:text-slate-100">{c.title}</p>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 mt-1.5">
                      <span className="truncate max-w-[130px] font-medium">{c.project_name || 'Global'}</span>
                      <span className="font-mono text-[10px] bg-slate-200/70 dark:bg-slate-700/60 px-1.5 py-0.2 rounded">{c.total_steps} steps</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="lg:col-span-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 h-[780px] overflow-y-auto space-y-6 shadow-sm">
              {activeConv ? (
                <>
                  <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex justify-between items-start">
                    <div>
                      <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{activeConv.title}</h2>
                      <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                        <span>ID: <code className="font-mono text-blue-600 dark:text-blue-400">{activeConv.id.slice(0, 8)}</code></span>
                        <span>Project: <strong className="text-slate-700 dark:text-slate-300">{activeConv.project_name || 'Global'}</strong></span>
                        <span>Model: <span className="text-slate-700 dark:text-slate-300">{activeConv.model}</span></span>
                      </div>
                    </div>
                    <span className="text-xs font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 px-2.5 py-1 rounded-md">
                      {activeConv.steps?.length || 0} Steps
                    </span>
                  </div>

                  <div className="space-y-4">
                    {activeConv.steps?.map((step) => (
                      <div
                        key={step.id}
                        className={`border rounded-xl p-4 text-xs transition-colors ${
                          step.type === 'USER_INPUT'
                            ? 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/50'
                            : 'bg-slate-50/60 dark:bg-slate-950/40 border-slate-200 dark:border-slate-800'
                        }`}
                      >
                        <div className="flex justify-between items-center mb-2.5">
                          <span className={`font-medium px-2 py-0.5 rounded text-[11px] ${
                            step.type === 'USER_INPUT'
                              ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
                          }`}>
                            Step {step.step_index} · {step.type === 'USER_INPUT' ? 'User Prompt' : 'Agent Action'}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">{step.created_at}</span>
                        </div>

                        {step.thinking && (
                          <div className="mb-3 bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-lg p-3">
                            <button
                              onClick={() => setExpandedThinking((prev) => ({ ...prev, [step.id]: !prev[step.id] }))}
                              className="text-xs font-medium text-amber-800 dark:text-amber-300 cursor-pointer select-none flex items-center space-x-1"
                            >
                              <span>Internal Agent Reasoning ({step.thinking.length} chars)</span>
                            </button>
                            {expandedThinking[step.id] && (
                              <p className="mt-2 text-xs text-slate-600 dark:text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                                {cleanText(step.thinking)}
                              </p>
                            )}
                          </div>
                        )}

                        {step.content && (
                          <div className="whitespace-pre-wrap leading-relaxed text-slate-800 dark:text-slate-200 font-sans text-xs">
                            {cleanText(step.content)}
                          </div>
                        )}

                        {step.tool_calls && step.tool_calls.length > 0 && (
                          <div className="mt-3.5 space-y-2.5 border-t border-slate-200 dark:border-slate-800 pt-3">
                            {step.tool_calls.map((tc) => (
                              <div key={tc.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3 shadow-sm">
                                <div className="flex justify-between items-center mb-1.5">
                                  <span className="font-mono font-semibold text-blue-600 dark:text-blue-400 text-xs flex items-center space-x-1.5">
                                    {Icons.terminal}
                                    <span>{tc.tool_name}</span>
                                  </span>
                                  {tc.tool_summary && <span className="text-xs text-slate-500 dark:text-slate-400">{tc.tool_summary}</span>}
                                </div>
                                <div className="bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 p-3 rounded-md text-xs font-mono overflow-x-auto relative mt-1">
                                  <button
                                    onClick={() => copyToClipboard(tc.arguments_json, 'Arguments')}
                                    className="absolute right-2 top-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] px-2 py-0.5 rounded flex items-center space-x-1 transition"
                                  >
                                    {Icons.copy} <span>Copy</span>
                                  </button>
                                  <p className="text-blue-400 text-[11px] font-semibold mb-1">Arguments:</p>
                                  <pre className="whitespace-pre-wrap">{cleanText(tc.arguments_json)}</pre>
                                </div>

                                {tc.output && (
                                  <div className="mt-2 bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 p-3 rounded-md text-xs font-mono overflow-x-auto relative">
                                    <button
                                      onClick={() => copyToClipboard(tc.output, 'Output')}
                                      className="absolute right-2 top-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] px-2 py-0.5 rounded flex items-center space-x-1 transition"
                                    >
                                      {Icons.copy} <span>Copy</span>
                                    </button>
                                    <p className="text-amber-400 text-[11px] font-semibold mb-1">Output:</p>
                                    <pre className="whitespace-pre-wrap max-h-40 overflow-y-auto">{cleanText(tc.output)}</pre>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  Select a session from the list to view trajectory playback
                </div>
              )}
            </div>
          </div>
        )}

        {/* MEMEX SEARCH */}
        {tab === 'memex' && (
          <div className="max-w-5xl mx-auto space-y-6">
            <form onSubmit={handleSearch} className="flex space-x-3">
              <input
                type="text"
                placeholder="Search past solutions, errors, identifiers, or commands..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-6 py-3 rounded-xl transition shadow-sm"
              >
                Search
              </button>
            </form>

            <div className="space-y-4">
              {searchResults.map((ep) => (
                <div key={ep.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-3 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2.5">
                        <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                          ep.outcome === 'SUCCESS'
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                            : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
                        }`}>
                          {ep.outcome}
                        </span>
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{ep.title}</h3>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                        Session: <span className="text-blue-600 dark:text-blue-400">{ep.conversation_id.slice(0, 8)}</span> [Steps {ep.start_step_index}-{ep.end_step_index}] · Match Score: {ep.score}
                      </p>
                    </div>
                  </div>

                  {ep.commands_run && ep.commands_run.length > 0 && (
                    <div className="bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 border border-slate-800 rounded-lg p-3 text-xs font-mono relative">
                      <button
                        onClick={() => copyToClipboard(ep.commands_run.join('\n'), 'Commands')}
                        className="absolute right-2.5 top-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-2 py-0.5 rounded flex items-center space-x-1 transition"
                      >
                        {Icons.copy} <span>Copy</span>
                      </button>
                      <p className="text-emerald-400 font-semibold text-xs mb-1"># Verified Resolution Commands:</p>
                      {ep.commands_run.map((cmd, idx) => (
                        <p key={idx} className="text-slate-300 leading-relaxed">$ {cleanText(cmd)}</p>
                      ))}
                    </div>
                  )}

                  <div className="text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950/60 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800/80 leading-relaxed">
                    <span className="font-semibold text-slate-900 dark:text-slate-100">Summary: </span>
                    {cleanText(ep.resolution)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* RULES */}
        {tab === 'rules' && (
          <div className="max-w-5xl mx-auto space-y-5">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Distilled Developer Rules</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Synthesized automatically from developer feedback, negative constraints, and course-corrections.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {rules.map((r) => {
                const parsed = parseRuleContent(r.content);
                return (
                  <div key={r.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col justify-between shadow-sm space-y-4">
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-medium bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60 px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                          {r.rule_type || 'Negative Constraint'}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">{r.project_name || 'Global'}</span>
                      </div>

                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{parsed.title || r.title}</h3>

                      <div className="bg-blue-50/60 dark:bg-blue-950/30 border-l-4 border-blue-600 dark:border-blue-500 p-3.5 rounded-r-lg text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
                        {parsed.directive}
                      </div>

                      {parsed.guidance && (
                        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1 pt-1 leading-relaxed whitespace-pre-wrap font-sans">
                          {parsed.guidance}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => copyToClipboard(r.content, 'Rule Markdown')}
                      className="w-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-medium py-2 rounded-lg text-slate-800 dark:text-slate-200 transition flex items-center justify-center space-x-1.5 shadow-sm"
                    >
                      {Icons.copy}
                      <span>Copy Rule Markdown</span>
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* SKILLS */}
        {tab === 'skills' && (
          <div className="max-w-5xl mx-auto space-y-5">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Candidate Draft Skills</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Mined from multi-step tool recipes and error resolutions across sessions. Drafts require human review before installation.</p>
            </div>

            <div className="space-y-5">
              {skills.map((s) => {
                const parsed = parseSkillInstructions(s.instructions);
                return (
                  <div key={s.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center space-x-2.5">
                          <span className="text-xs font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800/80 px-2.5 py-0.5 rounded-md tracking-wider">
                            DRAFT CANDIDATE
                          </span>
                          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 font-mono">{s.name}</h3>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{s.description}</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(s.instructions, 'SKILL.md')}
                        className="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg text-slate-800 dark:text-slate-200 transition flex items-center space-x-1.5 shadow-sm"
                      >
                        {Icons.copy} <span>Copy SKILL.md</span>
                      </button>
                    </div>

                    <div className="bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 p-3 rounded-lg text-xs text-amber-900 dark:text-amber-200 flex items-start space-x-2">
                      {Icons.alertCircle}
                      <span><strong>Human Review Required:</strong> Auto-extracted from multi-step recipes. Review the command patterns below before saving to active skills.</span>
                    </div>

                    {parsed.commands && parsed.commands.length > 0 && (
                      <div className="bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 border border-slate-800 rounded-lg p-3 text-xs font-mono space-y-1">
                        <p className="text-blue-400 font-semibold text-xs mb-1.5"># Recommended Command Patterns:</p>
                        {parsed.commands.map((c, i) => (
                          <p key={i} className="leading-relaxed">$ {cleanText(c)}</p>
                        ))}
                      </div>
                    )}

                    {parsed.guidelines && (
                      <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                        {cleanText(parsed.guidelines)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ADR HUB */}
        {tab === 'adrs' && (
          <div className="max-w-5xl mx-auto space-y-5">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Architecture Decision Records (ADRs)</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Parsed and organized architectural records from implementation plans and walkthroughs.</p>
            </div>

            <div className="space-y-5">
              {adrs.map((adr) => (
                <div key={adr.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-2.5 py-0.5 rounded-md tracking-wider">
                        ACCEPTED
                      </span>
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{adr.title}</h3>
                    </div>
                    <button
                      onClick={() => copyToClipboard(adr.raw_markdown, 'ADR.md')}
                      className="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg text-slate-800 dark:text-slate-200 transition flex items-center space-x-1.5 shadow-sm"
                    >
                      {Icons.copy} <span>Copy ADR.md</span>
                    </button>
                  </div>

                  <div className="space-y-3 pt-1">
                    {adr.context && adr.context.trim() && (
                      <div className="space-y-1">
                        <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 tracking-wider">Context & Problem</span>
                        <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-slate-50 dark:bg-slate-950/60 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                          {cleanText(adr.context)}
                        </div>
                      </div>
                    )}

                    {adr.decision && adr.decision.trim() && (
                      <div className="space-y-1">
                        <span className="text-xs font-semibold uppercase text-blue-600 dark:text-blue-400 tracking-wider">Decision Outcome</span>
                        <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-blue-50/50 dark:bg-blue-950/20 p-3.5 rounded-lg border border-blue-200 dark:border-blue-900/50">
                          {cleanText(adr.decision)}
                        </div>
                      </div>
                    )}

                    {adr.consequences && adr.consequences.trim() && (
                      <div className="space-y-1">
                        <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 tracking-wider">Verification & Results</span>
                        <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-slate-50 dark:bg-slate-950/60 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 font-mono text-xs">
                          {cleanText(adr.consequences)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
