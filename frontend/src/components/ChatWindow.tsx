/**
 * ChatWindow Component
 * 
 * Main chat area with message history and input.
 * Shows placeholder when no topic is selected.
 */

import { useEffect, useRef } from 'react';
import type { Message, ActiveContext } from '../types';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';

interface ChatWindowProps {
  messages: Message[];
  context: ActiveContext;
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export function ChatWindow({ messages, context, onSendMessage, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasContext = context.subject && context.topic;

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-dark-800">
      {/* Header */}
      <div className="px-6 py-4 border-b border-dark-600 bg-dark-800">
        {hasContext ? (
          <div>
            <h1 className="text-lg font-semibold text-gray-100">
              {context.topic?.title}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {context.subject?.name}
              {context.unit && (
                <>
                  <span className="mx-2">→</span>
                  {context.unit.title}
                </>
              )}
            </p>
          </div>
        ) : (
          <h1 className="text-lg font-semibold text-gray-400">
            Education RAG
          </h1>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {!hasContext ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-dark-700 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-medium text-gray-300 mb-2">
                Welcome to Education RAG
              </h2>
              <p className="text-gray-500 max-w-sm">
                Select a subject and topic from the sidebar to start learning
              </p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-dark-700 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-accent-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-medium text-gray-300 mb-2">
                Ready to learn
              </h2>
              <p className="text-gray-500 max-w-sm">
                Ask any question about <span className="text-accent-primary">{context.topic?.title}</span>
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
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
        disabled={!hasContext}
        isLoading={isLoading}
        placeholder={
          hasContext
            ? `Ask about ${context.topic?.title}...`
            : 'Select a topic to start chatting'
        }
      />
    </div>
  );
}
