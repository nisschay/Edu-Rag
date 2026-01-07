/**
 * Main App Component
 * 
 * Two-panel layout with sidebar navigation and chat window.
 * Manages state for subjects, context, and chat history.
 */

import { useState, useEffect, useCallback } from 'react';
import { Sidebar, ChatWindow } from './components';
import * as api from './api/client';
import type {
  SubjectWithUnits,
  UnitWithTopics,
  Topic,
  Message,
  ActiveContext,
} from './types';

function App() {
  // Navigation state
  const [subjects, setSubjects] = useState<SubjectWithUnits[]>([]);
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(true);

  // Active context
  const [context, setContext] = useState<ActiveContext>({
    subject: null,
    unit: null,
    topic: null,
  });

  // Chat state - keyed by topic ID
  const [chatHistories, setChatHistories] = useState<Record<number, Message[]>>({});
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Get current messages for selected topic
  const currentMessages = context.topic
    ? chatHistories[context.topic.id] || []
    : [];

  // Load subjects on mount
  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    setIsLoadingSubjects(true);
    try {
      const subjectList = await api.getSubjects();
      
      // Convert to SubjectWithUnits
      const subjectsWithUnits: SubjectWithUnits[] = subjectList.map((s) => ({
        ...s,
        units: [],
        expanded: false,
      }));
      
      setSubjects(subjectsWithUnits);
    } catch (error) {
      console.error('Failed to load subjects:', error);
    } finally {
      setIsLoadingSubjects(false);
    }
  };

  const handleToggleSubject = useCallback(async (subjectId: number) => {
    setSubjects((prev) =>
      prev.map((s) => {
        if (s.id === subjectId) {
          // Load units if expanding and not yet loaded
          if (!s.expanded && s.units.length === 0) {
            loadUnits(subjectId);
          }
          return { ...s, expanded: !s.expanded };
        }
        return s;
      })
    );
  }, []);

  const loadUnits = async (subjectId: number) => {
    try {
      const units = await api.getUnits(subjectId);
      
      const unitsWithTopics: UnitWithTopics[] = units.map((u) => ({
        ...u,
        topics: [],
        expanded: false,
      }));

      setSubjects((prev) =>
        prev.map((s) =>
          s.id === subjectId ? { ...s, units: unitsWithTopics } : s
        )
      );
    } catch (error) {
      console.error('Failed to load units:', error);
    }
  };

  const handleToggleUnit = useCallback(
    async (subjectId: number, unitId: number) => {
      setSubjects((prev) =>
        prev.map((s) => {
          if (s.id === subjectId) {
            return {
              ...s,
              units: s.units.map((u) => {
                if (u.id === unitId) {
                  // Load topics if expanding and not yet loaded
                  if (!u.expanded && u.topics.length === 0) {
                    loadTopics(subjectId, unitId);
                  }
                  return { ...u, expanded: !u.expanded };
                }
                return u;
              }),
            };
          }
          return s;
        })
      );
    },
    []
  );

  const loadTopics = async (subjectId: number, unitId: number) => {
    try {
      const topics = await api.getTopics(subjectId, unitId);

      setSubjects((prev) =>
        prev.map((s) => {
          if (s.id === subjectId) {
            return {
              ...s,
              units: s.units.map((u) =>
                u.id === unitId ? { ...u, topics } : u
              ),
            };
          }
          return s;
        })
      );
    } catch (error) {
      console.error('Failed to load topics:', error);
    }
  };

  const handleSelectTopic = useCallback(
    (subject: SubjectWithUnits, unit: UnitWithTopics, topic: Topic) => {
      setContext({
        subject,
        unit,
        topic,
      });
    },
    []
  );

  const handleSendMessage = useCallback(
    async (messageText: string) => {
      if (!context.subject || !context.topic) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: messageText,
        timestamp: new Date(),
      };

      // Add user message to history
      setChatHistories((prev) => ({
        ...prev,
        [context.topic!.id]: [...(prev[context.topic!.id] || []), userMessage],
      }));

      setIsLoadingChat(true);

      try {
        const response = await api.sendMessage(context.subject.id, {
          message: messageText,
          unit_id: context.unit?.id || null,
          topic_id: context.topic.id,
        });

        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          timestamp: new Date(),
        };

        // Add assistant message to history
        setChatHistories((prev) => ({
          ...prev,
          [context.topic!.id]: [...(prev[context.topic!.id] || []), assistantMessage],
        }));
      } catch (error) {
        console.error('Chat error:', error);

        const errorMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content:
            error instanceof Error
              ? `Error: ${error.message}`
              : 'Something went wrong. Please try again.',
          timestamp: new Date(),
        };

        setChatHistories((prev) => ({
          ...prev,
          [context.topic!.id]: [...(prev[context.topic!.id] || []), errorMessage],
        }));
      } finally {
        setIsLoadingChat(false);
      }
    },
    [context]
  );

  return (
    <div className="flex h-screen bg-dark-800 text-gray-100">
      {/* Sidebar */}
      <Sidebar
        subjects={subjects}
        selectedTopicId={context.topic?.id || null}
        isLoading={isLoadingSubjects}
        onToggleSubject={handleToggleSubject}
        onToggleUnit={handleToggleUnit}
        onSelectTopic={handleSelectTopic}
        onRefresh={loadSubjects}
      />

      {/* Main Chat Area */}
      <main className="flex-1">
        <ChatWindow
          messages={currentMessages}
          context={context}
          onSendMessage={handleSendMessage}
          isLoading={isLoadingChat}
        />
      </main>
    </div>
  );
}

export default App;
