import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NotesListPage from './pages/NotesListPage';
import NoteDetailPage from './pages/NoteDetailPage';

function App() {
  return (
    <BrowserRouter>
      <div className="container">
        <Routes>
          <Route path="/" element={<NotesListPage />} />
          <Route path="/notes/:id" element={<NoteDetailPage />} />
          {/* Optional: A dedicated route for creating new notes if not handled by NotesListPage */}
          {/* <Route path="/notes/new" element={<NoteDetailPage />} /> */}
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;