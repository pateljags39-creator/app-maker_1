import React, { useState, useEffect } from 'react';

function NoteForm({ note, onSave }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');

  useEffect(() => {
    if (note) {
      setTitle(note.title);
      setBody(note.body);
    } else {
      setTitle('');
      setBody('');
    }
  }, [note]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: note ? note.id : undefined, // Include ID if editing
      title,
      body,
    });
    // Clear form only if it's a new note or after successful submission
    if (!note) {
      setTitle('');
      setBody('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="note-form">
      <h2 className="text-xl font-bold mb-4">{note ? 'Edit Note' : 'Create New Note'}</h2>
      <div className="mb-4">
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
          Title
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note Title"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="mb-4">
        <label htmlFor="body" className="block text-sm font-medium text-gray-700 mb-1">
          Body
        </label>
        <textarea
          id="body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Note Body"
          rows="8"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        ></textarea>
      </div>
      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        {note ? 'Update Note' : 'Add Note'}
      </button>
    </form>
  );
}

export default NoteForm;