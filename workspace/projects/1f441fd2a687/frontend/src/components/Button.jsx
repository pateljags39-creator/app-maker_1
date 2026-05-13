import React from 'react';
import PropTypes from 'prop-types';

const Button = ({ children, onClick, className = '', type = 'default' }) => {
  const baseStyles = 'flex items-center justify-center rounded-lg text-2xl font-semibold transition-colors duration-200 ease-in-out shadow-md';
  let typeStyles = '';

  switch (type) {
    case 'operator':
      typeStyles = 'bg-orange-500 hover:bg-orange-600 text-white';
      break;
    case 'clear':
      typeStyles = 'bg-gray-400 hover:bg-gray-500 text-white';
      break;
    case 'equals':
      typeStyles = 'bg-blue-600 hover:bg-blue-700 text-white';
      break;
    case 'number':
    case 'default':
    default:
      typeStyles = 'bg-gray-200 hover:bg-gray-300 text-gray-800';
      break;
  }

  return (
    <button
      className={`${baseStyles} ${typeStyles} ${className}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func.isRequired,
  className: PropTypes.string,
  type: PropTypes.oneOf(['default', 'number', 'operator', 'clear', 'equals']),
};

export default Button;