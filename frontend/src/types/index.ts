/**
 * API Types for Education RAG
 */

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface Subject {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Unit {
  id: number;
  subject_id: number;
  title: string;
  description: string | null;
  created_at: string;
}

export interface Topic {
  id: number;
  unit_id: number;
  title: string;
  created_at: string;
}

export interface SourceReference {
  source_type: 'chunk' | 'topic_summary' | 'unit_summary';
  source_id: number;
  score: number;
  preview: string;
}

export interface ChatRequest {
  message: string;
  unit_id: number | null;
  topic_id: number | null;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: SourceReference[];
  subject_id: number;
  unit_id: number | null;
  topic_id: number | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceReference[];
  timestamp: Date;
}

export interface ActiveContext {
  subject: Subject | null;
  unit: Unit | null;
  topic: Topic | null;
}

export interface SubjectWithUnits extends Subject {
  units: UnitWithTopics[];
  expanded: boolean;
}

export interface UnitWithTopics extends Unit {
  topics: Topic[];
  expanded: boolean;
}
