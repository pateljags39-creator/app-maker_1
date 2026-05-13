const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Saves a new calculation to the backend history.
 * @param {object} calculationData - The calculation data to save.
 * @param {string} calculationData.session_id - The ID of the user session.
 * @param {string} calculationData.expression - The mathematical expression.
 * @param {string} calculationData.result - The result of the calculation.
 * @returns {Promise<object>} The saved calculation object from the backend.
 * @throws {Error} If the API call fails.
 */
export async function saveCalculation(calculationData) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/calculations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(calculationData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error saving calculation:', error);
    throw error;
  }
}

/**
 * Fetches the calculation history from the backend.
 * @returns {Promise<Array<object>>} An array of calculation history objects.
 * @throws {Error} If the API call fails.
 */
export async function fetchHistory() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/calculations/history`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching history:', error);
    throw error;
  }
}