import React from 'react';

/**
 * @typedef {object} Calculation
 * @property {string} id
 * @property {string} sessionId
 * @property {string} expression
 * @property {number} result
 * @property {string} timestamp // ISO 8601 string
 */

/**
 * History component displays a list of past calculations.
 *
 * @param {object} props
 * @param {Calculation[]} props.history - An array of calculation objects to display.
 */
const History = ({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg shadow-inner text-gray-400 text-center text-sm">
        No history yet.
      </div>
    );
  }

  // Group history by session ID for better readability
  const groupedHistory = history.reduce((acc, calc) => {
    const date = new Date(calc.timestamp);
    const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    const timeKey = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const sessionKey = `${calc.sessionId}-${dateKey}`; // Group by session and date
    if (!acc[sessionKey]) {
      acc[sessionKey] = {
        sessionId: calc.sessionId,
        date: dateKey,
        calculations: []
      };
    }
    acc[sessionKey].calculations.push({ ...calc, displayTime: timeKey });
    return acc;
  }, {});

  // Sort sessions by the timestamp of their first calculation (most recent first)
  const sortedSessionKeys = Object.keys(groupedHistory).sort((a, b) => {
    const timeA = new Date(groupedHistory[a].calculations[0].timestamp);
    const timeB = new Date(groupedHistory[b].calculations[0].timestamp);
    return timeB.getTime() - timeA.getTime();
  });


  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-inner overflow-y-auto max-h-96">
      <h2 className="text-xl font-semibold text-white mb-4 border-b border-gray-700 pb-2">Calculation History</h2>
      {sortedSessionKeys.map(sessionKey => {
        const session = groupedHistory[sessionKey];
        return (
          <div key={sessionKey} className="mb-6 last:mb-0">
            <h3 className="text-md font-medium text-gray-300 mb-2">
              Session: <span className="font-normal text-gray-400">{session.date}</span>
            </h3>
            <ul className="space-y-2">
              {session.calculations.map((calc) => (
                <li key={calc.id} className="bg-gray-700 p-3 rounded-md flex justify-between items-center text-sm">
                  <div className="flex-1 pr-2">
                    <div className="text-gray-200 font-mono break-all">{calc.expression}</div>
                    <div className="text-green-400 font-bold text-lg break-all">= {calc.result}</div>
                  </div>
                  <div className="text-gray-400 text-xs flex-shrink-0">{calc.displayTime}</div>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
};

export default History;