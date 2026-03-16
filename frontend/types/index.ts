export interface User {
  id: string;
  full_name: string;
  email: string;
  loyalty_points: number;
  is_verified: boolean;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  created_at?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}
