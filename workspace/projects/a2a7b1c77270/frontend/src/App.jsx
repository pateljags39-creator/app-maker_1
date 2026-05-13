import React, { useState } from 'react';
import ProjectList from './components/ProjectList';
import ProjectView from './components/ProjectView';

function App() {
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  const handleSelectProject = (projectId) => {
    setSelectedProjectId(projectId);
  };

  const handleBackToList = () => {
    setSelectedProjectId(null);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <header className="bg-blue-600 text-white p-4 shadow-md flex items-center justify-between">
        <h1 className="text-3xl font-bold">Team Todo App</h1>
        {selectedProjectId && (
          <button
            onClick={handleBackToList}
            className="bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 px-4 rounded-md transition duration-300 ease-in-out"
          >
            ← Back to Projects
          </button>
        )}
      </header>

      <main className="flex-grow p-6">
        {selectedProjectId ? (
          <ProjectView projectId={selectedProjectId} onBackToList={handleBackToList} />
        ) : (
          <ProjectList onSelectProject={handleSelectProject} />
        )}
      </main>
    </div>
  );
}

export default App;