import React, { useState, useEffect } from 'react';

function NoteForm({ note, onSubmit, onCancel }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');

  useEffect(() => {
    if (note) {
      setTitle(note.title || '');
      setBody(note.body || '');
    } else {
      setTitle('');
      setBody('');
    }
  }, [note]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ title, body });
  };

  return (
    <form onSubmit={handleSubmit} className="note-form">
      <div className="form-group">
        <label htmlFor="title">Title</label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note Title"
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="body">Body</label>
        <textarea
          id="body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Note Body"
          rows="10"
          required
        ></textarea>
      </div>
      <div className="form-actions">
        <button type="submit" className="button primary">
          {note ? 'Update Note' : 'Create Note'}
        </button>
        <button type="button" onClick={onCancel} className="button secondary">
          Cancel
        </button>
      </div>
    </form>
  );
}

export default NoteForm;