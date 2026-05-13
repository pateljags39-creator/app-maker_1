import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getNoteById, updateNote, deleteNote } from '../api';
import NoteForm from '../components/NoteForm';

function NoteDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);

  useEffect(() => {
    const fetchNote = async () => {
      try {
        const fetchedNote = await getNoteById(id);
        setNote(fetchedNote);
      } catch (error) {
        console.error('Failed to fetch note:', error);
      }
    };
    fetchNote();
  }, [id]);

  const handleSave = async (updatedNote) => {
    try {
      await updateNote(id, updatedNote);
      navigate('/');
    } catch (error) {
      console.error('Failed to update note:', error);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this note?')) {
      try {
        await deleteNote(id);
        navigate('/');
      } catch (error) {
        console.error('Failed to delete note:', error);
      }
    }
  };

  if (!note) {
    return <div>Loading note...</div>;
  }

  return (
    <div>
      <h1>Edit Note</h1>
      <NoteForm initialNote={note} onSave={handleSave} />
      <button onClick={handleDelete} className="button-danger">
        Delete Note
      </button>
    </div>
  );
}

export default NoteDetailPage;
