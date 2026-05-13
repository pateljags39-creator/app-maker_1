import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_BASE = `${BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

export const api = {
  base: API_BASE,
  // system
  health: () => client.get('/system/health').then(r => r.data),
  // projects
  listProjects: () => client.get('/projects').then(r => r.data),
  createProject: (data) => client.post('/projects', data).then(r => r.data),
  getProject: (id) => client.get(`/projects/${id}`).then(r => r.data),
  deleteProject: (id) => client.delete(`/projects/${id}`).then(r => r.data),
  // BRD
  getBrd: (id) => client.get(`/projects/${id}/brd`).then(r => r.data),
  generateQuestions: (id) => client.post(`/projects/${id}/brd/questions`).then(r => r.data),
  submitAnswers: (id, answers) => client.post(`/projects/${id}/brd/answers`, { answers }).then(r => r.data),
  // architecture
  getArchitecture: (id) => client.get(`/projects/${id}/architecture`).then(r => r.data),
  detectArchitecture: (id) => client.post(`/projects/${id}/architecture/detect`).then(r => r.data),
  overrideArchitecture: (id, body) => client.post(`/projects/${id}/architecture/override`, body).then(r => r.data),
  // plan
  getPlan: (id) => client.get(`/projects/${id}/plan`).then(r => r.data),
  makePlan: (id) => client.post(`/projects/${id}/plan`).then(r => r.data),
  // generate
  triggerGenerate: (id) => client.post(`/projects/${id}/generate`).then(r => r.data),
  generateStatus: (id) => client.get(`/projects/${id}/generate/status`).then(r => r.data),
  // files
  listFiles: (id) => client.get(`/projects/${id}/files`).then(r => r.data),
  fileContent: (id, path) => client.get(`/projects/${id}/files/content`, { params: { path } }).then(r => r.data),
  // build
  triggerBuild: (id) => client.post(`/projects/${id}/build`).then(r => r.data),
  listBuilds: (id) => client.get(`/projects/${id}/builds`).then(r => r.data),
  // acceptance
  runAcceptance: (id) => client.post(`/projects/${id}/acceptance`).then(r => r.data),
  latestAcceptance: (id) => client.get(`/projects/${id}/acceptance`).then(r => r.data),
  // export
  makeExport: (id) => client.post(`/projects/${id}/export`).then(r => r.data),
  latestExport: (id) => client.get(`/projects/${id}/export`).then(r => r.data),
  exportManifest: (id) => client.get(`/projects/${id}/export/manifest`).then(r => r.data),
  exportDownloadUrl: (id) => `${API_BASE}/projects/${id}/export/download`,
  // events
  listEvents: (id, limit = 50) => client.get(`/projects/${id}/events`, { params: { limit } }).then(r => r.data),
  eventsStreamUrl: (id) => `${API_BASE}/projects/${id}/events/stream`,
};

export default api;
