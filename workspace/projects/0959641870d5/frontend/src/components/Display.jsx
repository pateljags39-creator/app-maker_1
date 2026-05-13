import React from 'react';

/**
 * A presentational component that renders the calculator's display screen.
 * It shows the current input or result.
 *
 * @param {object} props - The component props.
 * @param {string} props.value - The string value to display on the screen.
 */
const Display = ({ value }) => {
  return (
    <div className="bg-gray-800 text-white text-4xl p-4 text-right rounded-t-lg font-mono h-20 flex items-center justify-end overflow-hidden">
      <span className="truncate">{value}</span>
    </div>
  );
};

export default Display;