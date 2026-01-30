export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  title: string;
  content: string;
  owner_id: number;
  workspace_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  id: number;
  name: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: number;
  workspace_id: number;
  user_id: number;
  role: "owner" | "editor" | "viewer";
  joined_at: string;
}

export interface DocumentShare {
  id: number;
  document_id: number;
  shared_with_user_id: number;
  permission: "view" | "edit";
  shared_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
