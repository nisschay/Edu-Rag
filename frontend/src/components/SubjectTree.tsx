/**
 * SubjectTree Component
 * 
 * Expandable tree navigation for subjects, units, and topics.
 */

import type { SubjectWithUnits, UnitWithTopics, Topic } from '../types';

interface SubjectTreeProps {
  subjects: SubjectWithUnits[];
  selectedTopicId: number | null;
  onToggleSubject: (subjectId: number) => void;
  onToggleUnit: (subjectId: number, unitId: number) => void;
  onSelectTopic: (subject: SubjectWithUnits, unit: UnitWithTopics, topic: Topic) => void;
}

export function SubjectTree({
  subjects,
  selectedTopicId,
  onToggleSubject,
  onToggleUnit,
  onSelectTopic,
}: SubjectTreeProps) {
  if (subjects.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        <p>No subjects yet</p>
        <p className="text-xs mt-1">Create one using the API</p>
      </div>
    );
  }

  return (
    <div className="py-2">
      {subjects.map((subject) => (
        <div key={subject.id} className="mb-1">
          {/* Subject */}
          <button
            onClick={() => onToggleSubject(subject.id)}
            className="w-full flex items-center gap-2 px-4 py-2 text-left
              text-gray-300 hover:bg-dark-600 transition-colors group"
          >
            <svg
              className={`w-4 h-4 text-gray-500 transition-transform ${
                subject.expanded ? 'rotate-90' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <svg
              className="w-4 h-4 text-accent-primary"
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
            <span className="font-medium truncate">{subject.name}</span>
          </button>

          {/* Units */}
          {subject.expanded && (
            <div className="ml-4">
              {subject.units.length === 0 ? (
                <div className="px-4 py-2 text-xs text-gray-600">No units</div>
              ) : (
                subject.units.map((unit) => (
                  <div key={unit.id}>
                    {/* Unit */}
                    <button
                      onClick={() => onToggleUnit(subject.id, unit.id)}
                      className="w-full flex items-center gap-2 px-4 py-1.5 text-left
                        text-gray-400 hover:bg-dark-600 transition-colors text-sm"
                    >
                      <svg
                        className={`w-3 h-3 text-gray-600 transition-transform ${
                          unit.expanded ? 'rotate-90' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <svg
                        className="w-4 h-4 text-gray-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                        />
                      </svg>
                      <span className="truncate">{unit.title}</span>
                    </button>

                    {/* Topics */}
                    {unit.expanded && (
                      <div className="ml-4">
                        {unit.topics.length === 0 ? (
                          <div className="px-4 py-1.5 text-xs text-gray-600">No topics</div>
                        ) : (
                          unit.topics.map((topic) => (
                            <button
                              key={topic.id}
                              onClick={() => onSelectTopic(subject, unit, topic)}
                              className={`w-full flex items-center gap-2 px-4 py-1.5 text-left
                                text-sm transition-colors ${
                                  selectedTopicId === topic.id
                                    ? 'bg-accent-primary/20 text-accent-primary'
                                    : 'text-gray-500 hover:bg-dark-600 hover:text-gray-300'
                                }`}
                            >
                              <svg
                                className="w-3 h-3"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <circle cx="12" cy="12" r="4" />
                              </svg>
                              <span className="truncate">{topic.title}</span>
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
