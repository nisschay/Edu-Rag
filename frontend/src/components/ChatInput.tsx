/**
 * ChatInput Component
 * 
 * Sticky input box at the bottom of the chat window.
 * Disabled when no topic is selected.
 */

import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onUpload?: () => void; // Optional upload handler
  disabled: boolean;
  placeholder?: string;
  isLoading?: boolean;
}

export function ChatInput({ onSend, onUpload, disabled, placeholder, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isLoading) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-dark-600 bg-dark-800">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <div className="flex-1 relative flex gap-2">
          {/* Upload Button */}
          {onUpload && (
            <button
              type="button"
              onClick={onUpload}
              disabled={disabled || isLoading}
              className={`p-3 rounded-xl transition-colors shrink-0
                ${disabled || isLoading
                  ? 'bg-dark-700 text-gray-500 cursor-not-allowed'
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-600 hover:text-white border border-dark-500'
                }`}
              title="Upload material"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </button>
          )}

          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            placeholder={placeholder || 'Ask a question...'}
            rows={1}
            className={`w-full resize-none rounded-xl px-4 py-3 pr-12 text-sm
              bg-dark-700 border border-dark-500 text-gray-100
              placeholder-gray-500 focus:outline-none focus:border-accent-primary
              focus:ring-1 focus:ring-accent-primary
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors`}
          />
        </div>

        <button
          type="submit"
          disabled={disabled || !message.trim() || isLoading}
          className={`p-3 rounded-xl transition-colors
            ${disabled || !message.trim() || isLoading
              ? 'bg-dark-600 text-gray-500 cursor-not-allowed'
              : 'bg-accent-primary hover:bg-accent-hover text-white'
            }`}
        >
          {isLoading ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
}
