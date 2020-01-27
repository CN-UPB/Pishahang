export interface Session {
  username: string;
  session_began_at: Date;
  token: Token;
}

export interface Token {
  access_token: string;
  expires_in: number;
  refresh_expires_in: number;
  refresh_token: string;
  token_type: string;
  session_state: string;
}
