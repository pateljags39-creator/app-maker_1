const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchAllNotes() {
  const response = await fetch(`${API_BASE_URL}/api/notes`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

async function fetchNoteById(id) {
  const response = await fetch(`${API_BASE_URL}/api/notes/${id}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

async function createNote(noteData) {
  const response = await fetch(`${API_BASE_URL}/api/notes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(noteData),
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

async function updateNote(id, noteData) {
  const response = await fetch(`${API_BASE_URL}/api/notes/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(noteData),
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

async function deleteNote(id) {
  const response = await fetch(`${API_BASE_URL}/api/notes/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  // DELETE requests typically don't return a body, just status 204 No Content
  // We can return true for success or handle specific status codes
  return response.status === 204 || response.ok;
}

export {
  fetchAllNotes,
  fetchNoteById,
  createNote,
  updateNote,
  deleteNote,
};