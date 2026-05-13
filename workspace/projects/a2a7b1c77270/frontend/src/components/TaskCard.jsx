import React from 'react';

const TaskCard = ({ task, onEditTask }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'No due date';
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 cursor-pointer border border-gray-200"
      onClick={() => onEditTask(task)}
    >
      <h3 className="text-md font-semibold text-gray-800 mb-2">{task.title}</h3>
      {task.description && (
        <p className="text-sm text-gray-600 mb-2 line-clamp-2">{task.description}</p>
      )}
      <div className="flex flex-col space-y-1 text-sm text-gray-500">
        {task.assignee && (
          <div className="flex items-center">
            <span className="material-icons-outlined text-base mr-1">person</span>
            <span>{task.assignee.email.split('@')[0]}</span>
          </div>
        )}
        {task.due_date && (
          <div className="flex items-center">
            <span className="material-icons-outlined text-base mr-1">event</span>
            <span>{formatDate(task.due_date)}</span>
          </div>
        )}
        {task.priority && (
          <div className="flex items-center">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
              {task.priority}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskCard;