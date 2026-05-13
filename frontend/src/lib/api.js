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
  runFullPipeline: (id) => client.post(`/projects/${id}/run_full_pipeline`).then(r => r.data),
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
  // Robust blob download (works cross-origin, bypasses anchor `download` quirks).
  downloadExportZip: async (id, filename) => {
    const r = await client.get(`/projects/${id}/export/download`, { responseType: 'blob' });
    const blob = new Blob([r.data], { type: 'application/zip' });
    // Try to extract filename from Content-Disposition; fall back to provided name.
    const cd = r.headers?.['content-disposition'] || r.headers?.['Content-Disposition'] || '';
    let name = filename || `project-${id}.zip`;
    const m = cd.match(/filename\*?=(?:UTF-\d''|")?([^";\n]+)/i);
    if (m) {
      try { name = decodeURIComponent(m[1].replace(/^"|"$/g, '')); } catch { /* keep fallback */ }
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return { filename: name, size: blob.size };
  },
  // constraints (bounded customization)
  getConstraints: (id) => client.get(`/projects/${id}/constraints`).then(r => r.data),
  putConstraints: (id, constraints) => client.put(`/projects/${id}/constraints`, { constraints }).then(r => r.data),
  resetConstraints: (id) => client.post(`/projects/${id}/constraints/reset`).then(r => r.data),
  // improve / fix
  requestImprove: (id, change_request) => client.post(`/projects/${id}/improve`, { change_request }, { timeout: 180000 }).then(r => r.data),
  listImproves: (id) => client.get(`/projects/${id}/improve`).then(r => r.data),
  getImprove: (id, attemptId) => client.get(`/projects/${id}/improve/${attemptId}`).then(r => r.data),
  // events
  listEvents: (id, limit = 50) => client.get(`/projects/${id}/events`, { params: { limit } }).then(r => r.data),
  eventsStreamUrl: (id) => `${API_BASE}/projects/${id}/events/stream`,
  // recovery — unstick a project frozen in Generating/Building/Repair/Acceptance
  recoverProject: (id) => client.post(`/projects/${id}/recover`).then(r => r.data),
  // sandbox — run a generated project so the user can demo it
  sandboxStart: (id) => client.post(`/projects/${id}/sandbox/start`, {}, { timeout: 30000 }).then(r => r.data),
  sandboxStop: (id) => client.post(`/projects/${id}/sandbox/stop`).then(r => r.data),
  sandboxStatus: (id) => client.get(`/projects/${id}/sandbox/status`).then(r => r.data),
  sandboxLogs: (id, lines = 120) => client.get(`/projects/${id}/sandbox/logs`, { params: { lines } }).then(r => r.data),
  sandboxIframeSrc: (id) => `${API_BASE}/sandbox/${id}/`,
};

export default api;
