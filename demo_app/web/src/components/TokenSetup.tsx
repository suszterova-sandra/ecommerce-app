import { useState, type FormEvent } from "react";
import { saveTokens, storedTokens, type StoredTokens } from "../staticBackend";

const FIELDS: { id: keyof StoredTokens; label: string; hint: string }[] = [
  { id: "admin", label: "Admin token", hint: "sandra.suszterova · required (Control Center, overview)" },
  { id: "analyze", label: "Analyze user token", hint: "sas.analyze.user · optional" },
  { id: "view", label: "View user token", hint: "sas.view.user · optional" },
];

/** First visit on the static (GitHub Pages) build: tokens are entered here and kept only in this browser. */
export function TokenSetup() {
  const [tokens, setTokens] = useState<StoredTokens>(storedTokens());
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!tokens.admin?.trim()) return;
    saveTokens(Object.fromEntries(Object.entries(tokens).map(([k, v]) => [k, (v || "").trim()]).filter(([, v]) => v)));
    location.reload();
  };
  return (
    <div className="boot">
      <form className="token-setup" onSubmit={submit}>
        <h2>Ecommerce Platform</h2>
        <p>
          Enter the GoodData API tokens for this demo. They are stored only in this browser and sent only to
          navy-blue-eagle.trial.cloud.gooddata.com.
        </p>
        {FIELDS.map((f) => (
          <label key={f.id}>
            <span>{f.label}</span>
            <input
              type="password"
              autoComplete="off"
              value={tokens[f.id] || ""}
              onChange={(e) => setTokens((t) => ({ ...t, [f.id]: e.target.value }))}
              placeholder={f.hint}
            />
          </label>
        ))}
        <button className="btn primary" type="submit" disabled={!tokens.admin?.trim()}>
          Open the demo
        </button>
      </form>
    </div>
  );
}
