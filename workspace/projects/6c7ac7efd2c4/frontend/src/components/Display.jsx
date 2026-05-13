import React from 'react';

/**
 * Display component for the calculator.
 * Shows the current expression being built and the current input/result.
 *
 * @param {object} props - The component props.
 * @param {string} props.currentExpression - The full mathematical expression being built.
 * @param {string} props.currentInput - The currently typed number or the active real-time result.
 * @param {boolean} props.isErrorState - True if an error message is currently displayed.
 */
const Display = ({ currentExpression, currentInput, isErrorState }) => {
  return (
    <div className="calculator-display">
      <div
        className="display-expression"
        aria-label="Current expression"
        aria-live="polite"
        aria-atomic="true"
      >
        {currentExpression || ''}
      </div>
      <div
        className={`display-input ${isErrorState ? 'error-state' : ''}`}
        aria-label="Current input or result"
        aria-live="assertive"
        aria-atomic="true"
      >
        {currentInput || '0'}
      </div>
    </div>
  );
};

export default Display;