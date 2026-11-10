import { useEffect, useRef, useState } from "react";
import { useApp } from "../AppContext";
import { STATIC } from "../staticBackend";

/** GoodData iframe authenticated as the current persona (token delivered by the postMessage handshake). */
export function Embed({ url, label, tall, onEvent }: { url: string; label: string; tall?: boolean; onEvent?: (name: string, data: any) => void }) {
  const { persona, localeVersion, localeReady } = useApp();
  const ref = useRef<HTMLIFrameElement>(null);
  if (STATIC && persona.id === "admin") url = url.replace(/[?&]apiTokenAuthentication=true/g, (m) => (m.startsWith("?") ? "?" : "")).replace("?&", "?");
  const [ready, setReady] = useState(false);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    const f = ref.current;
    if (!f) return;
    const handler = (ev: Event) => {
      const { name, data } = (ev as CustomEvent).detail || {};
      onEventRef.current?.(name, data);
    };
    f.addEventListener("gd-event", handler);
    return () => f.removeEventListener("gd-event", handler);
  }, [url, persona.id]);

  useEffect(() => {
    setReady(false);
    const f = ref.current;
    if (!f) return;
    const done = () => setReady(true);
    let timer = 0;
    const onLoad = () => (timer = window.setTimeout(done, 12000));
    f.addEventListener("gd-ready", done);
    f.addEventListener("load", onLoad);
    return () => {
      clearTimeout(timer);
      f.removeEventListener("gd-ready", done);
      f.removeEventListener("load", onLoad);
    };
  }, [url, persona.id, localeVersion, localeReady]);

  return (
    <div className={`embed-wrap ${tall ? "tall" : ""}`}>
      {localeReady && <iframe key={`${persona.id}|${localeVersion}|${url}`} ref={ref} data-gd data-persona={persona.id} src={url} allow="clipboard-write; fullscreen" title={label} />}
      <div className={`embed-loading ${ready ? "done" : ""}`}>
        <div>
          <span className="spinner" />
          &nbsp; {label}
        </div>
      </div>
    </div>
  );
}
