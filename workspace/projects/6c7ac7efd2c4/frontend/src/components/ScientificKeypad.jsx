import React from 'react';

/**
 * ScientificKeypad component renders the scientific function buttons of the calculator.
 * It takes `handleButtonClick`, `angleMode`, and `toggleAngleMode` as props.
 */
const ScientificKeypad = ({ handleButtonClick, angleMode, toggleAngleMode }) => {
  return (
    <div className="scientific-keypad">
      {/* Row 1: Memory functions */}
      <button className="button fn-button memory-button" onClick={() => handleButtonClick('mc')}>MC</button>
      <button className="button fn-button memory-button" onClick={() => handleButtonClick('mr')}>MR</button>
      <button className="button fn-button memory-button" onClick={() => handleButtonClick('m+')}>M+</button>
      <button className="button fn-button memory-button" onClick={() => handleButtonClick('m-')}>M-</button>

      {/* Row 2: Parentheses, Factorial, Modulo */}
      <button className="button fn-button" onClick={() => handleButtonClick('(')}>(</button>
      <button className="button fn-button" onClick={() => handleButtonClick(')')}>)</button>
      <button className="button fn-button" onClick={() => handleButtonClick('fact')}>n!</button>
      <button className="button fn-button" onClick={() => handleButtonClick('%')}>%</button>

      {/* Row 3: Power, Root, Reciprocal */}
      <button className="button fn-button" onClick={() => handleButtonClick('x^2')}>x²</button>
      <button className="button fn-button" onClick={() => handleButtonClick('sqrt')}>√</button>
      <button className="button fn-button" onClick={() => handleButtonClick('^')}>xʸ</button>
      <button className="button fn-button" onClick={() => handleButtonClick('1/x')}>1/x</button>

      {/* Row 4: Trigonometric functions & Angle Mode Toggle */}
      <button className="button fn-button" onClick={() => handleButtonClick('sin')}>sin</button>
      <button className="button fn-button" onClick={() => handleButtonClick('cos')}>cos</button>
      <button className="button fn-button" onClick={() => handleButtonClick('tan')}>tan</button>
      <button className="button fn-button mode-toggle" onClick={toggleAngleMode} aria-label={`Toggle angle mode, current mode: ${angleMode}`}>
        {angleMode === 'DEG' ? 'DEG' : 'RAD'} {/* Displays current angle mode */}
      </button>

      {/* Row 5: Logarithmic functions & Constants */}
      <button className="button fn-button" onClick={() => handleButtonClick('log')}>log</button>
      <button className="button fn-button" onClick={() => handleButtonClick('ln')}>ln</button>
      <button className="button fn-button" onClick={() => handleButtonClick('pi')}>π</button>
      <button className="button fn-button" onClick={() => handleButtonClick('e')}>e</button>

      {/* Row 6: Sign Change */}
      <button className="button fn-button" onClick={() => handleButtonClick('changeSign')}>+/-</button>
      {/* Remaining cells in the last row will be empty, styled by CSS grid */}
    </div>
  );
};

export default ScientificKeypad;