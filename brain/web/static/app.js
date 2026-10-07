// Project Brain - Modern Minimalist Frontend Engine

const store = new Map();
let currentTab = 'overview';
let activeSessionId = null;

// Clean SVG Icon Sprites
const ICONS = {
  copy: `<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`,
  check: `<svg class="w-3.5 h-3.5 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  terminal: `<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>`,
  chevronDown: `<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`,
  chevronRight: `<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`,
  alertCircle: `<svg class="w-4 h-4 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
};

// Clipboard Handler
function copySnippet(text, label, btnEl) {
  if (!text) return;
  navigator.clipboard.writeText(text);
  const toast = document.getElementById('copy-toast');
  const toastMsg = document.getElementById('copy-toast-msg');
  toastMsg.innerText = `Copied ${label || 'content'}`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 2200);

  if (btnEl) {
    const original = btnEl.innerHTML;
    btnEl.innerHTML = `${ICONS.check} <span class="text-emerald-500 font-medium">Copied</span>`;
    setTimeout(() => { btnEl.innerHTML = original; }, 1800);
  }
}

// Global Event Delegation for Copy Buttons
document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-copy-key]');
  if (btn) {
    const key = btn.getAttribute('data-copy-key');
    const label = btn.getAttribute('data-copy-label') || 'Content';
    const val = store.get(key) || '';
    copySnippet(val, label, btn);
    return;
  }
  const rawBtn = e.target.closest('[data-copy-btn]');
  if (rawBtn) {
    const val = rawBtn.getAttribute('data-copy-btn');
    const label = rawBtn.getAttribute('data-copy-label') || 'Content';
    copySnippet(val, label, rawBtn);
  }
});

// App Initialization
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initTabs();
  loadStats();
  loadProjects();
  loadConversations();
  loadRules();
  loadSkills();
  loadADRs();

  document.getElementById('rescan-btn').addEventListener('click', handleRescan);
  document.getElementById('memex-search-form').addEventListener('submit', handleMemexSearch);
  document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);
  document.getElementById('project-select').addEventListener('change', () => {
    loadConversations();
    loadRules();
    loadADRs();
  });
});

// Theme Management (Light / Dark)
function initTheme() {
  const saved = localStorage.getItem('pb_theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  applyTheme(theme);
}

function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
    document.documentElement.classList.remove('light');
  } else {
    document.documentElement.classList.remove('dark');
    document.documentElement.classList.add('light');
  }
  localStorage.setItem('pb_theme', theme);

  const sun = document.getElementById('theme-icon-sun');
  const moon = document.getElementById('theme-icon-moon');
  if (theme === 'dark') {
    sun.classList.remove('hidden');
    moon.classList.add('hidden');
  } else {
    sun.classList.add('hidden');
    moon.classList.remove('hidden');
  }
}

function toggleTheme() {
  const isDark = document.documentElement.classList.contains('dark');
  applyTheme(isDark ? 'light' : 'dark');
}

// Navigation Tabs
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('border-blue-600', 'dark:border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        b.classList.add('border-transparent', 'text-slate-500', 'dark:text-slate-400');
      });
      btn.classList.add('border-blue-600', 'dark:border-blue-500', 'text-blue-600', 'dark:text-blue-400');
      btn.classList.remove('border-transparent', 'text-slate-500', 'dark:text-slate-400');

      document.querySelectorAll('.tab-view').forEach(v => v.classList.add('hidden'));
      const activeView = document.getElementById(`view-${target}`);
      if (activeView) activeView.classList.remove('hidden');
      currentTab = target;
    });
  });
}

// Load System Metrics
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-episodes').innerText = data.episodes_count || 0;
    document.getElementById('stat-success').innerHTML = `${ICONS.check} <span>${data.successful_episodes || 0} verified resolutions</span>`;
    document.getElementById('stat-projects').innerText = data.projects_count || 0;
    document.getElementById('stat-rules').innerText = data.rules_count || 0;
    document.getElementById('stat-tools').innerText = data.tools_count || 0;
    document.getElementById('stat-steps').innerText = `${data.steps_count || 0} steps indexed`;

    updateBadge('rules-badge', data.rules_count);
    updateBadge('skills-badge', data.skills_count);
    updateBadge('adrs-badge', data.adrs_count);
  } catch (e) {
    console.error(e);
  }
}

function updateBadge(id, count) {
  const el = document.getElementById(id);
  if (!el) return;
  if (count && count > 0) {
    el.innerText = count;
    el.classList.remove('hidden');
  } else {
    el.classList.add('hidden');
  }
}

