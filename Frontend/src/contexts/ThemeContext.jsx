import React, { useState, createContext, useContext, useEffect } from 'react';
import { themes } from '../styles/appStyles';

const ThemeContext = createContext();

export const ThemeContextProvider = ({ children }) => {
  const [theme, setTheme] = useState('dark');
  const toggleTheme = () => setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  const currentTheme = themes[theme];

  useEffect(() => {
    // Set the data-theme attribute on the body to enable CSS variable theming
    document.body.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, currentTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);