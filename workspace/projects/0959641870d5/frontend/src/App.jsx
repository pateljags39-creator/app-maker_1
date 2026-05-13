import React, { useState } from 'react';

function App() {
  const [display, setDisplay] = useState('0');
  const [currentInput, setCurrentInput] = useState(''); // The number currently being typed
  const [expression, setExpression] = useState([]); // Array of numbers and operators for PEMDAS evaluation
  const [error, setError] = useState(null);
  const [lastActionWasEquals, setLastActionWasEquals] = useState(false);

  const MAX_DISPLAY_LENGTH = 12; // Arbitrary limit for display to prevent overflow (R10)

  const resetState = () => {
    setDisplay('0');
    setCurrentInput('');
    setExpression([]);
    setError(null);
    setLastActionWasEquals(false);
  };

  const handleNumberClick = (num) => {
    if (error) {
      // If there's an error, clear it and start fresh with the new number
      resetState();
      // The new number will be processed after reset
    }

    if (lastActionWasEquals) {
      // If the last action was '=', start a new calculation
      setExpression([]);
      setCurrentInput('');
      setLastActionWasEquals(false);
    }

    if (num === '.' && currentInput.includes('.')) {
      return; // Prevent multiple decimal points (R8)
    }

    let newCurrentInput = currentInput + num;

    // Handle leading zero: if currentInput is '0' and num is not '.', replace '0'
    if (currentInput === '0' && num !== '.') {
      newCurrentInput = num;
    }

    if (newCurrentInput.length > MAX_DISPLAY_LENGTH) {
      setError('Error: Limit');
      setDisplay('Error: Limit');
      return;
    }

    setCurrentInput(newCurrentInput);
    setDisplay(newCurrentInput);
  };

  const handleOperatorClick = (op) => {
    if (error) return; // Do nothing if in an error state

    setLastActionWasEquals(false);

    let newExpression = [...expression];

    if (currentInput !== '') {
      const num = parseFloat(currentInput);
      if (isNaN(num)) {
        setError('Error: Invalid Num');
        setDisplay('Error: Invalid Num');
        return;
      }
      newExpression.push(num);
      setCurrentInput('');
    } else if (newExpression.length > 0 && typeof newExpression[newExpression.length - 1] === 'string') {
      // If the last item in expression is an operator, replace it with the new one
      newExpression[newExpression.length - 1] = op;
      setExpression(newExpression);
      setDisplay(newExpression.map(item => typeof item === 'number' ? item.toString() : item).join(' '));
      return;
    } else if (newExpression.length === 0) {
      // If no number entered yet, assume 0 for the first operand
      newExpression.push(0);
    }

    newExpression.push(op);
    setExpression(newExpression);
    setDisplay(newExpression.map(item => typeof item === 'number' ? item.toString() : item).join(' '));
  };

  // Implements PEMDAS logic (R14)
  const evaluateExpression = (exprArray) => {
    if (exprArray.length === 0) return 0;
    if (exprArray.length === 1 && typeof exprArray[0] === 'number') return exprArray[0];

    // Ensure expression doesn't end with an operator before evaluation
    if (typeof exprArray[exprArray.length - 1] === 'string') {
      return 'Error: Incomplete'; // Expression ends with an operator
    }

    let tempExpr = [...exprArray];

    // Pass 1: Multiplication and Division (R3, R4)
    for (let i = 0; i < tempExpr.length; i++) {
      if (tempExpr[i] === '*' || tempExpr[i] === '/') {
        const num1 = tempExpr[i - 1];
        const operator = tempExpr[i];
        const num2 = tempExpr[i + 1];

        if (typeof num1 !== 'number' || typeof num2 !== 'number') {
          return 'Error: Malformed'; // Invalid expression structure (R10)
        }

        let result;
        if (operator === '*') {
          result = num1 * num2;
        } else if (operator === '/') {
          if (num2 === 0) {
            return 'Error: DivByZero'; // Division by zero (R9)
          }
          result = num1 / num2;
        }

        // Replace num1, operator, num2 with the result
        tempExpr.splice(i - 1, 3, result);
        i -= 2; // Adjust index to re-evaluate from the new result's position
      }
    }

    // Pass 2: Addition and Subtraction (R1, R2)
    for (let i = 0; i < tempExpr.length; i++) {
      if (tempExpr[i] === '+' || tempExpr[i] === '-') {
        const num1 = tempExpr[i - 1];
        const operator = tempExpr[i];
        const num2 = tempExpr[i + 1];

        if (typeof num1 !== 'number' || typeof num2 !== 'number') {
          return 'Error: Malformed'; // Invalid expression structure (R10)
        }

        let result;
        if (operator === '+') {
          result = num1 + num2;
        } else if (operator === '-') {
          result = num1 - num2;
        }

        tempExpr.splice(i - 1, 3, result);
        i -= 2; // Adjust index
      }
    }

    if (tempExpr.length === 1 && typeof tempExpr[0] === 'number') {
      return tempExpr[0];
    } else {
      return 'Error: Calculation'; // Should not happen if expression is well-formed (R10)
    }
  };

  const handleEqualsClick = () => {
    if (error) return; // Do nothing if in an error state

    let finalExpression = [...expression];
    if (currentInput !== '') {
      const num = parseFloat(currentInput);
      if (isNaN(num)) {
        setError('Error: Invalid Num');
        setDisplay('Error: Invalid Num');
        return;
      }
      finalExpression.push(num);
    } else if (finalExpression.length > 0 && typeof finalExpression[finalExpression.length - 1] === 'string') {
      // If equals is pressed with an operator at the end and no current input, remove the trailing operator
      finalExpression.pop();
    }

    if (finalExpression.length === 0) {
      setDisplay('0');
      setCurrentInput('');
      setExpression([]);
      setLastActionWasEquals(true);
      return;
    }

    const result = evaluateExpression(finalExpression);

    if (typeof result === 'string' && result.startsWith('Error')) {
      setError(result);
      setDisplay(result);
      setCurrentInput('');
      setExpression([]);
    } else {
      let resultString = result.toString();

      // Handle results exceeding display limits (R10)
      if (resultString.length > MAX_DISPLAY_LENGTH) {
        // Try to fit by reducing precision or using scientific notation
        resultString = result.toPrecision(MAX_DISPLAY_LENGTH - 5);
        if (resultString.length > MAX_DISPLAY_LENGTH) {
          resultString = result.toExponential(MAX_DISPLAY_LENGTH - 7);
        }
      }
      if (resultString.length > MAX_DISPLAY_LENGTH || isNaN(result) || !isFinite(result)) {
        setError('Error: Overflow');
        setDisplay('Error: Overflow');
        setCurrentInput('');
        setExpression([]);
        return;
      }

      setDisplay(resultString);
      setCurrentInput(resultString); // Set currentInput to result for chaining operations
      setExpression([result]); // Start new expression with the result
      setLastActionWasEquals(true);
      setError(null);
    }
  };

  const handleClearClick = () => {
    resetState(); // Reset all state (R5)
  };

  // Define calculator buttons (R11)
  const buttons = [
    { value: 'C', type: 'clear' }, { value: '/', type: 'operator' }, { value: '*', type: 'operator' }, { value: '-', type: 'operator' },
    { value: '7', type: 'number' }, { value: '8', type: 'number' }, { value: '9', type: 'number' }, { value: '+', type: 'operator' },
    { value: '4', type: 'number' }, { value: '5', type: 'number' }, { value: '6', type: 'number' }, { value: '.', type: 'number' },
    { value: '1', type: 'number' }, { value: '2', type: 'number' }, { value: '3', type: 'number' }, { value: '=', type: 'equals' },
  ];

  const renderButton = (button) => (
    <button
      key={button.value}
      onClick={() => {
        if (button.type === 'number') {
          handleNumberClick(button.value);
        } else if (button.type === 'operator') {
          handleOperatorClick(button.value);
        } else if (button.type === 'clear') {
          handleClearClick();
        } else if (button.type === 'equals') {
          handleEqualsClick();
        }
      }}
      className={`p-4 text-2xl font-semibold rounded-lg shadow-md transition-all duration-100 ease-in-out
                  ${button.type === 'number' ? 'bg-gray-700 hover:bg-gray-600 active:bg-gray-500 text-white' : ''}
                  ${button.type === 'operator' ? 'bg-orange-500 hover:bg-orange-400 active:bg-orange-300 text-white' : ''}
                  ${button.type === 'clear' ? 'bg-red-600 hover:bg-red-500 active:bg-red-400 text-white' : ''}
                  ${button.type === 'equals' ? 'bg-blue-600 hover:bg-blue-500 active:bg-blue-400 text-white' : ''}
                  ${error && button.type !== 'clear' ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
      disabled={error && button.type !== 'clear'} // Disable buttons except 'C' when in error state
    >
      {button.value}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-md">
        {/* Calculator Display (R11) */}
        <div className="bg-gray-900 text-white text-right p-4 mb-4 rounded-lg text-4xl font-mono overflow-hidden h-20 flex items-center justify-end">
          {display}
        </div>
        {/* Calculator Buttons (R11) */}
        <div className="grid grid-cols-4 gap-3">
          {buttons.map(renderButton)}
        </div>
      </div>
    </div>
  );
}

export default App;