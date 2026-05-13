import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // For generating unique session IDs
import Display from './components/Display';
import Button from './components/Button';
import History from './components/History';
import { saveCalculation, fetchCalculationHistory } from './api'; // API functions

function App() {
  const [displayValue, setDisplayValue] = useState('0'); // What's shown on the calculator screen
  const [currentValue, setCurrentValue] = useState(null); // The number currently being input or the result of the last operation (as string)
  const [previousValue, setPreviousValue] = useState(null); // The number before the current operation (as number)
  const [operator, setOperator] = useState(null); // The pending arithmetic operator
  const [waitingForOperand, setWaitingForOperand] = useState(true); // True if the next digit input should start a new number
  const [memory, setMemory] = useState(0); // Calculator memory
  const [history, setHistory] = useState([]); // Array of past calculations fetched from the backend
  const [sessionId, setSessionId] = useState(null); // Unique ID for the current user session

  // --- Session Management ---
  // Generate or retrieve a session ID from localStorage on component mount
  useEffect(() => {
    let storedSessionId = localStorage.getItem('calculatorSessionId');
    if (!storedSessionId) {
      storedSessionId = uuidv4();
      localStorage.setItem('calculatorSessionId', storedSessionId);
    }
    setSessionId(storedSessionId);
  }, []);

  // --- History Fetching ---
  // Fetch calculation history when the sessionId becomes available
  useEffect(() => {
    if (sessionId) {
      fetchHistory();
    }
  }, [sessionId]); // Dependency array ensures this runs when sessionId changes

  const fetchHistory = async () => {
    try {
      const data = await fetchCalculationHistory();
      setHistory(data);
    } catch (error) {
      console.error('Failed to fetch history:', error);
      // Optionally, display an error message to the user on the UI
    }
  };

  // --- Calculator Core Logic ---

  const inputDigit = (digit) => {
    if (displayValue === 'Error: Div by zero' || displayValue === 'Error') {
      clearAll(); // Clear error state before new input
    }

    if (waitingForOperand) {
      setDisplayValue(String(digit));
      setCurrentValue(String(digit));
      setWaitingForOperand(false);
    } else {
      // Prevent multiple leading zeros unless it's a decimal
      if (displayValue === '0' && digit === '0') return;
      // Replace '0' if it's the only digit and not a decimal
      if (displayValue === '0' && digit !== '.') {
        setDisplayValue(String(digit));
        setCurrentValue(String(digit));
      } else {
        setDisplayValue((prev) => prev + String(digit));
        setCurrentValue((prev) => prev + String(digit));
      }
    }
  };

  const inputDecimal = () => {
    if (displayValue === 'Error: Div by zero' || displayValue === 'Error') {
      clearAll(); // Clear error state before new input
    }

    if (waitingForOperand) {
      setDisplayValue('0.');
      setCurrentValue('0.');
      setWaitingForOperand(false);
    } else if (!displayValue.includes('.')) {
      setDisplayValue((prev) => prev + '.');
      setCurrentValue((prev) => prev + '.');
    }
  };

  const clearEntry = () => {
    setDisplayValue('0');
    setCurrentValue('0');
    // Do not reset previousValue or operator, only current input
    setWaitingForOperand(true); // Ready for new input
  };

  const clearAll = () => {
    setDisplayValue('0');
    setCurrentValue(null);
    setPreviousValue(null);
    setOperator(null);
    setWaitingForOperand(true);
  };

  const toggleSign = () => {
    if (displayValue === '0' || displayValue === 'Error' || displayValue === 'Error: Div by zero') return;
    const newValue = parseFloat(displayValue) * -1;
    setDisplayValue(String(newValue));
    setCurrentValue(String(newValue));
  };

  const inputPercent = () => {
    if (displayValue === 'Error' || displayValue === 'Error: Div by zero') return;
    const value = parseFloat(displayValue);
    if (isNaN(value)) {
      setDisplayValue('Error');
      setCurrentValue(null);
      return;
    }
    const newValue = value / 100;
    setDisplayValue(String(newValue));
    setCurrentValue(String(newValue));
  };

  const inputSquareRoot = () => {
    if (displayValue === 'Error' || displayValue === 'Error: Div by zero') return;
    const value = parseFloat(displayValue);
    if (isNaN(value) || value < 0) {
      setDisplayValue('Error');
      setCurrentValue(null);
      return;
    }
    const newValue = Math.sqrt(value);
    setDisplayValue(String(newValue));
    setCurrentValue(String(newValue));
  };

  // Performs the actual arithmetic calculation
  const calculate = (prev, curr, op) => {
    const prevNum = parseFloat(prev);
    const currNum = parseFloat(curr);

    if (isNaN(prevNum) || isNaN(currNum)) return 'Error';

    let result;
    switch (op) {
      case '+':
        result = prevNum + currNum;
        break;
      case '-':
        result = prevNum - currNum;
        break;
      case '*':
        result = prevNum * currNum;
        break;
      case '/':
        if (currNum === 0) return 'Error: Div by zero';
        result = prevNum / currNum;
        break;
      default:
        return currNum; // If no operator, just return the current number
    }
    return result;
  };

  const performOperation = (nextOperator) => {
    if (displayValue === 'Error' || displayValue === 'Error: Div by zero') return;

    const inputValue = parseFloat(currentValue);

    if (previousValue === null) {
      setPreviousValue(inputValue);
    } else if (!waitingForOperand) {
      // If an operand was entered, calculate the previous operation
      const result = calculate(previousValue, inputValue, operator);
      if (typeof result === 'string' && result.startsWith('Error')) {
        setDisplayValue(result);
        setCurrentValue(null);
        setPreviousValue(null);
        setOperator(null);
        setWaitingForOperand(true);
        return;
      }
      setPreviousValue(result);
      setDisplayValue(String(result));
      setCurrentValue(String(result));
    }

    setWaitingForOperand(true);
    setOperator(nextOperator);
  };

  const handleEquals = async () => {
    if (displayValue === 'Error' || displayValue === 'Error: Div by zero' || previousValue === null || operator === null) {
      return;
    }

    const inputValue = parseFloat(currentValue);
    const result = calculate(previousValue, inputValue, operator);

    if (typeof result === 'string' && result.startsWith('Error')) {
      setDisplayValue(result);
      setCurrentValue(null);
      setPreviousValue(null);
      setOperator(null);
      setWaitingForOperand(true);
      return;
    }

    const expression = `${previousValue} ${operator} ${inputValue}`;
    const resultString = String(result);

    setDisplayValue(resultString);
    setCurrentValue(resultString);
    setPreviousValue(null);
    setOperator(null);
    setWaitingForOperand(true);

    // Save calculation to history if a session ID exists
    if (sessionId) {
      try {
        await saveCalculation(sessionId, expression, resultString);
        fetchHistory(); // Refresh history after saving
      } catch (error) {
        console.error('Failed to save calculation:', error);
      }
    }
  };

  // --- Memory Functions ---
  const memoryAdd = () => {
    if (displayValue === 'Error' || displayValue === 'Error: Div by zero') return;
    const value = parseFloat(displayValue);
    if (!isNaN(value)) {
      setMemory((prev) => prev + value);
    }
  };

  const memorySubtract = () => {
    if (displayValue === 'Error' || displayValue === 'Error: Div by zero') return;
    const value = parseFloat(displayValue);
    if (!isNaN(value)) {
      setMemory((prev) => prev - value);
    }
  };

  const memoryRecall = () => {
    setDisplayValue(String(memory));
    setCurrentValue(String(memory));
    setWaitingForOperand(true); // After recalling, next digit should start a new number
  };

  const memoryClear = () => {
    setMemory(0);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold mb-8 text-blue-400">Web Calculator Pro</h1>
      <div className="flex flex-col lg:flex-row gap-8 w-full max-w-6xl">
        {/* Calculator Section */}
        <div className="flex-1 bg-gray-800 rounded-lg shadow-xl p-6 max-w-md mx-auto lg:mx-0">
          <Display value={displayValue} />
          <div className="grid grid-cols-4 gap-2 mt-4">
            {/* Memory Buttons */}
            <Button onClick={memoryClear} className="bg-gray-600 hover:bg-gray-700">MC</Button>
            <Button onClick={memoryRecall} className="bg-gray-600 hover:bg-gray-700">MR</Button>
            <Button onClick={memoryAdd} className="bg-gray-600 hover:bg-gray-700">M+</Button>
            <Button onClick={memorySubtract} className="bg-gray-600 hover:bg-gray-700">M-</Button>

            {/* Clear & Special Functions */}
            <Button onClick={clearAll} className="bg-red-500 hover:bg-red-600">C</Button>
            <Button onClick={clearEntry} className="bg-orange-500 hover:bg-orange-600">CE</Button>
            <Button onClick={inputPercent} className="bg-gray-600 hover:bg-gray-700">%</Button>
            <Button onClick={() => performOperation('/')} className="bg-blue-500 hover:bg-blue-600">/</Button>

            {/* Number Row 7-9 */}
            <Button onClick={() => inputDigit(7)}>7</Button>
            <Button onClick={() => inputDigit(8)}>8</Button>
            <Button onClick={() => inputDigit(9)}>9</Button>
            <Button onClick={() => performOperation('*')} className="bg-blue-500 hover:bg-blue-600">*</Button>

            {/* Number Row 4-6 */}
            <Button onClick={() => inputDigit(4)}>4</Button>
            <Button onClick={() => inputDigit(5)}>5</Button>
            <Button onClick={() => inputDigit(6)}>6</Button>
            <Button onClick={() => performOperation('-')} className="bg-blue-500 hover:bg-blue-600">-</Button>

            {/* Number Row 1-3 */}
            <Button onClick={() => inputDigit(1)}>1</Button>
            <Button onClick={() => inputDigit(2)}>2</Button>
            <Button onClick={() => inputDigit(3)}>3</Button>
            <Button onClick={() => performOperation('+')} className="bg-blue-500 hover:bg-blue-600">+</Button>

            {/* Bottom Row */}
            <Button onClick={toggleSign} className="bg-gray-600 hover:bg-gray-700">+/-</Button>
            <Button onClick={() => inputDigit(0)}>0</Button>
            <Button onClick={inputDecimal}>.</Button>
            <Button onClick={handleEquals} className="bg-green-500 hover:bg-green-600">=</Button>
          </div>
          <div className="mt-2">
            <Button onClick={inputSquareRoot} className="w-full bg-gray-600 hover:bg-gray-700">√</Button>
          </div>
        </div>

        {/* History Section */}
        <div className="flex-1 bg-gray-800 rounded-lg shadow-xl p-6 max-w-md mx-auto lg:mx-0">
          <History history={history} />
        </div>
      </div>
    </div>
  );
}

export default App;