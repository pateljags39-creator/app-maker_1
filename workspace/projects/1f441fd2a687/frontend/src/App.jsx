import React, { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Calculator from './components/Calculator';
import History from './components/History';
import { saveCalculation, getCalculations } from './api';

const LOCAL_STORAGE_CURRENT_SESSION_ID_KEY = 'web-calculator-pro-current-session-id';
const LOCAL_STORAGE_RECENT_SESSION_IDS_KEY = 'web-calculator-pro-recent-session-ids';
const MAX_RECENT_SESSIONS = 3;

function App() {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [recentSessionIds, setRecentSessionIds] = useState([]);
  const [calculationHistory, setCalculationHistory] = useState([]);

  // Effect to initialize session IDs on component mount
  useEffect(() => {
    let storedCurrentSessionId = localStorage.getItem(LOCAL_STORAGE_CURRENT_SESSION_ID_KEY);
    let storedRecentSessionIds = JSON.parse(localStorage.getItem(LOCAL_STORAGE_RECENT_SESSION_IDS_KEY) || '[]');

    if (!storedCurrentSessionId) {
      // No current session ID, generate a new one
      storedCurrentSessionId = uuidv4();
      localStorage.setItem(LOCAL_STORAGE_CURRENT_SESSION_ID_KEY, storedCurrentSessionId);
    }

    // Ensure the current session ID is in the recent list and keep it trimmed
    // Add current session ID to the front if not already present
    if (!storedRecentSessionIds.includes(storedCurrentSessionId)) {
      storedRecentSessionIds = [storedCurrentSessionId, ...storedRecentSessionIds];
    }
    // Filter out any duplicates and trim to MAX_RECENT_SESSIONS
    storedRecentSessionIds = Array.from(new Set(storedRecentSessionIds)).slice(0, MAX_RECENT_SESSIONS);
    
    localStorage.setItem(LOCAL_STORAGE_RECENT_SESSION_IDS_KEY, JSON.stringify(storedRecentSessionIds));

    setCurrentSessionId(storedCurrentSessionId);
    setRecentSessionIds(storedRecentSessionIds);
  }, []); // Run only once on mount

  // Function to fetch history, memoized to prevent unnecessary re-creations
  const fetchHistory = useCallback(async () => {
    if (recentSessionIds.length > 0) {
      try {
        const sessionIdsParam = recentSessionIds.join(',');
        const history = await getCalculations(sessionIdsParam);
        setCalculationHistory(history);
      } catch (error) {
        console.error('Failed to fetch calculation history:', error);
        setCalculationHistory([]); // Clear history on error
      }
    } else {
      setCalculationHistory([]);
    }
  }, [recentSessionIds]); // Recreate if recentSessionIds changes

  // Effect to fetch history whenever recentSessionIds changes (via fetchHistory dependency)
  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]); // Dependency on fetchHistory (which itself depends on recentSessionIds)

  // Callback for when a calculation is completed and needs to be saved
  const handleSaveCalculation = useCallback(async (expression, result) => {
    if (!currentSessionId) {
      console.error('Cannot save calculation: currentSessionId is not set.');
      return;
    }
    try {
      await saveCalculation({ sessionId: currentSessionId, expression, result });
      // After saving, refetch the history to update the display
      await fetchHistory();
    } catch (error) {
      console.error('Failed to save calculation:', error);
    }
  }, [currentSessionId, fetchHistory]); // Recreate if currentSessionId or fetchHistory changes

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold mb-8 text-blue-400">Web Calculator Pro</h1>
      <div className="flex flex-col lg:flex-row gap-8 w-full max-w-6xl">
        <div className="flex-1">
          <Calculator onSaveCalculation={handleSaveCalculation} />
        </div>
        <div className="flex-1">
          <History history={calculationHistory} />
        </div>
      </div>
    </div>
  );
}

export default App;