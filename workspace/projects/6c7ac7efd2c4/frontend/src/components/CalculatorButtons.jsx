import React from 'react';
import PropTypes from 'prop-types';

/**
 * CalculatorButtons component renders the grid of calculator buttons.
 * It handles button clicks and passes their values to the parent component.
 * It also manages the display of the angle mode toggle (DEG/RAD).
 *
 * @param {object} props - The component props.
 * @param {function(string): void} props.handleButtonClick - Function to call when a standard button is clicked.
 * @param {'DEG' | 'RAD'} props.angleMode - Current angle mode for trigonometric functions.
 * @param {function(): void} props.toggleAngleMode - Function to call when the angle mode toggle button is clicked.
 */
const CalculatorButtons = ({ handleButtonClick, angleMode, toggleAngleMode }) => {
  // Define button configurations, including label, value, CSS class, and ARIA label for accessibility.
  // The 'value' corresponds to the operation or input to be processed by calculatorLogic.js.
  const buttons = [
    // Row 1: Parentheses, percentage, clear
    { label: '(', value: '(', className: 'btn-function', ariaLabel: 'Open parenthesis' },
    { label: ')', value: ')', className: 'btn-function', ariaLabel: 'Close parenthesis' },
    { label: '%', value: '%', className: 'btn-operator', ariaLabel: 'Percentage' },
    { label: 'AC', value: 'AC', className: 'btn-clear', ariaLabel: 'All Clear' },
    { label: 'C', value: 'C', className: 'btn-clear', ariaLabel: 'Clear Entry' },

    // Row 2: Trigonometric functions, angle mode toggle, sign toggle
    { label: 'sin', value: 'sin', className: 'btn-function', ariaLabel: 'Sine function' },
    { label: 'cos', value: 'cos', className: 'btn-function', ariaLabel: 'Cosine function' },
    { label: 'tan', value: 'tan', className: 'btn-function', ariaLabel: 'Tangent function' },
    { label: 'DEG', value: 'DEG_RAD_TOGGLE', className: 'btn-mode-toggle', ariaLabel: `Toggle angle mode, currently ${angleMode}`, dynamicLabel: true },
    { label: '+/-', value: 'SIGN_TOGGLE', className: 'btn-function', ariaLabel: 'Change sign of current number' },

    // Row 3: Logarithmic functions, power, square root, division
    { label: 'log', value: 'log', className: 'btn-function', ariaLabel: 'Common logarithm base 10' },
    { label: 'ln', value: 'ln', className: 'btn-function', ariaLabel: 'Natural logarithm' },
    { label: 'xʸ', value: '^', className: 'btn-function', ariaLabel: 'Power (x to the power of y)' },
    { label: '√', value: 'sqrt', className: 'btn-function', ariaLabel: 'Square root' },
    { label: '÷', value: '/', className: 'btn-operator', ariaLabel: 'Divide' },

    // Row 4: Constants, square, factorial, multiplication
    { label: 'π', value: 'PI', className: 'btn-constant', ariaLabel: 'Pi constant' },
    { label: 'e', value: 'e', className: 'btn-constant', ariaLabel: 'Euler\'s number' },
    { label: 'x²', value: 'x^2', className: 'btn-function', ariaLabel: 'Square function' },
    { label: 'x!', value: 'fact', className: 'btn-function', ariaLabel: 'Factorial function' },
    { label: '×', value: '*', className: 'btn-operator', ariaLabel: 'Multiply' },

    // Row 5: Memory clear, 7, 8, 9, subtraction
    { label: 'MC', value: 'MC', className: 'btn-memory', ariaLabel: 'Memory Clear' },
    { label: '7', value: '7', className: 'btn-number', ariaLabel: 'Seven' },
    { label: '8', value: '8', className: 'btn-number', ariaLabel: 'Eight' },
    { label: '9', value: '9', className: 'btn-number', ariaLabel: 'Nine' },
    { label: '−', value: '-', className: 'btn-operator', ariaLabel: 'Subtract' },

    // Row 6: Memory recall, 4, 5, 6, addition
    { label: 'MR', value: 'MR', className: 'btn-memory', ariaLabel: 'Memory Recall' },
    { label: '4', value: '4', className: 'btn-number', ariaLabel: 'Four' },
    { label: '5', value: '5', className: 'btn-number', ariaLabel: 'Five' },
    { label: '6', value: '6', className: 'btn-number', ariaLabel: 'Six' },
    { label: '+', value: '+', className: 'btn-operator', ariaLabel: 'Add' },

    // Row 7: Memory add, 1, 2, 3, EQUALS (top part of the two-row spanned button)
    { label: 'M+', value: 'M+', className: 'btn-memory', ariaLabel: 'Memory Add' },
    { label: '1', value: '1', className: 'btn-number', ariaLabel: 'One' },
    { label: '2', value: '2', className: 'btn-number', ariaLabel: 'Two' },
    { label: '3', value: '3', className: 'btn-number', ariaLabel: 'Three' },
    { label: '=', value: '=', className: 'btn-equals span-two-rows', ariaLabel: 'Calculate equals' },

    // Row 8: Memory subtract, 0, decimal point. (The last column is implicitly occupied by the spanned '=' button)
    { label: 'M-', value: 'M-', className: 'btn-memory', ariaLabel: 'Memory Subtract' },
    { label: '0', value: '0', className: 'btn-number', ariaLabel: 'Zero' },
    { label: '.', value: '.', className: 'btn-number', ariaLabel: 'Decimal point' },
    // The 4th and 5th columns of this row are empty or part of the spanned '=' button from the row above.
  ];

  return (
    <div className="calculator-buttons">
      {buttons.map((button, index) => (
        <button
          key={index}
          className={`calculator-button ${button.className}`}
          onClick={() => {
            if (button.value === 'DEG_RAD_TOGGLE') {
              toggleAngleMode();
            } else {
              handleButtonClick(button.value);
            }
          }}
          aria-label={button.ariaLabel}
        >
          {button.dynamicLabel ? angleMode : button.label}
        </button>
      ))}
    </div>
  );
};

CalculatorButtons.propTypes = {
  handleButtonClick: PropTypes.func.isRequired,
  angleMode: PropTypes.oneOf(['DEG', 'RAD']).isRequired,
  toggleAngleMode: PropTypes.func.isRequired,
};

export default CalculatorButtons;