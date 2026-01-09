/**
 * API Client for Education RAG Backend
 * 
 * All requests include x-user-id header for auth stub
 */

import type { Subject, Unit, Topic, File, ChatRequest, ChatResponse } from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

// Default user ID (auth stub)
let currentUserId = 1;

export function setUserId(id: number): void {
  currentUserId = id;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'x-user-id': String(currentUserId),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Subjects API
// ============================================================================

export async function getSubjects(): Promise<Subject[]> {
  const data = await apiRequest<{ subjects: Subject[] }>('/subjects');
  return data.subjects;
}

export async function createSubject(name: string, description?: string): Promise<Subject> {
  return apiRequest<Subject>('/subjects', {
    method: 'POST',
    body: JSON.stringify({ name, description }),
  });
}

// ============================================================================
// Units API
// ============================================================================

export async function getUnits(subjectId: number): Promise<Unit[]> {
  const data = await apiRequest<{ units: Unit[] }>(`/subjects/${subjectId}/units`);
  return data.units;
}

export async function createUnit(
  subjectId: number,
  title: string,
  description?: string
): Promise<Unit> {
  return apiRequest<Unit>(`/subjects/${subjectId}/units`, {
    method: 'POST',
    body: JSON.stringify({ title, description }),
  });
}

export async function getUnit(subjectId: number, unitId: number): Promise<Unit> {
  return apiRequest<Unit>(`/subjects/${subjectId}/units/${unitId}`);
}

// ============================================================================
// Topics API
// ============================================================================

export async function getTopics(subjectId: number, unitId: number): Promise<Topic[]> {
  const data = await apiRequest<{ topics: Topic[] }>(
    `/subjects/${subjectId}/units/${unitId}/topics`
  );
  return data.topics;
}

export async function createTopic(
  subjectId: number,
  unitId: number,
  title: string
): Promise<Topic> {
  return apiRequest<Topic>(`/subjects/${subjectId}/units/${unitId}/topics`, {
    method: 'POST',
    body: JSON.stringify({ title }),
  });
}

// ============================================================================
// Chat API
// ============================================================================

export async function sendMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  // Use new flexible endpoint
  return apiRequest<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ============================================================================
// File Upload API
// ============================================================================

export async function uploadFile(
  subjectId: number,
  unitId: number,
  topicId: number,
  file: File | globalThis.File
): Promise<{ message: string; file: any }> {
  const formData = new FormData();
  formData.append('file', file as any);

  const url = `${API_BASE}/subjects/${subjectId}/units/${unitId}/topics/${topicId}/files`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'x-user-id': String(currentUserId),
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function getFileStatus(
  subjectId: number,
  unitId: number,
  topicId: number,
  fileId: number
): Promise<any> {
  return apiRequest(`/subjects/${subjectId}/units/${unitId}/topics/${topicId}/files/${fileId}/status`);
}

export async function getFiles(
  subjectId: number,
  unitId: number,
  topicId: number
): Promise<{ files: any[]; count: number }> {
  return apiRequest(`/subjects/${subjectId}/units/${unitId}/topics/${topicId}/files`);
}

// Obsolete: Handled in background now
// export async function processChunks(...)
// export async function embedChunks(...)

// ============================================================================
// Summary API
// ============================================================================

export async function generateTopicSummary(
  subjectId: number,
  unitId: number,
  topicId: number
): Promise<{ summary_text: string }> {
  return apiRequest(`/subjects/${subjectId}/units/${unitId}/topics/${topicId}/summarize`, {
    method: 'POST',
  });
}

export async function generateUnitSummary(
  subjectId: number,
  unitId: number
): Promise<{ summary_text: string }> {
  return apiRequest(`/subjects/${subjectId}/units/${unitId}/summarize`, {
    method: 'POST',
  });
}

export async function embedSummaries(
  subjectId: number,
  unitId: number
): Promise<{ newly_embedded: number }> {
  return apiRequest(`/subjects/${subjectId}/units/${unitId}/embed-summaries`, {
    method: 'POST',
  });
}
