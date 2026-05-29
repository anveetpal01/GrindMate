/** Shape of objects returned by the Django backend. Mirrors DRF serializers. */

export interface User {
  public_id: string;
  username: string;
  email: string;
  display_name: string;
  avatar_url: string;
  timezone: string;
  is_email_verified: boolean;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export interface LeetCodeAccount {
  handle: string;
  sync_status: "pending" | "ok" | "failed" | "unverified";
  is_verified: boolean;
  last_synced_at: string | null;
  last_sync_error: string;
  total_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  ranking: number | null;
  created_at: string;
  updated_at: string;
}

export interface SyncResult {
  new_solves: number;
  total_solved: number;
  problems_resolved: number;
  error: string | null;
  account: LeetCodeAccount;
}

export interface Problem {
  title_slug: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  topic_tags: string[];
  is_premium: boolean;
  leetcode_id: number | null;
}

export interface SubmissionLog {
  id: number;
  problem: Problem;
  solved_at: string;
  source: "auto" | "manual";
  created_at: string;
}

export interface Group {
  public_id: string;
  name: string;
  description: string;
  owner: number;
  member_count: number;
  role: "admin" | "member" | null;
  created_at: string;
  updated_at: string;
}

export interface GroupInvite {
  token: string;
  expires_at: string;
  max_uses: number | null;
  use_count: number;
  revoked: boolean;
  is_active: boolean;
  created_at: string;
}

export interface LeaderboardRow {
  rank: number;
  public_id: string;
  username: string;
  display_name: string;
  avatar_url: string;
  total_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  score: number;
  current_streak: number;
  longest_streak: number;
}

export interface LeaderboardResponse {
  period: "daily" | "weekly" | "all-time";
  rows: LeaderboardRow[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
