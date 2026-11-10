import { useEffect, useRef, useState } from "react";
import { useApp } from "../AppContext";
import { STATIC } from "../staticBackend";

/** Everything before "#": the GoodData app page. Dashboards of one workspace differ only after it. */
const pageOf = (url: string) => url.split("#")[0];

/**
 * GoodData iframe authenticated as the current persona (token delivered by the postMessage handshake).
 * The iframe is kept while only the part after "#" changes, so switching dashboards navigates inside the
 * already running GoodData app instead of downloading and booting it again.
 */
export function Embed({ url, label, tall, onEvent }: { url: string; label: string; tall?: boolean; onEvent?: (name: string, data: any) => void }) {
  const { persona, localeVersion, localeReady } = useApp();
  const ref = useRef<HTMLIFrameElement>(null);
  if (STATIC && persona.id === "admin") url = url.replace(/[?&]apiTokenAuthentication=true/g, (m) => (m.startsWith("?") ? "?" : "")).replace("?&", "?");
  const page = pageOf(url);
  const frameKey = `${persona.id}|${localeVersion}|${page}`;
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
  }, [frameKey, localeReady]);

  // the loading overlay only covers a fresh boot of the GoodData app, not a dashboard switch inside it
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
  }, [frameKey, localeReady]);

  // same GoodData page, different dashboard: change only the hash of the running iframe
  useEffect(() => {
    const f = ref.current;
    if (f && f.getAttribute("src") !== url) f.setAttribute("src", url);
  }, [url]);

  return (
    <div className={`embed-wrap ${tall ? "tall" : ""}`}>
      {localeReady && <iframe key={frameKey} ref={ref} data-gd data-persona={persona.id} src={url} allow="clipboard-write; fullscreen" title={label} />}
      <div className={`embed-loading ${ready ? "done" : ""}`}>
        <div>
          <span className="spinner" />
          &nbsp; {label}
        </div>
      </div>
    </div>
  );
}

/**
 * Hidden, one-off GoodData dashboard that boots in the background (e.g. while the user reads Home), so the
 * browser has GoodData's app (~11 MB) cached and the dashboard data warm before the first real dashboard.
 */
export function Prewarm({ url }: { url: string }) {
  const { persona, localeReady } = useApp();
  const [gone, setGone] = useState(false);
  useEffect(() => {
    setGone(false);
    const t = window.setTimeout(() => setGone(true), 90_000);
    return () => window.clearTimeout(t);
  }, [url, persona.id]);
  if (!localeReady || gone) return null;
  return <iframe className="prewarm" data-gd data-persona={persona.id} src={url} title="" aria-hidden="true" tabIndex={-1} />;
}
