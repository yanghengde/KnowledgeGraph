import { Tooltip } from "antd";
import { useThemeMode } from "../../theme";

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20.2 15.1A8.6 8.6 0 0 1 8.9 3.8a8.8 8.8 0 1 0 11.3 11.3Z" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="3.7" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

export function ThemeToggle() {
  const { mode, toggle } = useThemeMode();
  const label = mode === "light" ? "切换到深色主题" : "切换到浅色主题";

  return (
    <Tooltip title={label} placement="bottomRight">
      <button className="theme-toggle" type="button" onClick={toggle} aria-label={label}>
        {mode === "light" ? <MoonIcon /> : <SunIcon />}
      </button>
    </Tooltip>
  );
}
