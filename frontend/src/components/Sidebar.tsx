/**
 * Sidebar Component
 * 
 * Left panel with subject/unit/topic navigation tree.
 */

import { useState } from 'react';
import type { SubjectWithUnits, UnitWithTopics, Topic } from '../types';
import { SubjectTree } from './SubjectTree';
import { AddItemForm } from './AddItemForm';

interface SidebarProps {
  subjects: SubjectWithUnits[];
  selectedTopicId: number | null;
  isLoading: boolean;
  onToggleSubject: (subjectId: number) => void;
  onToggleUnit: (subjectId: number, unitId: number) => void;
  onSelectTopic: (subject: SubjectWithUnits, unit: UnitWithTopics, topic: Topic) => void;
  onRefresh: () => void;
  onCreateSubject: (name: string) => Promise<void>;
  onCreateUnit: (subjectId: number, title: string) => Promise<void>;
  onCreateTopic: (subjectId: number, unitId: number, title: string) => Promise<void>;
}

export function Sidebar({
  subjects,
  selectedTopicId,
  isLoading,
  onToggleSubject,
  onToggleUnit,
  onSelectTopic,
  onRefresh,
  onCreateSubject,
  onCreateUnit,
  onCreateTopic,
}: SidebarProps) {
  const [showAddSubject, setShowAddSubject] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateSubject = async (name: string) => {
    setIsCreating(true);
    try {
      await onCreateSubject(name);
      setShowAddSubject(false);
    } catch (error) {
      console.error('Failed to create subject:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="w-72 h-full flex flex-col bg-dark-900 border-r border-dark-600">
      {/* Header */}
      <div className="p-4 border-b border-dark-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent-primary flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <span className="font-semibold text-gray-100">EduRAG</span>
          </div>

          <div className="flex items-center gap-1">
            {/* Add Subject Button */}
            <button
              onClick={() => setShowAddSubject(true)}
              disabled={isLoading || showAddSubject}
              className="p-2 rounded-lg hover:bg-dark-700 text-gray-400 
                hover:text-accent-primary transition-colors disabled:opacity-50"
              title="Add subject"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 rounded-lg hover:bg-dark-700 text-gray-400 
                hover:text-gray-200 transition-colors disabled:opacity-50"
              title="Refresh subjects"
            >
              <svg
                className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Add Subject Form */}
      {showAddSubject && (
        <AddItemForm
          placeholder="Subject name..."
          onSubmit={handleCreateSubject}
          onCancel={() => setShowAddSubject(false)}
          isLoading={isCreating}
        />
      )}

      {/* Navigation Tree */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && subjects.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            Loading...
          </div>
        ) : (
          <SubjectTree
            subjects={subjects}
            selectedTopicId={selectedTopicId}
            onToggleSubject={onToggleSubject}
            onToggleUnit={onToggleUnit}
            onSelectTopic={onSelectTopic}
            onCreateUnit={onCreateUnit}
            onCreateTopic={onCreateTopic}
          />
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-dark-600">
        <div className="text-xs text-gray-600 text-center">
          User ID: 1 (stub)
        </div>
      </div>
    </div>
  );
}