// Load Projects
async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) return;
    const projects = await res.json();
    const select = document.getElementById('project-select');
    select.innerHTML = '<option value="">All Projects</option>';
    projects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.innerText = p.name;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error(e);
  }
}

// Load Sessions List
async function loadConversations() {
  try {
    const pId = document.getElementById('project-select').value;
    const url = pId ? `/api/conversations?project_id=${pId}` : '/api/conversations';
    const res = await fetch(url);
    if (!res.ok) return;
    const convs = await res.json();

    const countBadge = document.getElementById('session-count-badge');
    if (countBadge) countBadge.innerText = convs.length;

    const list = document.getElementById('replayer-sessions-list');
    list.innerHTML = '';

    convs.forEach(c => {
      const btn = document.createElement('button');
      btn.className = `w-full text-left p-3 rounded-lg text-xs transition border ${
        activeSessionId === c.id
          ? 'bg-blue-50/60 dark:bg-slate-800 border-blue-500 dark:border-blue-500 text-slate-900 dark:text-slate-100 shadow-sm'
          : 'border-transparent hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-600 dark:text-slate-300'
      }`;
      btn.innerHTML = `
        <p class="font-medium truncate text-slate-900 dark:text-slate-100">${escapeHtml(c.title)}</p>
        <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 mt-1.5">
          <span class="truncate max-w-[130px] font-medium">${escapeHtml(c.project_name || 'Global')}</span>
          <span class="font-mono text-[10px] bg-slate-200/70 dark:bg-slate-700/60 px-1.5 py-0.2 rounded">${c.total_steps} steps</span>
        </div>
      `;
      btn.addEventListener('click', () => loadConversationDetails(c.id));
      list.appendChild(btn);
    });

    if (convs.length > 0 && !activeSessionId) {
      loadConversationDetails(convs[0].id);
    }
  } catch (e) {
    console.error(e);
  }
}

// Load Conversation Trajectory Playback
async function loadConversationDetails(id) {
  activeSessionId = id;
  const container = document.getElementById('replayer-content');
  container.innerHTML = `<div class="text-xs text-slate-400 flex items-center space-x-2">
    <span class="animate-spin-fast">${ICONS.terminal}</span>
    <span>Loading trajectory stream...</span>
  </div>`;

  try {
    const res = await fetch(`/api/conversations/${id}`);
    if (!res.ok) return;
    const conv = await res.json();

    let html = `
      <div class="border-b border-slate-200 dark:border-slate-800 pb-4 flex justify-between items-start">
        <div>
          <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(conv.title)}</h2>
          <div class="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
            <span>ID: <code class="font-mono text-blue-600 dark:text-blue-400">${conv.id.slice(0, 8)}</code></span>
            <span>Project: <strong class="text-slate-700 dark:text-slate-300">${escapeHtml(conv.project_name || 'Global')}</strong></span>
            <span>Model: <span class="text-slate-700 dark:text-slate-300">${escapeHtml(conv.model || 'Gemini')}</span></span>
          </div>
        </div>
        <span class="text-xs font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 px-2.5 py-1 rounded-md">
          ${conv.steps?.length || 0} Steps
        </span>
      </div>
      <div class="space-y-4">
    `;

    (conv.steps || []).forEach(step => {
      const isUser = step.type === 'USER_INPUT';
      html += `
        <div class="border rounded-xl p-4 text-xs transition-colors ${
          isUser
            ? 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/50'
            : 'bg-slate-50/60 dark:bg-slate-950/40 border-slate-200 dark:border-slate-800'
        }">
          <div class="flex justify-between items-center mb-2.5">
            <span class="font-medium px-2 py-0.5 rounded text-[11px] ${
              isUser
                ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
            }">
              Step ${step.step_index} · ${isUser ? 'User Prompt' : 'Agent Action'}
            </span>
            <span class="text-[11px] text-slate-400 font-mono">${step.created_at || ''}</span>
          </div>
      `;

      if (step.thinking) {
        html += `
          <div class="mb-3 bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-lg p-3">
            <details>
              <summary class="text-xs font-medium text-amber-800 dark:text-amber-300 cursor-pointer select-none">
                Internal Agent Reasoning (${step.thinking.length} chars)
              </summary>
              <div class="mt-2 text-xs text-slate-600 dark:text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                ${escapeHtml(cleanText(step.thinking))}
              </div>
            </details>
          </div>
        `;
      }

      if (step.content) {
        html += `<div class="prose prose-sm dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 leading-relaxed font-sans">${renderMarkdown(step.content)}</div>`;
      }

      if (step.tool_calls && step.tool_calls.length > 0) {
        html += `<div class="mt-3.5 space-y-2.5 border-t border-slate-200 dark:border-slate-800 pt-3">`;
        step.tool_calls.forEach(tc => {
          const argsKey = `tool_args_${tc.id}`;
          const outKey = `tool_out_${tc.id}`;
          store.set(argsKey, tc.arguments_json);
          if (tc.output) store.set(outKey, tc.output);

          html += `
            <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3 shadow-sm">
              <div class="flex justify-between items-center mb-1.5">
                <span class="font-mono font-semibold text-blue-600 dark:text-blue-400 text-xs flex items-center space-x-1.5">
                  ${ICONS.terminal}
                  <span>${escapeHtml(tc.tool_name)}</span>
                </span>
                ${tc.tool_summary ? `<span class="text-xs text-slate-500 dark:text-slate-400">${escapeHtml(tc.tool_summary)}</span>` : ''}
              </div>
              <div class="bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 p-3 rounded-md text-xs font-mono overflow-x-auto relative mt-1">
                <button data-copy-key="${argsKey}" data-copy-label="Arguments" class="absolute right-2 top-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] px-2 py-0.5 rounded flex items-center space-x-1 transition">
                  ${ICONS.copy} <span>Copy</span>
                </button>
                <p class="text-blue-400 text-[11px] font-semibold mb-1">Arguments:</p>
                <pre class="whitespace-pre-wrap">${escapeHtml(cleanText(tc.arguments_json))}</pre>
              </div>
          `;
          if (tc.output) {
            html += `
              <div class="mt-2 bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 p-3 rounded-md text-xs font-mono overflow-x-auto relative">
                <button data-copy-key="${outKey}" data-copy-label="Output" class="absolute right-2 top-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] px-2 py-0.5 rounded flex items-center space-x-1 transition">
                  ${ICONS.copy} <span>Copy</span>
                </button>
                <p class="text-amber-400 text-[11px] font-semibold mb-1">Output:</p>
                <pre class="whitespace-pre-wrap max-h-40 overflow-y-auto">${escapeHtml(cleanText(tc.output))}</pre>
              </div>
            `;
          }
          html += `</div>`;
        });
        html += `</div>`;
      }

      html += `</div>`;
    });

    html += `</div>`;
    container.innerHTML = html;
  } catch (e) {
    console.error(e);
  }
}

