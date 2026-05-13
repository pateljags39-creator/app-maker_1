import React, { useState, useEffect } from 'react';
import NoteList from './components/NoteList';
import NoteForm from './components/NoteForm';
import NoteDetail from './components/NoteDetail';
import * as api from './api';

function App() {
  const [notes, setNotes] = useState([]);
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [editingNote, setEditingNote] = useState(null); // Null for viewing/listing, object for creating/editing

  // Fetches all notes from the backend
  const fetchNotes = async () => {
    try {
      const data = await api.getNotes();
      setNotes(data);
    } catch (error) {
      console.error("Error fetching notes:", error);
      alert("Failed to load notes. Please ensure the backend server is running.");
    }
  };

  // Effect to load notes on initial component mount
  useEffect(() => {
    fetchNotes();
  }, []);

  // Handler for saving a note (either creating or updating)
  const handleSaveNote = async (noteData) => {
    try {
      if (noteData.id) {
        // Update existing note
        await api.updateNote(noteData.id, { title: noteData.title, body: noteData.body });
        setSelectedNoteId(noteData.id); // Keep the updated note selected
      } else {
        // Create new note
        const newNote = await api.createNote(noteData);
        setSelectedNoteId(newNote.id); // Select the newly created note
      }
      setEditingNote(null); // Close the form
      await fetchNotes(); // Refresh the notes list
    } catch (error) {
      console.error("Error saving note:", error);
      alert(`Failed to ${noteData.id ? 'update' : 'create'} note.`);
    }
  };

  // Handler for deleting a note
  const handleDeleteNote = async (id) => {
    if (window.confirm("Are you sure you want to delete this note?")) {
      try {
        await api.deleteNote(id);
        setSelectedNoteId(null); // Clear selection
        setEditingNote(null); // Close any open form related to this note
        await fetchNotes(); // Refresh the notes list
      } catch (error) {
        console.error("Error deleting note:", error);
        alert("Failed to delete note.");
      }
    }
  };

  // Handler for selecting a note from the list
  const handleSelectNote = (id) => {
    setSelectedNoteId(id);
    setEditingNote(null); // Close any open form
  };

  // Handler for initiating a new note creation
  const handleAddNewNote = () => {
    setEditingNote({ title: '', body: '' }); // Prepare an empty note object for creation
    setSelectedNoteId(null); // Clear any selected note to ensure form is primary view
  };

  // Handler for initiating an edit of the currently selected note
  const handleEditSelectedNote = () => {
    const noteToEdit = notes.find(n => n.id === selectedNoteId);
    if (noteToEdit) {
      setEditingNote(noteToEdit);
    }
  };

  // Handler for canceling the note form (either creation or edit)
  const handleCancelForm = () => {
    setEditingNote(null); // Simply close the form. If a note was selected before, it remains selected.
  };

  // Find the currently selected note object for display in NoteDetail
  const selectedNote = selectedNoteId ? notes.find(n => n.id === selectedNoteId) : null;

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Personal Notes</h1>
      </header>

      <div className="main-content">
        <div className="sidebar">
          <button className="new-note-button" onClick={handleAddNewNote}>
            + New Note
          </button>
          <NoteList 
            notes={notes} 
            onSelectNote={handleSelectNote} 
            selectedNoteId={selectedNoteId} 
          />
        </div>

        <div className="detail-area">
          {editingNote ? (
            // If editingNote is not null, show the NoteForm
            <NoteForm
              note={editingNote} // Pass the note data (either empty for new, or existing for edit)
              onSave={handleSaveNote}
              onCancel={handleCancelForm}
            />
          ) : selectedNote ? (
            // If a note is selected and not editing, show the NoteDetail
            <NoteDetail
              note={selectedNote}
              onEdit={handleEditSelectedNote}
              onDelete={handleDeleteNote}
              onClose={() => setSelectedNoteId(null)} // Option to close detail view
            />
          ) : (
            // Default message when no note is selected or being edited
            <div className="no-selection-message">
              Select a note from the list or create a new one.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;