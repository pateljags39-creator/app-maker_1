const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchReport(sector, market) {
  const params = new URLSearchParams();
  if (sector) params.append('sector', sector);
  if (market) params.append('market', market);

  const url = `${API_BASE_URL}/api/report?${params.toString()}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errorMessage = `Error fetching report: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch (e) {
      // Ignore JSON parse errors for non-JSON error responses
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

// AUTO-STUB: missing named exports added by Local App Creator post-fixup.
// Each missing symbol below is either aliased to a same-file export with
// a similar name + verb category, or it throws loudly so the bug isn't
// silently swallowed at runtime.
export const fetchReport = (...args) => { throw new Error("Local App Creator: missing implementation for 'fetchReport'. Replace this auto-stub with the real function."); };
