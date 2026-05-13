import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getNotes } from '../api';

function NotesListPage() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const data = await getNotes();
        setNotes(data);
      } catch (err) {
        console.error("Failed to fetch notes:", err);
        setError("Failed to load notes. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchNotes();
  }, []);

  if (loading) {
    return <div className="container">Loading notes...</div>;
  }

  if (error) {
    return <div className="container error-message">{error}</div>;
  }

  return (
    <div className="container">
      <div className="notes-header">
        <h1>My Notes</h1>
        <Link to="/notes/new" className="button primary">
          + Create Note
        </Link>
      </div>

      <div className="notes-list">
        {notes.length === 0 ? (
          <p>No notes found. Create your first note!</p>
        ) : (
          notes.map((note) => (
            <Link key={note.id} to={`/notes/${note.id}`} className="note-card">
              <h2>{note.title || "Untitled Note"}</h2>
              <p className="note-date">
                {new Date(note.created_at).toLocaleString()}
              </p>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}

export default NotesListPage;