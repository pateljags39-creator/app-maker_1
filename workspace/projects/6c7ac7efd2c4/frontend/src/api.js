const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetches the persisted calculator state from the backend.
 * @returns {Promise<{memory_register: number, history_log: Array<{expression: string, result: string}>}>}
 */
export const getCalculatorState = async () => {
  try {
    const response = await fetch(`${BASE_URL}/api/calculator-state`);
    if (!response.ok) {
      if (response.status === 404) {
        // No state found, return initial state equivalent
        return { memory_register: 0, history_log: [] };
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return {
      memory_register: data.memory_register,
      history_log: data.history_log ? JSON.parse(data.history_log) : [],
    };
  } catch (error) {
    console.error("Error fetching calculator state:", error);
    // Return a default/initial state on error to allow the app to function
    return { memory_register: 0, history_log: [] };
  }
};

/**
 * Saves the current calculator state to the backend.
 * @param {number} memory_register - The current value of the memory register.
 * @param {Array<{expression: string, result: string}>} history_log - The calculation history.
 * @returns {Promise<void>}
 */
export const saveCalculatorState = async (memory_register, history_log) => {
  try {
    const response = await fetch(`${BASE_URL}/api/calculator-state`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        memory_register: memory_register,
        history_log: JSON.stringify(history_log), // Stringify the history array
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    // Optionally, parse and return data if the backend sends a confirmation
    // const data = await response.json();
    // console.log("Calculator state saved:", data);
  } catch (error) {
    console.error("Error saving calculator state:", error);
  }
};