import React from 'react';

function NoteDetail({ note, onEdit, onDelete, onCancel }) {
  if (!note) {
    return <p>No note selected.</p>;
  }

  const formattedDate = new Date(note.created_at).toLocaleString();

  return (
    <div className="note-detail-container">
      <h2>{note.title}</h2>
      <p className="note-detail-body">{note.body}</p>
      <p className="note-detail-date">Created: {formattedDate}</p>
      <div className="note-detail-actions">
        <button onClick={() => onEdit(note.id)}>Edit</button>
        <button className="delete-button" onClick={() => onDelete(note.id)}>Delete</button>
        <button onClick={onCancel}>Back to List</button>
      </div>
    </div>
  );
}

export default NoteDetail;