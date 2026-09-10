import React from "react";
import { Moon, Sun } from "lucide-react";

const ThemeToggle = ({ toggleTheme, isDark, className }) => {
  return (
    <button
      className={className}
      onClick={toggleTheme}

      style={{
        width: "30px",
        height: "30px",
        borderRadius: "50%",
        border: "none",
        cursor: "pointer",
        background: isDark ? "#222" : "#fff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative", // needed for star positioning
        boxShadow: isDark
          ? "0 0 12px rgba(255,255,255,0.4)"
          : "0 0 12px rgba(255,255,255,0.4)",
        transition: "all 0.3s ease-in-out",
      }}

    >
      {isDark ? (
        <Moon size={20} color="white" />
      ) : (
        <Sun size={20} color="grey" />
      )}
    </button>
  );
};

export default ThemeToggle;