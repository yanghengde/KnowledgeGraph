import { useCallback, useEffect, useRef, useState } from "react";
import { mappingApi, type MappingDetail, type SourceDesign } from "../../mappingApi";

export function useMappingAutosave(detail: MappingDetail) {
  const [design, setDesign] = useState(detail.design);
  const latest = useRef(design);
  const revision = useRef(detail.revision);
  const saved = useRef(JSON.stringify(design));
  const queue = useRef<Promise<void> | null>(null);
  const [status, setStatus] = useState("已保存");
  const [error, setError] = useState("");
  const flush = useCallback(async () => {
    if (queue.current) await queue.current;
    if (saved.current === JSON.stringify(latest.current)) return;
    const task = (async () => {
      setStatus("正在保存…"); setError("");
      while (saved.current !== JSON.stringify(latest.current)) {
        const value = latest.current;
        const result = await mappingApi.save(detail.draftId, revision.current, value);
        revision.current = result.revision; saved.current = JSON.stringify(value);
      }
      setStatus("已自动保存");
    })();
    queue.current = task;
    try { await task; } catch (e) { setStatus("未保存"); setError((e as Error).message); throw e; }
    finally { if (queue.current === task) queue.current = null; }
  }, [detail.draftId]);
  const change = (patch: Partial<SourceDesign>) => {
    const next = { ...latest.current, ...patch }; latest.current = next; setDesign(next); setStatus("待保存…");
  };
  useEffect(() => { const timer = window.setTimeout(() => { void flush().catch(() => {}); }, 800); return () => window.clearTimeout(timer); }, [design, flush]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (saved.current !== JSON.stringify(latest.current)) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", warn);
    return () => { window.removeEventListener("beforeunload", warn); void flush().catch(() => {}); };
  }, [flush]);
  return { design, change, flush, revision, status, error };
}
