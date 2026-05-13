import React, { useState } from 'react';
import Display from './Display';
import Button from './Button';

const Calculator = () => {
  const [displayValue, setDisplayValue] = useState('0');
  const [firstOperand, setFirstOperand] = useState(null);
  const [operator, setOperator] = useState(null);
  const [waitingForSecondOperand, setWaitingForSecondOperand] = useState(false);

  // Object to hold calculation functions
  const calculate = {
    '/': (prevValue, nextValue) => prevValue / nextValue,
    '*': (prevValue, nextValue) => prevValue * nextValue,
    '+': (prevValue, nextValue) => prevValue + nextValue,
    '-': (prevValue, nextValue) => prevValue - nextValue,
  };

  // Handles digit (0-9) input
  const inputDigit = (digit) => {
    if (displayValue === 'Error') {
      // If in error state, clear it and start a new number
      setDisplayValue(digit);
      setFirstOperand(null);
      setOperator(null);
      setWaitingForSecondOperand(false);
      return;
    }
    if (waitingForSecondOperand) {
      // If waiting for the second operand, replace the display with the new digit
      setDisplayValue(digit);
      setWaitingForSecondOperand(false);
    } else {
      // Otherwise, append the digit to the current display value
      // If display is '0', replace it; otherwise, concatenate
      setDisplayValue(displayValue === '0' ? digit : displayValue + digit);
    }
  };

  // Handles decimal point input
  const inputDecimal = () => {
    if (displayValue === 'Error') {
      // If in error state, clear it and start with '0.'
      setDisplayValue('0.');
      setFirstOperand(null);
      setOperator(null);
      setWaitingForSecondOperand(false);
      return;
    }
    if (waitingForSecondOperand) {
      // If waiting for second operand, start with '0.'
      setDisplayValue('0.');
      setWaitingForSecondOperand(false);
      return;
    }
    // Only add a decimal if one isn't already present
    if (!displayValue.includes('.')) {
      setDisplayValue(displayValue + '.');
    }
  };

  // Resets the calculator to its initial state
  const clearAll = () => {
    setDisplayValue('0');
    setFirstOperand(null);
    setOperator(null);
    setWaitingForSecondOperand(false);
  };

  // Handles operator (+, -, *, /) input
  const handleOperator = (nextOperator) => {
    const inputValue = parseFloat(displayValue);

    if (displayValue === 'Error') {
      // If currently in error state, clear it and prepare for a new calculation
      // The inputValue will be NaN, which will be handled if used in calculation
      setFirstOperand(inputValue);
      setOperator(nextOperator);
      setWaitingForSecondOperand(true);
      setDisplayValue('0'); // Reset display to '0' after error
      return;
    }

    if (firstOperand === null) {
      // If no first operand is set, store the current display value as the first operand
      setFirstOperand(inputValue);
    } else if (operator) {
      // If there's a pending operator and a first operand, perform the previous calculation
      // This handles chaining operations like "5 + 3 * 2"
      const prevValue = firstOperand;
      const nextValue = inputValue;

      // Handle division by zero
      if (operator === '/' && nextValue === 0) {
        setDisplayValue('Error');
        setFirstOperand(null);
        setOperator(null);
        setWaitingForSecondOperand(false);
        return;
      }

      const result = calculate[operator](prevValue, nextValue);
      // Handle potential NaN or Infinity results (e.g., 0/0, 1/0)
      if (isNaN(result) || !isFinite(result)) {
        setDisplayValue('Error');
        setFirstOperand(null);
        setOperator(null);
        setWaitingForSecondOperand(false);
        return;
      }
      setDisplayValue(String(result));
      setFirstOperand(result); // The result becomes the new first operand for further chaining
    }

    setWaitingForSecondOperand(true); // Next digit input should start a new number
    setOperator(nextOperator); // Set the new operator
  };

  // Handles the equals (=) button
  const handleEquals = () => {
    // Only perform calculation if there's a first operand and a pending operator
    if (firstOperand === null || operator === null) {
      return;
    }

    const inputValue = parseFloat(displayValue);
    const prevValue = firstOperand;
    const currentOperator = operator; // Use the current operator for calculation

    // Handle division by zero for the final calculation
    if (currentOperator === '/' && inputValue === 0) {
      setDisplayValue('Error');
      setFirstOperand(null);
      setOperator(null);
      setWaitingForSecondOperand(false);
      return;
    }

    const result = calculate[currentOperator](prevValue, inputValue);
    // Handle potential NaN or Infinity results
    if (isNaN(result) || !isFinite(result)) {
      setDisplayValue('Error');
      setFirstOperand(null);
      setOperator(null);
      setWaitingForSecondOperand(false);
      return;
    }

    setDisplayValue(String(result)); // Display the result
    setFirstOperand(null); // Reset for a new calculation
    setOperator(null);
    setWaitingForSecondOperand(false);
  };

  return (
    <div className="calculator bg-gray-800 p-4 rounded-lg shadow-xl max-w-xs mx-auto mt-10">
      <Display value={displayValue} />
      <div className="calculator-grid grid grid-cols-4 gap-2 mt-4">
        {/* Clear button */}
        <Button onClick={clearAll} className="col-span-3 bg-red-500 hover:bg-red-600">C</Button>
        {/* Division operator */}
        <Button onClick={() => handleOperator('/')} className="bg-orange-500 hover:bg-orange-600">/</Button>

        {/* Number buttons */}
        <Button onClick={() => inputDigit('7')}>7</Button>
        <Button onClick={() => inputDigit('8')}>8</Button>
        <Button onClick={() => inputDigit('9')}>9</Button>
        {/* Multiplication operator */}
        <Button onClick={() => handleOperator('*')} className="bg-orange-500 hover:bg-orange-600">*</Button>

        <Button onClick={() => inputDigit('4')}>4</Button>
        <Button onClick={() => inputDigit('5')}>5</Button>
        <Button onClick={() => inputDigit('6')}>6</Button>
        {/* Subtraction operator */}
        <Button onClick={() => handleOperator('-')} className="bg-orange-500 hover:bg-orange-600">-</Button>

        <Button onClick={() => inputDigit('1')}>1</Button>
        <Button onClick={() => inputDigit('2')}>2</Button>
        <Button onClick={() => inputDigit('3')}>3</Button>
        {/* Addition operator */}
        <Button onClick={() => handleOperator('+')} className="bg-orange-500 hover:bg-orange-600">+</Button>

        {/* Zero and Decimal */}
        <Button onClick={() => inputDigit('0')} className="col-span-2">0</Button>
        <Button onClick={inputDecimal}>.</Button>
        {/* Equals button */}
        <Button onClick={handleEquals} className="bg-green-500 hover:bg-green-600">=</Button>
      </div>
    </div>
  );
};

export default Calculator;