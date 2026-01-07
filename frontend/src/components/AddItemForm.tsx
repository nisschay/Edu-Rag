/**
 * AddItemForm Component
 * 
 * Reusable inline form for adding subjects, units, and topics.
 */

import { useState, useRef, useEffect } from 'react';

interface AddItemFormProps {
    placeholder: string;
    onSubmit: (name: string) => Promise<void>;
    onCancel: () => void;
    isLoading?: boolean;
}

export function AddItemForm({ placeholder, onSubmit, onCancel, isLoading }: AddItemFormProps) {
    const [value, setValue] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (value.trim() && !isLoading) {
            await onSubmit(value.trim());
            setValue('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            onCancel();
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex items-center gap-2 px-4 py-2">
            <input
                ref={inputRef}
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={isLoading}
                className="flex-1 px-3 py-1.5 text-sm rounded-lg bg-dark-700 border border-dark-500 
          text-gray-100 placeholder-gray-500 focus:outline-none focus:border-accent-primary
          disabled:opacity-50"
            />
            <button
                type="submit"
                disabled={!value.trim() || isLoading}
                className="p-1.5 rounded-lg bg-accent-primary text-white hover:bg-accent-hover
          disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                {isLoading ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                )}
            </button>
            <button
                type="button"
                onClick={onCancel}
                disabled={isLoading}
                className="p-1.5 rounded-lg text-gray-400 hover:bg-dark-600 hover:text-gray-200
          disabled:opacity-50 transition-colors"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </form>
    );
}
