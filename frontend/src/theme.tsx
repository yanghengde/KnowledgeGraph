import { App as AntApp, ConfigProvider, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

type ThemeMode = "light" | "dark";

const STORAGE_KEY = "opcenter_console_theme";
const ThemeModeContext = createContext<{ mode: ThemeMode; toggle: () => void } | null>(null);

const lightTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#006783",
    colorInfo: "#006783",
    colorSuccess: "#4e9a5b",
    colorWarning: "#c98818",
    colorError: "#cf3f4f",
    colorBgBase: "#f3f6f8",
    colorBgContainer: "#ffffff",
    colorBgElevated: "#ffffff",
    colorBorder: "#ccd7dd",
    colorText: "#24343c",
    colorTextSecondary: "#627780",
    borderRadius: 8,
    fontFamily: 'Inter, "Segoe UI", "Microsoft YaHei", sans-serif',
  },
  components: {
    Layout: { siderBg: "#005f78", headerBg: "#e5edf2", bodyBg: "#f3f6f8" },
    Menu: { darkItemBg: "transparent", darkSubMenuItemBg: "transparent" },
    Card: { colorBgContainer: "#ffffff" },
  },
};

const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#28d7b5",
    colorInfo: "#28d7b5",
    colorSuccess: "#4ed69a",
    colorWarning: "#f4bb55",
    colorError: "#ff6d7a",
    colorBgBase: "#07151e",
    colorBgContainer: "#0c202b",
    colorBgElevated: "#102936",
    colorBorder: "#213c47",
    colorText: "#edf7f7",
    colorTextSecondary: "#9ab1b7",
    borderRadius: 10,
    fontFamily: 'Inter, "Segoe UI", "Microsoft YaHei", sans-serif',
  },
  components: {
    Layout: { siderBg: "#081923", headerBg: "#091b25", bodyBg: "#07151e" },
    Menu: { darkItemBg: "transparent", darkSubMenuItemBg: "transparent" },
    Card: { colorBgContainer: "#0b202b" },
  },
};

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(() =>
    window.localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light",
  );

  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    document.documentElement.style.colorScheme = mode;
    window.localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const value = useMemo(
    () => ({ mode, toggle: () => setMode((current) => (current === "light" ? "dark" : "light")) }),
    [mode],
  );

  return (
    <ThemeModeContext.Provider value={value}>
      <ConfigProvider locale={zhCN} theme={mode === "light" ? lightTheme : darkTheme}>
        <AntApp>{children}</AntApp>
      </ConfigProvider>
    </ThemeModeContext.Provider>
  );
}

export function useThemeMode() {
  const context = useContext(ThemeModeContext);
  if (!context) throw new Error("useThemeMode must be used inside AppThemeProvider");
  return context;
}
