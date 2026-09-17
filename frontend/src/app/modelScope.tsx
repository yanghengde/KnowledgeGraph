import { useIsMutating,useQuery } from "@tanstack/react-query";
import { Alert,Button,Select,Space,Spin,Typography } from "antd";
import { createContext,useContext,useEffect,useState,type ReactNode } from "react";
import { syncApi } from "../api";
import type { GraphProfile } from "../types";
import { resolveModelSelection } from "./modelSelection";

const KEY = "opcenter_active_model";
const ScopeContext = createContext<{
  profileKey: string;
  profile?: GraphProfile;
  lock: () => () => void;
  selector: ReactNode;
  unavailable: ReactNode;
} | null>(null);

export function ModelScopeProvider({ children }: { children: ReactNode }) {
  const profiles = useQuery({ queryKey: ["sync-profiles"], queryFn: syncApi.profiles });
  const [selected, setSelected] = useState(() => { try { return localStorage.getItem(KEY) || ""; } catch { return ""; } });
  const [locks, setLocks] = useState(0);
  const mutating = useIsMutating();
  const [lock] = useState(() => () => {
    setLocks(n => n + 1);
    return () => setLocks(n => n - 1);
  });
  const items = profiles.data?.items.filter(p => p.enabled) || [];
  // Never replace a previously selected model silently, even if only one remains.
  const profileKey = profiles.isError ? "" : resolveModelSelection(items, selected);
  useEffect(() => {
    if (profileKey) {
      setSelected(profileKey);
      try { localStorage.setItem(KEY, profileKey); } catch { /* session-only selection */ }
    }
  }, [profileKey]);
  const selector = <Space className="model-scope-selector">
    <Typography.Text type="secondary">当前模型</Typography.Text>
    <Select aria-label="当前模型" placeholder="选择模型" value={profileKey || undefined}
      loading={profiles.isPending} disabled={locks > 0 || mutating > 0 || profiles.isError}
      title={locks > 0 ? "完成并关闭对象编辑后可切换模型" : undefined}
      style={{ minWidth: 190 }} onChange={setSelected}
      options={items.map(p => ({ value: p.profile_key, label: p.title || p.profile_key }))} />
  </Space>;
  const unavailable = profiles.isPending ? <Spin tip="正在读取模型配置"><div style={{ height: 120 }} /></Spin>
    : <Alert showIcon type={profiles.isError ? "error" : "info"}
      message={profiles.isError ? "模型配置读取失败" : selected ? "上次使用的模型已不可用，请重新选择" : items.length ? "请先选择当前模型" : "尚无可用模型"}
      description="当前模型决定建模、数据同步与发布的操作范围。"
      action={<Button onClick={() => void profiles.refetch()}>重新读取</Button>} />;
  return <ScopeContext.Provider value={{ profileKey, profile: items.find(p => p.profile_key === profileKey), lock, selector, unavailable }}>{children}</ScopeContext.Provider>;
}

export function useModelScope() {
  const context = useContext(ScopeContext);
  if (!context) throw new Error("ModelScopeProvider is required");
  return context;
}

export function useModelEditLock() {
  const { lock } = useModelScope();
  useEffect(() => lock(), [lock]);
}
