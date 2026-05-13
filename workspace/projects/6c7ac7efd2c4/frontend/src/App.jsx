import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getCalculatorState, saveCalculatorState } from './api';
import { initialCalculatorState, handleInput, setHistoryLog, setMemoryRegister } from './utils/calculatorLogic';
import CalculatorDisplay from './components/CalculatorDisplay';
import CalculatorButtons from './components/CalculatorButtons';
import HistoryPanel from './components/HistoryPanel';
import { useDebounce } from './utils/storage'; // Assuming a simple useDebounce hook might be in storage.js or a new utils file

function App() {
  const [calculatorState, setCalculatorState] = useState(initialCalculatorState);
  const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false);
  const saveStateDebounced = useDebounce(saveCalculatorState, 1000); // Debounce saving state

  // Load state from backend on mount
  useEffect(() => {
    const loadState = async () => {
      try {
        const data = await getCalculatorState();
        if (data) {
          // console.log("Loaded state from backend:", data);
          setCalculatorState(prevState => ({
            ...prevState,
            memoryRegister: data.memory_register,
            historyLog: JSON.parse(data.history_log || '[]'),
          }));
        }
      } catch (error) {
        console.error("Failed to load calculator state:", error);
      }
    };
    loadState();
  }, []);

  // Save state to backend whenever memoryRegister or historyLog changes
  useEffect(() => {
    // console.log("Saving state to backend...");
    saveStateDebounced({
      memory_register: calculatorState.memoryRegister,
      history_log: JSON.stringify(calculatorState.historyLog),
    });
  }, [calculatorState.memoryRegister, calculatorState.historyLog, saveStateDebounced]);

  const handleButtonClick = useCallback((value, type) => {
    setCalculatorState(prevState => {
      const newState = handleInput(prevState, value, type);
      // console.log("New calculator state:", newState);
      return newState;
    });
  }, []);

  const handleHistoryItemClick = useCallback((expression, result) => {
    setCalculatorState(prevState => ({
      ...prevState,
      currentExpression: expression,
      currentInput: result,
      isErrorState: false,
    }));
    setIsHistoryPanelOpen(false); // Close history panel after selecting an item
  }, []);

  const clearHistory = useCallback(() => {
    setCalculatorState(prevState => setHistoryLog(prevState, []));
  }, []);

  const handleKeyboardInput = useCallback((event) => {
    const { key, shiftKey } = event;

    // Mapping keyboard keys to calculator button values/types
    const keyMap = {
      '0': { value: '0', type: 'number' },
      '1': { value: '1', type: 'number' },
      '2': { value: '2', type: 'number' },
      '3': { value: '3', type: 'number' },
      '4': { value: '4', type: 'number' },
      '5': { value: '5', type: 'number' },
      '6': { value: '6', type: 'number' },
      '7': { value: '7', type: 'number' },
      '8': { value: '8', type: 'number' },
      '9': { value: '9', type: 'number' },
      '.': { value: '.', type: 'number' },
      ',': { value: '.', type: 'number' }, // Allow comma as decimal separator
      '+': { value: '+', type: 'operator' },
      '-': { value: '-', type: 'operator' },
      '*': { value: '*', type: 'operator' },
      '/': { value: '/', type: 'operator' },
      'Enter': { value: '=', type: 'equals' },
      '=': { value: '=', type: 'equals' },
      'Escape': { value: 'AC', type: 'clear' },
      'Backspace': { value: 'DEL', type: 'delete' },
      '%': { value: '%', type: 'operator' },
      '(': { value: '(', type: 'paren' },
      ')': { value: ')', type: 'paren' },
    };

    // Handle shift key combinations for operators and functions
    if (shiftKey) {
      if (key === '+') { event.preventDefault(); handleButtonClick('+', 'operator'); return; }
      if (key === '*') { event.preventDefault(); handleButtonClick('*', 'operator'); return; }
      if (key === '%') { event.preventDefault(); handleButtonClick('%', 'operator'); return; } // Shift+5 for %
      if (key === '^') { event.preventDefault(); handleButtonClick('^', 'operator'); return; } // Shift+6 for ^
      // For scientific functions, we might need a more complex mapping or dedicated keys
      // Example: 'S' for sin, 'C' for cos, 'T' for tan, 'L' for log, 'N' for ln, 'P' for Pi, 'E' for E
      if (key.toLowerCase() === 'p') { event.preventDefault(); handleButtonClick('π', 'constant'); return; }
      if (key.toLowerCase() === 'e') { event.preventDefault(); handleButtonClick('e', 'constant'); return; }
    }


    if (keyMap[key]) {
      event.preventDefault(); // Prevent default browser actions for calculator keys
      handleButtonClick(keyMap[key].value, keyMap[key].type);
    } else if (key === 'Delete') { // Standard Delete key for AC (Clear All)
        event.preventDefault();
        handleButtonClick('AC', 'clear');
    }
  }, [handleButtonClick]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyboardInput);
    return () => {
      window.removeEventListener('keydown', handleKeyboardInput);
    };
  }, [handleKeyboardInput]);

  return (
    <div className={`calculator-container ${isHistoryPanelOpen ? 'history-open' : ''}`} role="application" aria-label="Scientific Calculator">
      <div className="calculator-main">
        <CalculatorDisplay
          expression={calculatorState.currentExpression}
          input={calculatorState.currentInput}
          angleMode={calculatorState.angleMode}
          isErrorState={calculatorState.isErrorState}
        />
        <CalculatorButtons
          onButtonClick={handleButtonClick}
          onToggleAngleMode={() =>
            setCalculatorState(prevState => ({
              ...prevState,
              angleMode: prevState.angleMode === 'DEG' ? 'RAD' : 'DEG',
            }))
          }
          angleMode={calculatorState.angleMode}
          memoryRegister={calculatorState.memoryRegister}
          onToggleHistory={() => setIsHistoryPanelOpen(prev => !prev)}
        />
      </div>
      <HistoryPanel
        isOpen={isHistoryPanelOpen}
        history={calculatorState.historyLog}
        onClearHistory={clearHistory}
        onSelectItem={handleHistoryItemClick}
      />
    </div>
  );
}

export default App;