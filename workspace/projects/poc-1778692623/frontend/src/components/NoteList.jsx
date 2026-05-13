import React from 'react';

function NoteList({ notes, onSelectNote, selectedNoteId }) {
  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  return (
    <div className="note-list">
      {notes.length === 0 ? (
        <p className="no-notes-message">No notes yet. Create one!</p>
      ) : (
        notes.map((note) => (
          <div
            key={note.id}
            className={`note-list-item ${selectedNoteId === note.id ? 'selected' : ''}`}
            onClick={() => onSelectNote(note.id)}
          >
            <h3 className="note-list-title">{note.title || 'Untitled Note'}</h3>
            <p className="note-list-body-snippet">
              {note.body ? note.body.substring(0, 100) + (note.body.length > 100 ? '...' : '') : 'No content'}
            </p>
            <span className="note-list-date">{formatDate(note.created_at)}</span>
          </div>
        ))
      )}
    </div>
  );
}

export default NoteList;