import React, { useState, useEffect, useCallback } from 'react';
import Button from './Button';

const Calculator = ({ onSaveCalculation }) => {
  const [displayValue, setDisplayValue] = useState('0');
  const [firstOperand, setFirstOperand] = useState(null);
  const [operator, setOperator] = useState(null);
  const [waitingForSecondOperand, setWaitingForSecondOperand] = useState(false);
  const [memory, setMemory] = useState(0);
  const [error, setError] = useState(null);
  const [currentExpression, setCurrentExpression] = useState('');

  const clearAll = useCallback(() => {
    setDisplayValue('0');
    setFirstOperand(null);
    setOperator(null);
    setWaitingForSecondOperand(false);
    setError(null);
    setCurrentExpression('');
  }, []);

  const clearEntry = useCallback(() => {
    if (error) {
      clearAll();
      return;
    }
    setDisplayValue('0');
  }, [clearAll, error]);

  const inputDigit = useCallback((digit) => {
    if (error) {
      clearAll();
      return;
    }
    if (waitingForSecondOperand) {
      setDisplayValue(String(digit));
      setWaitingForSecondOperand(false);
    } else {
      setDisplayValue(displayValue === '0' ? String(digit) : displayValue + digit);
    }
  }, [displayValue, waitingForSecondOperand, error, clearAll]);

  const inputDecimal = useCallback(() => {
    if (error) {
      clearAll();
      return;
    }
    if (waitingForSecondOperand) {
      setDisplayValue('0.');
      setWaitingForSecondOperand(false);
      return;
    }
    if (!displayValue.includes('.')) {
      setDisplayValue(displayValue + '.');
    }
  }, [displayValue, waitingForSecondOperand, error, clearAll]);

  const performCalculation = useCallback((prevOperand, nextOperand, op) => {
    switch (op) {
      case '+':
        return prevOperand + nextOperand;
      case '-':
        return prevOperand - nextOperand;
      case '*':
        return prevOperand * nextOperand;
      case '/':
        if (nextOperand === 0) {
          setError('Error: Div by zero');
          return NaN;
        }
        return prevOperand / nextOperand;
      default:
        return nextOperand;
    }
  }, []);

  const handleOperator = useCallback((nextOperator) => {
    if (error) {
      clearAll();
      return;
    }

    const inputValue = parseFloat(displayValue);

    if (firstOperand === null) {
      setFirstOperand(inputValue);
      setCurrentExpression(displayValue + ' ' + nextOperator);
    } else if (operator) {
      const result = performCalculation(firstOperand, inputValue, operator);
      if (isNaN(result)) {
        return; // Error already set
      }
      setDisplayValue(String(result));
      setFirstOperand(result);
      setCurrentExpression(result + ' ' + nextOperator);
    }

    setWaitingForSecondOperand(true);
    setOperator(nextOperator);
  }, [displayValue, firstOperand, operator, performCalculation, error, clearAll]);

  const handleEquals = useCallback(() => {
    if (error) {
      clearAll();
      return;
    }
    if (firstOperand === null || operator === null) {
      return; // No pending operation
    }

    const inputValue = parseFloat(displayValue);
    const result = performCalculation(firstOperand, inputValue, operator);

    if (isNaN(result)) {
      return; // Error already set
    }

    const fullExpression = `${currentExpression} ${inputValue}`;
    setDisplayValue(String(result));
    setFirstOperand(null);
    setOperator(null);
    setWaitingForSecondOperand(false);
    setCurrentExpression(''); // Clear expression after calculation

    // Save calculation to history
    onSaveCalculation(fullExpression, result);
  }, [displayValue, firstOperand, operator, performCalculation, onSaveCalculation, error, clearAll, currentExpression]);

  const toggleSign = useCallback(() => {
    if (error) {
      clearAll();
      return;
    }
    setDisplayValue(String(parseFloat(displayValue) * -1));
  }, [displayValue, error, clearAll]);

  const handlePercentage = useCallback(() => {
    if (error) {
      clearAll();
      return;
    }
    const value = parseFloat(displayValue);
    if (firstOperand !== null && operator !== null) {
      // If there's a pending operation, percentage applies to the second operand relative to the first
      // e.g., 100 + 10% = 100 + (100 * 0.10) = 110
      // or 100 * 10% = 100 * 0.10 = 10
      const percentageValue = (firstOperand * (value / 100));
      setDisplayValue(String(percentageValue));
    } else {
      setDisplayValue(String(value / 100));
    }
  }, [displayValue, firstOperand, operator, error, clearAll]);

  const handleSquareRoot = useCallback(() => {
    if (error) {
      clearAll();
      return;
    }
    const value = parseFloat(displayValue);
    if (value < 0) {
      setError('Error: Invalid input');
      return;
    }
    setDisplayValue(String(Math.sqrt(value)));
    setWaitingForSecondOperand(true); // Treat as a new number for next operation
  }, [displayValue, error, clearAll]);

  const handleMemory = useCallback((action) => {
    if (error) {
      clearAll();
      return;
    }
    const currentValue = parseFloat(displayValue);
    switch (action) {
      case 'M+':
        setMemory(memory + currentValue);
        break;
      case 'M-':
        setMemory(memory - currentValue);
        break;
      case 'MR':
        setDisplayValue(String(memory));
        setWaitingForSecondOperand(true);
        break;
      case 'MC':
        setMemory(0);
        break;
      default:
        break;
    }
  }, [displayValue, memory, error, clearAll]);

  const handleButtonClick = useCallback((value) => {
    if (error && value !== 'C' && value !== 'CE') {
      return; // Only allow clear buttons if there's an error
    }

    if (value === 'C') {
      clearAll();
    } else if (value === 'CE') {
      clearEntry();
    } else if (value === '+/-') {
      toggleSign();
    } else if (value === '%') {
      handlePercentage();
    } else if (value === '√') {
      handleSquareRoot();
    } else if (value === '=') {
      handleEquals();
    } else if (['+', '-', '*', '/'].includes(value)) {
      handleOperator(value);
    } else if (['M+', 'M-', 'MR', 'MC'].includes(value)) {
      handleMemory(value);
    } else if (value === '.') {
      inputDecimal();
    } else { // Digits
      inputDigit(value);
    }
  }, [clearAll, clearEntry, toggleSign, handlePercentage, handleSquareRoot, handleEquals, handleOperator, handleMemory, inputDecimal, inputDigit, error]);

  useEffect(() => {
    if (error) {
      // If an error occurs, reset other states to prevent further operations
      setFirstOperand(null);
      setOperator(null);
      setWaitingForSecondOperand(false);
      setCurrentExpression('');
    }
  }, [error]);

  return (
    <div className="calculator bg-gray-800 p-4 rounded-lg shadow-xl max-w-sm mx-auto">
      <div className="display bg-gray-900 text-white text-right p-4 mb-4 rounded-md text-4xl font-light overflow-hidden whitespace-nowrap">
        {error || displayValue}
      </div>
      <div className="grid grid-cols-4 gap-2">
        {/* Memory Buttons */}
        <Button value="MC" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />
        <Button value="MR" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />
        <Button value="M+" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />
        <Button value="M-" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />

        {/* Special Functions & Clear */}
        <Button value="C" onClick={handleButtonClick} className="bg-red-500 hover:bg-red-600 text-white" />
        <Button value="CE" onClick={handleButtonClick} className="bg-orange-500 hover:bg-orange-600 text-white" />
        <Button value="+/-" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />
        <Button value="%" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />
        <Button value="√" onClick={handleButtonClick} className="bg-gray-600 hover:bg-gray-700 text-white" />

        {/* Numbers and Operators */}
        <Button value="7" onClick={handleButtonClick} />
        <Button value="8" onClick={handleButtonClick} />
        <Button value="9" onClick={handleButtonClick} />
        <Button value="/" onClick={handleButtonClick} className="bg-orange-500 hover:bg-orange-600 text-white" />

        <Button value="4" onClick={handleButtonClick} />
        <Button value="5" onClick={handleButtonClick} />
        <Button value="6" onClick={handleButtonClick} />
        <Button value="*" onClick={handleButtonClick} className="bg-orange-500 hover:bg-orange-600 text-white" />

        <Button value="1" onClick={handleButtonClick} />
        <Button value="2" onClick={handleButtonClick} />
        <Button value="3" onClick={handleButtonClick} />
        <Button value="-" onClick={handleButtonClick} className="bg-orange-500 hover:bg-orange-600 text-white" />

        <Button value="0" onClick={handleButtonClick} className="col-span-2" />
        <Button value="." onClick={handleButtonClick} />
        <Button value="+" onClick={handleButtonClick} className="bg-orange-500 hover:bg-orange-600 text-white" />

        <Button value="=" onClick={handleButtonClick} className="col-span-4 bg-blue-600 hover:bg-blue-700 text-white" />
      </div>
    </div>
  );
};

export default Calculator;