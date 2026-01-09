/**
 * ChatWindow Component
 * 
 * Main chat area with message history and input.
 * Supports flexible chat (no topic) and file uploads with location picking.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { Message, ActiveContext, SubjectWithUnits, UnitState, File as ApiFile } from '../types';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import * as api from '../api/client';

interface ChatWindowProps {
  messages: Message[];
  context: ActiveContext;
  subjects: SubjectWithUnits[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export function ChatWindow({ messages, context, subjects, onSendMessage, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasContext = !!(context.subject && context.topic);

  // Unit Status & Files
  const [unitState, setUnitState] = useState<UnitState | null>(null);
  const [topicFiles, setTopicFiles] = useState<ApiFile[]>([]);
  const [showFiles, setShowFiles] = useState(false);

  // File Upload State (Restored)
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [showLocationPicker, setShowLocationPicker] = useState(false);

  // Location Picker State (Restored)
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [selectedUnitId, setSelectedUnitId] = useState<number | null>(null);
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null);

  // Poll Unit Status
  useEffect(() => {
    if (!context.subject || !context.unit) {
      setUnitState(null);
      return;
    }

    let isMounted = true;
    const fetchStatus = async () => {
      try {
        const unit = await api.getUnit(context.subject!.id, context.unit!.id);
        if (isMounted) {
          setUnitState(unit.processing_state || null);
        }
      } catch (e) {
        console.error("Failed to poll unit status", e);
      }
    };

    fetchStatus(); // Initial fetch
    const interval = setInterval(fetchStatus, 3000); // Poll every 3s
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [context.subject, context.unit]);


  // Load Topic Files
  useEffect(() => {
    if (!context.subject || !context.unit || !context.topic) {
      setTopicFiles([]);
      return;
    }

    const loadFiles = async () => {
      try {
        const result = await api.getFiles(context.subject!.id, context.unit!.id, context.topic!.id);
        setTopicFiles(result.files);
      } catch (e) {
        console.error("Failed to load files", e);
      }
    };

    loadFiles();
    // Also reload when status changes to ready (to see extracted text indication if we used that)
  }, [context.subject, context.unit, context.topic, unitState?.status]);


  // Handle file selection
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (hasContext) {
      startUpload(file, context.subject!.id, context.unit!.id, context.topic!.id);
    } else {
      // ... (existing picker logic if we keep it, but for simplicity assuming context)
      // If global, we disable upload in ChatInput usually, or show picker. 
      setPendingFile(file);
      setShowLocationPicker(true);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const startUpload = async (file: File, subjectId: number, unitId: number, topicId: number) => {
    setIsUploading(true);
    setUploadStatus('Uploading...'); // Temporary local status
    setShowLocationPicker(false);

    try {
      // Backend now returns immediately
      await api.uploadFile(subjectId, unitId, topicId, file);
      // Status poller will pick up "uploaded" then "processing"
    } catch (error: any) {
      console.error('Upload failed:', error);
      alert(`Upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
      setUploadStatus(null);
      setPendingFile(null);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // existing picker submit...
  const handlePickerSubmit = () => {
    if (pendingFile && selectedSubjectId && selectedUnitId && selectedTopicId) {
      startUpload(pendingFile, selectedSubjectId, selectedUnitId, selectedTopicId);
    }
  };

  // Get units/topics for picker...
  const activeSubject = subjects.find(s => s.id === selectedSubjectId);
  const activeUnit = activeSubject?.units.find(u => u.id === selectedUnitId);

  return (
    <div className="flex flex-col h-full bg-dark-800 relative">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md,.docx"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Header */}
      <div className="px-6 py-4 border-b border-dark-600 bg-dark-800 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-100">
              {hasContext ? context.topic?.title : "Global Chat"}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {hasContext ? (
                <>
                  {context.subject?.name} <span className="mx-2">→</span> {context.unit?.title}
                </>
              ) : (
                "Asking about anything across your subjects"
              )}
            </p>
          </div>

          {/* File List Toggle */}
          {hasContext && (
            <button
              onClick={() => setShowFiles(!showFiles)}
              className="text-sm text-accent-primary hover:text-accent-hover underline"
            >
              {showFiles ? 'Hide Files' : `Show Files (${topicFiles.length})`}
            </button>
          )}
        </div>

        {/* Unit Status Banner */}
        {unitState && unitState.status !== 'ready' && (
          <div className={`text-sm px-3 py-2 rounded-lg flex items-center gap-2
                ${unitState.status === 'failed' ? 'bg-red-900/30 text-red-200 border border-red-800' :
              unitState.status === 'empty' ? 'bg-dark-700 text-gray-400' :
                'bg-blue-900/30 text-blue-200 border border-blue-800'}`}>

            {unitState.status === 'processing' && (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}

            <span className="font-medium uppercase text-xs tracking-wider">{unitState.status}</span>
            <span>
              {unitState.status === 'failed' ? unitState.last_error :
                unitState.status === 'processing' ? 'Processing material...' :
                  unitState.status === 'uploaded' ? 'Queued for processing...' :
                    'No material uploaded'}
            </span>
          </div>
        )}

        {/* File List Panel */}
        {showFiles && hasContext && (
          <div className="bg-dark-700 rounded-lg p-3 mt-2 text-sm text-gray-300">
            <h3 className="font-medium text-gray-400 mb-2 uppercase text-xs">Files in {context.topic?.title}</h3>
            {topicFiles.length === 0 ? (
              <p className="text-gray-500 italic">No files uploaded.</p>
            ) : (
              <ul className="space-y-1">
                {topicFiles.map(f => (
                  <li key={f.id} className="flex justify-between">
                    <span>{f.filename}</span>
                    <span className="text-xs text-gray-500">{(f.file_size / 1024).toFixed(1)} KB</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-dark-700 flex items-center justify-center">
                <svg className="w-8 h-8 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h2 className="text-xl font-medium text-gray-300 mb-2">
                {subjects.length === 0 ? "Welcome to Education RAG" : "How can I help you?"}
              </h2>
              <p className="text-gray-500 max-w-sm mx-auto">
                {subjects.length === 0
                  ? "Create a subject in the sidebar to start learning!"
                  : hasContext
                    ? `Ask anything about ${context.topic?.title}`
                    : "Select a topic for best results, or just start chatting!"}
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-dark-700 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-75" />
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-150" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={onSendMessage}
        onUpload={hasContext || subjects.length > 0 ? handleUploadClick : undefined}
        disabled={subjects.length === 0}
        isLoading={isLoading}
        placeholder={hasContext ? `Message about ${context.topic?.title}...` : "Type a message..."}
      />

      {/* Location Picker Modal */}
      {showLocationPicker && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 w-96 shadow-xl">
            <h3 className="text-lg font-medium text-gray-100 mb-4">Select Upload Location</h3>

            <div className="space-y-4">
              {/* Subject Select */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Subject</label>
                <select
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-gray-200 outline-none focus:border-accent-primary"
                  value={selectedSubjectId || ''}
                  onChange={(e) => {
                    const id = Number(e.target.value);
                    setSelectedSubjectId(id);
                    setSelectedUnitId(null);
                    setSelectedTopicId(null);
                  }}
                >
                  <option value="">Select Subject</option>
                  {subjects.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              {/* Unit Select */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Unit</label>
                <select
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-gray-200 outline-none focus:border-accent-primary disabled:opacity-50"
                  value={selectedUnitId || ''}
                  onChange={(e) => {
                    setSelectedUnitId(Number(e.target.value));
                    setSelectedTopicId(null);
                  }}
                  disabled={!selectedSubjectId}
                >
                  <option value="">Select Unit</option>
                  {activeSubject?.units.map(u => (
                    <option key={u.id} value={u.id}>{u.title}</option>
                  ))}
                </select>
              </div>

              {/* Topic Select */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Topic</label>
                <select
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-gray-200 outline-none focus:border-accent-primary disabled:opacity-50"
                  value={selectedTopicId || ''}
                  onChange={(e) => setSelectedTopicId(Number(e.target.value))}
                  disabled={!selectedUnitId}
                >
                  <option value="">Select Topic</option>
                  {activeUnit?.topics.map(t => (
                    <option key={t.id} value={t.id}>{t.title}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => {
                  setShowLocationPicker(false);
                  setPendingFile(null);
                }}
                className="flex-1 px-4 py-2 rounded-lg bg-dark-700 text-gray-300 hover:bg-dark-600"
              >
                Cancel
              </button>
              <button
                disabled={!selectedTopicId}
                onClick={handlePickerSubmit}
                className="flex-1 px-4 py-2 rounded-lg bg-accent-primary text-white hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
