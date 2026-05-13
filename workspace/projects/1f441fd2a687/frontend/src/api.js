import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Saves a new calculation to the backend.
 * @param {object} calculationData - The calculation data to save.
 * @param {string} calculationData.sessionId - The ID of the current session.
 * @param {string} calculationData.expression - The mathematical expression.
 * @param {number} calculationData.result - The result of the calculation.
 * @returns {Promise<object>} The saved calculation object from the backend.
 */
export const saveCalculation = async (calculationData) => {
  try {
    const response = await api.post('/api/calculations', calculationData);
    return response.data;
  } catch (error) {
    console.error('Error saving calculation:', error);
    throw error;
  }
};

/**
 * Fetches calculation history for a given list of session IDs.
 * @param {string[]} sessionIds - An array of session IDs to fetch history for.
 * @returns {Promise<object[]>} An array of calculation objects.
 */
export const fetchCalculationHistory = async (sessionIds) => {
  try {
    if (!sessionIds || sessionIds.length === 0) {
      return [];
    }
    const queryString = sessionIds.join(',');
    const response = await api.get(`/api/calculations?session_ids=${queryString}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching calculation history:', error);
    throw error;
  }
};


// AUTO-STUB: missing named exports added by Local App Creator post-fixup.
// Each missing symbol below is either aliased to a same-file export with
// a similar name + verb category, or it throws loudly so the bug isn't
// silently swallowed at runtime.
// `getCalculations` aliased to `fetchCalculationHistory` (best-guess match, score=1.04). Replace if wrong.
export const getCalculations = fetchCalculationHistory;
