const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function callApi(endpoint, method = 'GET', data = null) {
  const url = `${BASE_URL}${endpoint}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API error: ${response.status} ${response.statusText}`);
    }
    // For DELETE requests or responses with no content, return null or a success indicator
    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`Error calling API endpoint ${endpoint}:`, error);
    throw error;
  }
}

// User API calls
export const getUsers = async () => {
  return callApi('/api/users');
};

// Project API calls
export const getProjects = async () => {
  return callApi('/api/projects');
};

export const createProject = async (projectData) => {
  return callApi('/api/projects', 'POST', projectData);
};

export const getProjectDetails = async (projectId) => {
  return callApi(`/api/projects/${projectId}`);
};

// Task API calls
export const createTask = async (projectId, taskData) => {
  return callApi(`/api/projects/${projectId}/tasks`, 'POST', taskData);
};

export const updateTask = async (taskId, taskData) => {
  return callApi(`/api/tasks/${taskId}`, 'PUT', taskData);
};

export const deleteTask = async (taskId) => {
  return callApi(`/api/tasks/${taskId}`, 'DELETE');
};

// Status API calls
export const createStatus = async (projectId, statusData) => {
  return callApi(`/api/projects/${projectId}/statuses`, 'POST', statusData);
};

// Comment API calls
export const getTaskComments = async (taskId) => {
  return callApi(`/api/tasks/${taskId}/comments`);
};

export const addTaskComment = async (taskId, commentData) => {
  return callApi(`/api/tasks/${taskId}/comments`, 'POST', commentData);
};

// Metrics API calls
export const getProjectMetrics = async (projectId) => {
  return callApi(`/api/projects/${projectId}/metrics`);
};