export interface Project {
  id: string;
  name: string;
  root_path?: string;
  default_branch?: string;
  raw_config?: string;
  updated_at?: string;
}

export interface Conversation {
  id: string;
  project_id?: string;
  project_name?: string;
  title: string;
  model: string;
  total_steps: number;
  created_at: string;
  updated_at: string;
  steps?: Step[];
  episodes?: Episode[];
  artifacts?: Artifact[];
}

export interface Episode {
  id: string;
  conversation_id: string;
  project_id?: string;
  project_name?: string;
  episode_index: number;
  title: string;
  intent: string;
  attempts_summary: string;
  resolution: string;
  outcome: 'SUCCESS' | 'FAILURE' | 'USER_CORRECTED' | 'IN_PROGRESS';
  outcome_score: number;
  start_step_index: number;
  end_step_index: number;
  commands_run: string[];
  files_touched: string[];
  score?: number;
  created_at: string;
}

export interface Step {
  id: string;
  conversation_id: string;
  step_index: number;
  source: string;
  type: string;
  status: string;
  thinking: string;
  content: string;
  created_at: string;
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  id: number;
  step_id: string;
  conversation_id: string;
  tool_name: string;
  tool_action: string;
  tool_summary: string;
  arguments_json: string;
  output: string;
  exit_code: number;
  created_at: string;
}

export interface Artifact {
  id: string;
  conversation_id: string;
  project_id?: string;
  file_path: string;
  file_name: string;
  artifact_type: string;
  content: string;
  summary: string;
  created_at: string;
}

export interface Rule {
  id: string;
  title: string;
  project_id?: string;
  project_name?: string;
  conversation_id?: string;
  rule_type: string;
  content: string;
  created_at: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  instructions: string;
  trigger_pattern: string;
  source_sessions: string;
  status: 'draft' | 'installed' | 'ignored';
  installed_path?: string;
  created_at: string;
  updated_at: string;
}

export interface ADR {
  id: string;
  title: string;
  project_id?: string;
  project_name?: string;
  conversation_id?: string;
  status: string;
  context: string;
  decision: string;
  consequences: string;
  raw_markdown: string;
  created_at: string;
}

export interface SystemStats {
  projects_count: number;
  conversations_count: number;
  episodes_count: number;
  successful_episodes: number;
  steps_count: number;
  tools_count: number;
  rules_count: number;
  adrs_count: number;
  skills_count: number;
}
