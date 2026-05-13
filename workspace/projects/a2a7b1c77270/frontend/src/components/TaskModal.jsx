import React, { useState, useEffect } from 'react';

const TaskModal = ({ isOpen, onClose, projectId, task, onSave, users, statuses }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status_id: '',
    due_date: '',
    assignee_id: '',
    priority: 'Medium',
  });

  const isEditMode = !!task;

  useEffect(() => {
    if (isOpen) {
      if (isEditMode) {
        setFormData({
          title: task.title || '',
          description: task.description || '',
          status_id: task.status_id || (statuses.length > 0 ? statuses[0].id : ''),
          due_date: task.due_date ? new Date(task.due_date).toISOString().split('T')[0] : '',
          assignee_id: task.assignee_id || (users.length > 0 ? users[0].id : ''),
          priority: task.priority || 'Medium',
        });
      } else {
        // Reset for new task
        setFormData({
          title: '',
          description: '',
          status_id: statuses.length > 0 ? statuses[0].id : '',
          due_date: '',
          assignee_id: users.length > 0 ? users[0].id : '',
          priority: 'Medium',
        });
      }
    }
  }, [isOpen, task, isEditMode, users, statuses]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      project_id: projectId, // Always include project_id for context
      status_id: parseInt(formData.status_id),
      assignee_id: formData.assignee_id ? parseInt(formData.assignee_id) : null,
      // Convert due_date to ISO string if it exists
      due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
    };

    await onSave(payload, task?.id); // Pass task.id if in edit mode
    onClose();
  };

  if (!isOpen) return null;

  const priorityOptions = ['Low', 'Medium', 'High'];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">
          {isEditMode ? 'Edit Task' : 'Create New Task'}
        </h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Title
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            ></textarea>
          </div>

          <div className="mb-4">
            <label htmlFor="status_id" className="block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              id="status_id"
              name="status_id"
              value={formData.status_id}
              onChange={handleChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              required
            >
              {statuses.map((status) => (
                <option key={status.id} value={status.id}>
                  {status.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="assignee_id" className="block text-sm font-medium text-gray-700">
              Assignee
            </label>
            <select
              id="assignee_id"
              name="assignee_id"
              value={formData.assignee_id}
              onChange={handleChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">Unassigned</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.email}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="due_date" className="block text-sm font-medium text-gray-700">
              Due Date
            </label>
            <input
              type="date"
              id="due_date"
              name="due_date"
              value={formData.due_date}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="mb-6">
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
              Priority
            </label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {priorityOptions.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isEditMode ? 'Save Changes' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TaskModal;