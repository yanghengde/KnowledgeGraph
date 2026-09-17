import { App as AntApp,ConfigProvider,theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import { createContext,useContext,useEffect,useMemo,useState,type ReactNode } from "react";

type ThemeMode = "light" | "dark";

const STORAGE_KEY = "opcenter_console_theme";
const ThemeModeContext = createContext<{ mode: ThemeMode; toggle: () => void } | null>(null);

const lightTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#0070f2",
    colorInfo: "#0070f2",
    colorSuccess: "#4e9a5b",
    colorWarning: "#c98818",
    colorError: "#cf3f4f",
    colorBgBase: "#f5f6f7",
    colorBgContainer: "#ffffff",
    colorBgElevated: "#ffffff",
    colorBgContainerDisabled: "#e8eef1",
    colorBorder: "#b8c8cf",
    colorBorderDisabled: "#a9bbc3",
    colorText: "#1d2d3e",
    colorTextSecondary: "#556b82",
    colorTextDisabled: "#657a83",
    borderRadius: 8,
    fontFamily: 'Inter, "Segoe UI", "Microsoft YaHei", sans-serif',
  },
  components: {
    Layout: { siderBg: "#1d2d3e", headerBg: "#ffffff", bodyBg: "#f5f6f7" },
    Menu: { darkItemBg: "transparent", darkSubMenuItemBg: "transparent" },
    Card: { colorBgContainer: "#ffffff" },
    Button: {
      fontWeight: 600,
      defaultColor: "#173f4d",
      defaultBg: "#ffffff",
      defaultBorderColor: "#9fb4bd",
      defaultHoverColor: "#005b73",
      defaultHoverBg: "#edf7f9",
      defaultHoverBorderColor: "#006f8b",
      defaultActiveColor: "#004c61",
      defaultActiveBg: "#dfeef2",
      defaultActiveBorderColor: "#1d2d3e",
      defaultBgDisabled: "#e8eef1",
      borderColorDisabled: "#a9bbc3",
      textTextColor: "#234b59",
      textTextHoverColor: "#1d2d3e",
      textTextActiveColor: "#00485d",
      textHoverBg: "#e8f3f6",
      dangerColor: "#b42336",
      defaultShadow: "0 1px 2px rgba(24, 58, 70, 0.10)",
      primaryShadow: "0 2px 5px rgba(0, 79, 101, 0.24)",
      dangerShadow: "0 1px 3px rgba(180, 35, 54, 0.16)",
    },
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