// Memex Search View
async function handleMemexSearch(e) {
  e.preventDefault();
  const q = document.getElementById('memex-query-input').value.trim();
  if (!q) return;

  const container = document.getElementById('memex-results');
  container.innerHTML = `<div class="text-xs text-slate-400 flex items-center space-x-2">
    <span class="animate-spin-fast">${ICONS.terminal}</span>
    <span>Querying dual FTS5 index...</span>
  </div>`;

  try {
    const pId = document.getElementById('project-select').value;
    const url = `/api/search?q=${encodeURIComponent(q)}${pId ? `&project_id=${pId}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const results = await res.json();

    if (results.length === 0) {
      container.innerHTML = `<div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center text-sm text-slate-500 dark:text-slate-400">
        No episodes matching "${escapeHtml(q)}".
      </div>`;
      return;
    }

    let html = '';
    results.forEach((ep, idx) => {
      const isSuccess = ep.outcome === 'SUCCESS';
      const cmdKey = `memex_cmd_${idx}`;
      if (ep.commands_run && ep.commands_run.length > 0) {
        store.set(cmdKey, ep.commands_run.join('\n'));
      }

      html += `
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-3 shadow-sm">
          <div class="flex justify-between items-start">
            <div>
              <div class="flex items-center space-x-2.5">
                <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                  isSuccess
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                    : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
                }">
                  ${ep.outcome}
                </span>
                <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(ep.title)}</h3>
              </div>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                Session: <span class="text-blue-600 dark:text-blue-400">${ep.conversation_id.slice(0, 8)}</span> [Steps ${ep.start_step_index}-${ep.end_step_index}] · Match Score: ${ep.score}
              </p>
            </div>
          </div>
      `;

      if (ep.commands_run && ep.commands_run.length > 0) {
        html += `
          <div class="bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 border border-slate-800 rounded-lg p-3 text-xs font-mono relative">
            <button data-copy-key="${cmdKey}" data-copy-label="Commands" class="absolute right-2.5 top-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-2 py-0.5 rounded flex items-center space-x-1 transition">
              ${ICONS.copy} <span>Copy</span>
            </button>
            <p class="text-emerald-400 font-semibold text-xs mb-1"># Verified Resolution Commands:</p>
            ${ep.commands_run.map(cmd => `<p class="text-slate-300 leading-relaxed">$ ${escapeHtml(cleanText(cmd))}</p>`).join('')}
          </div>
        `;
      }

      html += `
          <div class="text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950/60 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800/80 leading-relaxed font-sans">
            <span class="font-semibold text-slate-900 dark:text-slate-100">Summary: </span>${renderMarkdown(ep.resolution)}
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (e) {
    console.error(e);
  }
}

// Distilled Rules View
async function loadRules() {
  try {
    const pId = document.getElementById('project-select').value;
    const url = pId ? `/api/rules?project_id=${pId}` : '/api/rules';
    const res = await fetch(url);
    if (!res.ok) return;
    const rules = await res.json();
    const grid = document.getElementById('rules-grid');
    grid.innerHTML = '';

    rules.forEach((r, idx) => {
      const copyKey = `rule_raw_${idx}`;
      store.set(copyKey, r.content);

      // Parse the rule content cleanly into structured components
      const parsed = parseRuleContent(r.content);

      const card = document.createElement('div');
      card.className = 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col justify-between shadow-sm space-y-4';
      card.innerHTML = `
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-xs font-medium bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60 px-2.5 py-0.5 rounded-md uppercase tracking-wider">
              ${escapeHtml(r.rule_type || 'Negative Constraint')}
            </span>
            <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">${escapeHtml(r.project_name || 'Global')}</span>
          </div>

          <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(parsed.title || r.title)}</h3>

          <!-- Clean Directive Callout Box -->
          <div class="bg-blue-50/60 dark:bg-blue-950/30 border-l-4 border-blue-600 dark:border-blue-500 p-3.5 rounded-r-lg text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
            ${renderMarkdown(parsed.directive)}
          </div>

          ${parsed.guidance ? `
            <div class="text-xs text-slate-600 dark:text-slate-400 space-y-1.5 pt-1 leading-relaxed">
              ${renderMarkdown(parsed.guidance)}
            </div>
          ` : ''}
        </div>

        <button data-copy-key="${copyKey}" data-copy-label="Rule Markdown" class="w-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-medium py-2 rounded-lg text-slate-800 dark:text-slate-200 transition flex items-center justify-center space-x-1.5 shadow-sm">
          ${ICONS.copy}
          <span>Copy Rule Markdown</span>
        </button>
      `;
      grid.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

// Candidate Skills View
async function loadSkills() {
  try {
    const res = await fetch('/api/skills');
    if (!res.ok) return;
    const skills = await res.json();
    const list = document.getElementById('skills-list');
    list.innerHTML = '';

    skills.forEach((s, idx) => {
      const copyKey = `skill_raw_${idx}`;
      store.set(copyKey, s.instructions);

      // Parse commands and content from the instructions
      const parsed = parseSkillInstructions(s.instructions);

      const card = document.createElement('div');
      card.className = 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-4 shadow-sm';
      card.innerHTML = `
        <div class="flex justify-between items-start">
          <div>
            <div class="flex items-center space-x-2.5">
              <span class="text-xs font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800/80 px-2.5 py-0.5 rounded-md tracking-wider">
                DRAFT CANDIDATE
              </span>
              <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100 font-mono">${escapeHtml(s.name)}</h3>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${escapeHtml(s.description)}</p>
          </div>
          <button data-copy-key="${copyKey}" data-copy-label="SKILL.md" class="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg text-slate-800 dark:text-slate-200 transition flex items-center space-x-1.5 shadow-sm">
            ${ICONS.copy} <span>Copy SKILL.md</span>
          </button>
        </div>

        <!-- Human Review Alert -->
        <div class="bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 p-3 rounded-lg text-xs text-amber-900 dark:text-amber-200 flex items-start space-x-2">
          ${ICONS.alertCircle}
          <span><strong>Human Review Required:</strong> Auto-extracted from multi-step recipes. Review the command patterns below before saving to active skills.</span>
        </div>

        <!-- Commands Section -->
        ${parsed.commands && parsed.commands.length > 0 ? `
          <div class="bg-slate-900 text-slate-200 dark:bg-black dark:text-slate-300 border border-slate-800 rounded-lg p-3 text-xs font-mono space-y-1">
            <p class="text-blue-400 font-semibold text-xs mb-1.5"># Recommended Command Patterns:</p>
            ${parsed.commands.map(c => `<p class="leading-relaxed">$ ${escapeHtml(cleanText(c))}</p>`).join('')}
          </div>
        ` : ''}

        <!-- Best Practices / Guidelines -->
        ${parsed.guidelines ? `
          <div class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans">
            ${renderMarkdown(parsed.guidelines)}
          </div>
        ` : ''}
      `;
      list.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

// ADR Hub View
async function loadADRs() {
  try {
    const pId = document.getElementById('project-select').value;
    const url = pId ? `/api/adrs?project_id=${pId}` : '/api/adrs';
    const res = await fetch(url);
    if (!res.ok) return;
    const adrs = await res.json();
    const list = document.getElementById('adrs-list');
    list.innerHTML = '';

    adrs.forEach((adr, idx) => {
      const copyKey = `adr_raw_${idx}`;
      store.set(copyKey, adr.raw_markdown);

      const card = document.createElement('div');
      card.className = 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-4 shadow-sm';
      card.innerHTML = `
        <div class="flex justify-between items-start">
          <div class="flex items-center space-x-2.5">
            <span class="text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-2.5 py-0.5 rounded-md tracking-wider">
              ACCEPTED
            </span>
            <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(adr.title)}</h3>
          </div>
          <button data-copy-key="${copyKey}" data-copy-label="ADR.md" class="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg text-slate-800 dark:text-slate-200 transition flex items-center space-x-1.5 shadow-sm">
            ${ICONS.copy} <span>Copy ADR.md</span>
          </button>
        </div>

        <div class="space-y-3 pt-1">
          ${adr.context && adr.context.trim() ? `
            <div class="space-y-1">
              <span class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 tracking-wider">Context & Problem</span>
              <div class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-slate-50 dark:bg-slate-950/60 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                ${renderMarkdown(adr.context)}
              </div>
            </div>
          ` : ''}

          ${adr.decision && adr.decision.trim() ? `
            <div class="space-y-1">
              <span class="text-xs font-semibold uppercase text-blue-600 dark:text-blue-400 tracking-wider">Decision Outcome</span>
              <div class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-blue-50/50 dark:bg-blue-950/20 p-3.5 rounded-lg border border-blue-200 dark:border-blue-900/50">
                ${renderMarkdown(adr.decision)}
              </div>
            </div>
          ` : ''}

          ${adr.consequences && adr.consequences.trim() ? `
            <div class="space-y-1">
              <span class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 tracking-wider">Verification & Results</span>
              <div class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-slate-50 dark:bg-slate-950/60 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 font-mono text-xs">
                ${renderMarkdown(adr.consequences)}
              </div>
            </div>
          ` : ''}
        </div>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

// Rescan Pipeline Trigger
async function handleRescan() {
  const label = document.getElementById('rescan-label');
  const icon = document.getElementById('rescan-icon');
  label.innerText = 'Syncing...';
  icon.classList.add('animate-spin-fast');
  try {
    await fetch('/api/scan', { method: 'POST' });
    await fetch('/api/distill-rules', { method: 'POST' });
    await fetch('/api/mine-skills', { method: 'POST' });
    await loadStats();
    await loadConversations();
    await loadRules();
    await loadSkills();
    await loadADRs();
  } finally {
    label.innerText = 'Sync';
    icon.classList.remove('animate-spin-fast');
  }
}

// Helper: Clean raw escaped text
function cleanText(str) {
  if (!str) return '';
  return String(str)
    .replace(/\\n/g, '\n')
    .replace(/\\r/g, '')
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\?\$?\\rightarrow\\?\$?/g, '→');
}

// Helper: Clean Markdown Parser
function renderMarkdown(str) {
  if (!str) return '';
  const cleaned = cleanText(str);
  if (window.marked && typeof window.marked.parse === 'function') {
    return window.marked.parse(cleaned);
  }
  // Fallback: format bold, code, paragraphs
  let out = escapeHtml(cleaned);
  out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/`([^`]+)`/g, '<code class="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono text-xs">$1</code>');
  out = out.replace(/\n\n/g, '<br><br>');
  return out;
}

// Helper: Extract structured fields from a Rule markdown string
function parseRuleContent(raw) {
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
    // Look for blockquote
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

// Helper: Extract structured fields from a Skill instruction string
function parseSkillInstructions(raw) {
  const text = cleanText(raw);
  const commands = [];

  // Match commands inside code blocks
  const codeMatches = text.matchAll(/```bash\s*\n([\s\S]*?)```/g);
  for (const m of codeMatches) {
    const lines = m[1].trim().split('\n');
    lines.forEach(l => {
      if (l.trim()) commands.push(l.trim());
    });
  }

  // Extract guidelines after Best Practices
  let guidelines = '';
  const guideMatch = text.match(/## (?:Best Practices|Guidelines)\s*\n+([\s\S]+)/i);
  if (guideMatch) {
    guidelines = guideMatch[1].trim();
  }

  return { commands, guidelines };
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
