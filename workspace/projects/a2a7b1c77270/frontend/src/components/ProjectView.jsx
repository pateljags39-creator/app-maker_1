import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../api';
import TaskCard from './TaskCard';
import TaskModal from './TaskModal';

function ProjectView({ onBackToList }) {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [users, setUsers] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [selectedStatusIdForNewTask, setSelectedStatusIdForNewTask] = useState(null);
  const [draggedTaskId, setDraggedTaskId] = useState(null);

  const fetchProjectData = useCallback(async () => {
    try {
      const projectData = await api.getProject(projectId);
      setProject(projectData);
      setTasks(projectData.tasks || []);
      setStatuses(projectData.statuses || []);
      const projectMetrics = await api.getProjectMetrics(projectId);
      setMetrics(projectMetrics);
    } catch (error) {
      console.error('Error fetching project data:', error);
      // Optionally navigate back or show an error message
    }
  }, [projectId]);

  const fetchUsers = useCallback(async () => {
    try {
      const usersData = await api.getUsers();
      setUsers(usersData);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  }, []);

  useEffect(() => {
    fetchProjectData();
    fetchUsers();
  }, [fetchProjectData, fetchUsers]);

  const handleAddTaskClick = (statusId = null) => {
    setEditingTask(null); // For creating a new task
    setSelectedStatusIdForNewTask(statusId);
    setShowTaskModal(true);
  };

  const handleEditTaskClick = (task) => {
    setEditingTask(task);
    setShowTaskModal(true);
  };

  const handleCloseTaskModal = () => {
    setShowTaskModal(false);
    setEditingTask(null);
    setSelectedStatusIdForNewTask(null);
  };

  const handleSaveTask = async (taskData) => {
    try {
      if (editingTask) {
        await api.updateTask(editingTask.id, taskData);
      } else {
        await api.createTask(projectId, taskData);
      }
      fetchProjectData();
      handleCloseTaskModal();
    } catch (error) {
      console.error('Error saving task:', error);
      alert('Failed to save task. Please try again.');
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await api.deleteTask(taskId);
        fetchProjectData();
      } catch (error) {
        console.error('Error deleting task:', error);
        alert('Failed to delete task. Please try again.');
      }
    }
  };

  const handleDragStart = (e, taskId) => {
    setDraggedTaskId(taskId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault(); // Necessary to allow dropping
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, targetStatusId) => {
    e.preventDefault();
    if (!draggedTaskId) return;

    const taskToUpdate = tasks.find(task => task.id === draggedTaskId);
    if (taskToUpdate && taskToUpdate.status_id !== targetStatusId) {
      try {
        await api.updateTask(draggedTaskId, { status_id: targetStatusId });
        fetchProjectData(); // Re-fetch all data to update the UI
      } catch (error) {
        console.error('Error updating task status:', error);
        alert('Failed to update task status. Please try again.');
      }
    }
    setDraggedTaskId(null);
  };

  if (!project) {
    return (
      <div className="flex justify-center items-center h-screen text-gray-600">
        Loading project...
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">{project.name}</h1>
        <button
          onClick={onBackToList}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Back to Projects
        </button>
      </div>

      <p className="text-gray-600 mb-6">{project.description}</p>

      {/* Project Metrics */}
      <div className="bg-white shadow-md rounded-lg p-4 mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Project Metrics</h2>
        {metrics ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-3 bg-blue-50 rounded-md">
              <p className="text-sm text-gray-500">Total Tasks</p>
              <p className="text-lg font-bold text-blue-800">{metrics.total_tasks}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-md">
              <p className="text-sm text-gray-500">Completed Tasks</p>
              <p className="text-lg font-bold text-green-800">{metrics.completed_tasks}</p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-md">
              <p className="text-sm text-gray-500">Avg. Cycle Time (days)</p>
              <p className="text-lg font-bold text-yellow-800">
                {metrics.average_cycle_time_days !== null ? metrics.average_cycle_time_days.toFixed(2) : 'N/A'}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">No metrics available yet.</p>
        )}
      </div>

      {/* Kanban Board */}
      <div className="flex space-x-4 overflow-x-auto pb-4">
        {statuses
          .sort((a, b) => a.id - b.id) // Ensure consistent order
          .map((status) => (
            <div
              key={status.id}
              className="flex-shrink-0 w-80 bg-gray-100 rounded-lg shadow-sm p-4"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, status.id)}
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-700">{status.name}</h3>
                <button
                  onClick={() => handleAddTaskClick(status.id)}
                  className="text-gray-500 hover:text-gray-700"
                  title={`Add task to ${status.name}`}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
              <div className="space-y-3 min-h-[100px]">
                {tasks
                  .filter((task) => task.status_id === status.id)
                  .sort((a, b) => new Date(a.created_at) - new Date(b.created_at)) // Sort tasks by creation date
                  .map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onEdit={handleEditTaskClick}
                      onDelete={handleDeleteTask}
                      onDragStart={handleDragStart}
                      assignee={users.find(u => u.id === task.assignee_id)}
                    />
                  ))}
                {tasks.filter((task) => task.status_id === status.id).length === 0 && (
                  <p className="text-gray-400 text-sm text-center py-4">No tasks in this column.</p>
                )}
              </div>
            </div>
          ))}
        <div className="flex-shrink-0 w-80 bg-gray-100 rounded-lg shadow-sm p-4 flex flex-col justify-center items-center">
          <button
            onClick={() => handleAddTaskClick()}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            Add New Task
          </button>
        </div>
      </div>

      {showTaskModal && (
        <TaskModal
          task={editingTask}
          projectId={projectId}
          statuses={statuses}
          users={users}
          onSave={handleSaveTask}
          onClose={handleCloseTaskModal}
          initialStatusId={selectedStatusIdForNewTask}
        />
      )}
    </div>
  );
}

export default ProjectView;