import React, { useState, useEffect } from 'react';
import { getProjects, createProject, getUsers } from '../api';

function ProjectList({ onSelectProject }) {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectOwnerId, setNewProjectOwnerId] = useState('');
  const [newProjectStartDate, setNewProjectStartDate] = useState('');
  const [newProjectEndDate, setNewProjectEndDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      setError('Failed to fetch projects.');
      console.error('Error fetching projects:', err);
    }
  };

  const fetchUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (err) {
      setError('Failed to fetch users.');
      console.error('Error fetching users:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchProjects(), fetchUsers()]);
      setLoading(false);
    };
    loadData();
  }, []);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName || !newProjectOwnerId) {
      alert('Project name and owner are required.');
      return;
    }

    try {
      const newProject = {
        name: newProjectName,
        description: newProjectDescription,
        owner_id: parseInt(newProjectOwnerId, 10),
        start_date: newProjectStartDate || null,
        end_date: newProjectEndDate || null,
      };
      await createProject(newProject);
      await fetchProjects(); // Refresh the list
      // Clear form fields
      setNewProjectName('');
      setNewProjectDescription('');
      setNewProjectOwnerId('');
      setNewProjectStartDate('');
      setNewProjectEndDate('');
    } catch (err) {
      setError('Failed to create project.');
      console.error('Error creating project:', err);
    }
  };

  if (loading) {
    return <div className="text-center p-4">Loading projects...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Projects</h1>

      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-4 text-gray-700">Create New Project</h2>
        <form onSubmit={handleCreateProject} className="space-y-4">
          <div>
            <label htmlFor="projectName" className="block text-sm font-medium text-gray-700">
              Project Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="projectName"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="projectDescription" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="projectDescription"
              rows="3"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
            ></textarea>
          </div>
          <div>
            <label htmlFor="projectOwner" className="block text-sm font-medium text-gray-700">
              Owner <span className="text-red-500">*</span>
            </label>
            <select
              id="projectOwner"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
              value={newProjectOwnerId}
              onChange={(e) => setNewProjectOwnerId(e.target.value)}
              required
            >
              <option value="">Select an owner</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.email}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="projectStartDate" className="block text-sm font-medium text-gray-700">
                Start Date
              </label>
              <input
                type="date"
                id="projectStartDate"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
                value={newProjectStartDate}
                onChange={(e) => setNewProjectStartDate(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="projectEndDate" className="block text-sm font-medium text-gray-700">
                End Date
              </label>
              <input
                type="date"
                id="projectEndDate"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
                value={newProjectEndDate}
                onChange={(e) => setNewProjectEndDate(e.target.value)}
              />
            </div>
          </div>
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Create Project
          </button>
        </form>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-700">Existing Projects</h2>
        {projects.length === 0 ? (
          <p className="text-gray-600">No projects found. Create one above!</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {projects.map((project) => (
              <li
                key={project.id}
                className="py-4 flex justify-between items-center hover:bg-gray-50 cursor-pointer"
                onClick={() => onSelectProject(project.id)}
              >
                <div>
                  <p className="text-lg font-medium text-gray-900">{project.name}</p>
                  <p className="text-sm text-gray-500">{project.description}</p>
                </div>
                <button
                  className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent li onClick from firing
                    onSelectProject(project.id);
                  }}
                >
                  View Details
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ProjectList;