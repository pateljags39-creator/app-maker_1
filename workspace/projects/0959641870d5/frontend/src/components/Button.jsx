import React from 'react';

/**
 * A reusable button component for the calculator's keypad.
 * It handles numbers, operators, the equals sign, and the clear button.
 *
 * @param {object} props - The component props.
 * @param {string} props.value - The value displayed on the button and passed to the onClick handler.
 * @param {function} props.onClick - The function to call when the button is clicked.
 * @param {string} [props.className=''] - Additional CSS classes to apply to the button.
 */
const Button = ({ value, onClick, className = '' }) => {
  let buttonClasses = "flex justify-center items-center text-2xl font-semibold rounded-lg shadow-md transition-all duration-200 ease-in-out active:scale-95";

  // Apply specific styles based on the button's value
  if (['+', '-', '*', '/'].includes(value)) {
    buttonClasses += " bg-orange-500 hover:bg-orange-600 text-white";
  } else if (value === '=') {
    buttonClasses += " bg-blue-500 hover:bg-blue-600 text-white";
  } else if (value === 'C') {
    buttonClasses += " bg-red-500 hover:bg-red-600 text-white";
  } else if (value === '.') {
    buttonClasses += " bg-gray-300 hover:bg-gray-400 text-gray-800";
  } else {
    // Default for numbers
    buttonClasses += " bg-gray-200 hover:bg-gray-300 text-gray-800";
  }

  // Add any additional classes passed via props
  buttonClasses += ` ${className}`;

  return (
    <button
      className={buttonClasses.trim()}
      onClick={() => onClick(value)}
    >
      {value}
    </button>
  );
};

export default Button;