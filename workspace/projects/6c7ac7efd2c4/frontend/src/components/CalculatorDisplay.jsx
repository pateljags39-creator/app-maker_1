import React from 'react';

/**
 * CalculatorDisplay component
 * Displays the current mathematical expression and the current input/result.
 *
 * @param {object} props - The component props.
 * @param {string} props.currentExpression - The full mathematical expression being built.
 * @param {string} props.currentInput - The currently typed number or the active real-time result.
 * @param {boolean} props.isErrorState - Indicates if an error message is currently displayed.
 */
const CalculatorDisplay = ({ currentExpression, currentInput, isErrorState }) => {
  return (
    <div className="calculator-display" aria-live="polite" aria-atomic="true">
      <div
        className="display-expression"
        role="status"
        aria-label="Current expression"
        data-testid="display-expression"
      >
        {currentExpression || ' '} {/* Display a space if empty to maintain height */}
      </div>
      <div
        className={`display-input ${isErrorState ? 'error' : ''}`}
        role="status"
        aria-label="Current input or result"
        data-testid="display-input"
      >
        {currentInput || '0'} {/* Display '0' if currentInput is empty */}
      </div>
    </div>
  );
};

export default CalculatorDisplay;