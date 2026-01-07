/**
 * MessageBubble Component
 * 
 * Displays a single chat message with appropriate styling
 * for user vs assistant messages. Includes source display.
 */

import { useState } from 'react';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-accent-primary text-white rounded-br-md'
            : 'bg-dark-700 text-gray-100 rounded-bl-md'
        }`}
      >
        {/* Message Content */}
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {formatContent(message.content)}
        </div>

        {/* Sources (for assistant messages) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-2 border-t border-dark-500">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs text-gray-400 hover:text-gray-300 flex items-center gap-1"
            >
              <svg
                className={`w-3 h-3 transition-transform ${showSources ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {showSources ? 'Hide' : 'Show'} {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </button>
            
            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="text-xs bg-dark-800 rounded-lg p-2 text-gray-400"
                  >
                    <span className="text-gray-500">
                      [{source.source_type}:{source.source_id}]
                    </span>
                    {source.preview && (
                      <p className="mt-1 text-gray-500 line-clamp-2">
                        {source.preview}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs mt-2 ${isUser ? 'text-indigo-200' : 'text-gray-500'}`}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatContent(content: string): React.ReactNode {
  // Simple code block detection
  const parts = content.split(/(```[\s\S]*?```)/g);
  
  return parts.map((part, idx) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const code = part.slice(3, -3).replace(/^\w+\n/, '');
      return (
        <pre
          key={idx}
          className="bg-dark-900 rounded-lg p-3 my-2 overflow-x-auto text-xs font-mono"
        >
          <code>{code}</code>
        </pre>
      );
    }
    
    // Simple inline code
    const inlineParts = part.split(/(`[^`]+`)/g);
    return inlineParts.map((inline, i) => {
      if (inline.startsWith('`') && inline.endsWith('`')) {
        return (
          <code
            key={`${idx}-${i}`}
            className="bg-dark-900 px-1.5 py-0.5 rounded text-indigo-300 text-xs"
          >
            {inline.slice(1, -1)}
          </code>
        );
      }
      return inline;
    });
  });
}
