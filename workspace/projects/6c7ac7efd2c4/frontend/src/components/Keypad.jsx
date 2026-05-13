import React from 'react';

/**
 * Keypad component renders the basic calculator buttons (numbers, operators, special functions).
 *
 * @param {object} props - The component props.
 * @param {function} props.onButtonClick - Function to call when a button is clicked,
 *                                       passing the button's value.
 */
function Keypad({ onButtonClick }) {
  return (
    <div className="keypad">
      {/* Row 1: Clear, Sign Change, Percentage, Divide */}
      <button className="key special" onClick={() => onButtonClick('AC')}>AC</button> {/* All Clear */}
      <button className="key special" onClick={() => onButtonClick('+/-')}>+/-</button>
      <button className="key special" onClick={() => onButtonClick('%')}>%</button>
      <button className="key operator" onClick={() => onButtonClick('/')}>/</button>

      {/* Row 2: 7, 8, 9, Multiply */}
      <button className="key digit" onClick={() => onButtonClick('7')}>7</button>
      <button className="key digit" onClick={() => onButtonClick('8')}>8</button>
      <button className="key digit" onClick={() => onButtonClick('9')}>9</button>
      <button className="key operator" onClick={() => onButtonClick('*')}>×</button>

      {/* Row 3: 4, 5, 6, Subtract */}
      <button className="key digit" onClick={() => onButtonClick('4')}>4</button>
      <button className="key digit" onClick={() => onButtonClick('5')}>5</button>
      <button className="key digit" onClick={() => onButtonClick('6')}>6</button>
      <button className="key operator" onClick={() => onButtonClick('-')}>−</button>

      {/* Row 4: 1, 2, 3, Add */}
      <button className="key digit" onClick={() => onButtonClick('1')}>1</button>
      <button className="key digit" onClick={() => onButtonClick('2')}>2</button>
      <button className="key digit" onClick={() => onButtonClick('3')}>3</button>
      <button className="key operator" onClick={() => onButtonClick('+')}>+</button>

      {/* Row 5: 0 (wide), Decimal, Equals */}
      <button className="key digit wide" onClick={() => onButtonClick('0')}>0</button> {/* 'wide' class for spanning 2 columns */}
      <button className="key digit" onClick={() => onButtonClick('.')}>.</button>
      <button className="key equals" onClick={() => onButtonClick('=')}>=</button>
    </div>
  );
}

export default Keypad;