import React from 'react';

/**
 * Renders a panel displaying the history of calculations.
 *
 * @param {object} props - The component props.
 * @param {Array<{expression: string, result: string}>} props.historyLog - An array of calculation history entries.
 */
const HistoryPanel = ({ historyLog }) => {
  return (
    <div className="history-panel" role="region" aria-labelledby="history-heading">
      {/* Visually hidden heading for screen reader context */}
      <h2 id="history-heading" className="sr-only">Calculation History</h2>

      {historyLog && historyLog.length > 0 ? (
        <ul className="history-list" aria-label="List of past calculations">
          {/* Display newest calculations first by reversing the log for display purposes */}
          {historyLog.slice().reverse().map((entry, index) => (
            <li key={index} className="history-item">
              {/* The expression part of the history entry */}
              <span className="history-expression" aria-hidden="true">{entry.expression}</span>
              {/* The result part, with an explicit aria-label for screen readers */}
              <span className="history-result" role="status" aria-label={`Result: ${entry.result}`}>{entry.result}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="history-empty" aria-live="polite">
          No history yet. Calculations will appear here.
        </p>
      )}
    </div>
  );
};

export default HistoryPanel;