import React, { useState, useEffect, FormEvent } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Navigate,
  useNavigate,
  Link,
} from "react-router-dom";
import { api, API, Run, Result, Message, Evidence, Status } from "./api";
import "./styles.css";

type Doc = {
  id: string;
  name: string;
  ingestion: { records: number; at: string; embedding: string };
};
const date = (v: string) =>
  new Date(v).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
export function Badge({ value }: { value: string }) {
  return <span className={"badge " + value}>{value.replaceAll("_", " ")}</span>;
}
function ErrorBox({ error }: { error: string }) {
  return error ? (
    <div role="alert" className="error">
      {error}
    </div>
  ) : null;
}
function Loading() {
  return (
    <div className="empty" role="status">
      Loading workspace…
    </div>
  );
}
function EvidenceList({ items }: { items: Evidence[] }) {
  return (
    <div className="evidence">
      {items.map((e, i) => (
        <details key={e.id || e.source_id || i}>
          <summary>
            {e.source?.file || e.source_type || "Knowledge record"} ·{" "}
            {e.source?.record_id || e.source_id || e.id}
            {e.score !== undefined && (
              <span>Similarity {e.score.toFixed(3)}</span>
            )}
          </summary>
          <pre>{e.text || JSON.stringify(e.original, null, 2)}</pre>
        </details>
      ))}
    </div>
  );
}
function Header({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {children}
    </header>
  );
}
function Login({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState("operator"),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/session", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      onLogin();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login">
      <div className="login-story">
        <div className="brand">
          <span className="brand-mark">e</span> EventOps Intelligence
        </div>
        <p className="eyebrow">Operations, with evidence.</p>
        <h1>
          Every detail.
          <br />
          Accounted for.
        </h1>
        <p>
          A shared workspace for event knowledge, attendee verification, and
          transparent execution.
        </p>
        <div className="login-footer">
          EVENT OPERATIONS / INTELLIGENCE WORKSPACE
        </div>
      </div>
      <div className="login-form">
        <form onSubmit={submit}>
          <p className="eyebrow">WELCOME TO YOUR WORKSPACE</p>
          <h2>Sign in</h2>
          <p>Use your configured demonstration credentials.</p>
          <label>
            Username
            <input
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <ErrorBox error={error} />
          <button disabled={busy}>
            {busy ? "Signing in…" : "Enter workspace"}
          </button>
          <small>Your session is validated by the server.</small>
        </form>
      </div>
    </div>
  );
}
function Dashboard() {
  const [docs, setDocs] = useState<Doc[]>([]),
    [runs, setRuns] = useState<Run[]>([]),
    [status, setStatus] = useState<Status | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const load = () =>
    Promise.all([
      api<Doc[]>("/documents"),
      api<Run[]>("/runs"),
      api<Status>("/status"),
    ])
      .then(([d, r, s]) => {
        setDocs(d);
        setRuns(r);
        setStatus(s);
      })
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, []);
  async function ingest() {
    setBusy(true);
    setError("");
    try {
      await api("/documents/ingest", { method: "POST" });
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Header
        eyebrow="YOUR OPERATIONS AT A GLANCE"
        title="A clearer view of every event."
      >
        <Badge value={status?.mode || "loading"} />
      </Header>
      <ErrorBox error={error} />
      <div className="stats">
        <article>
          <span>Knowledge documents</span>
          <strong>{docs.length}</strong>
          <small>
            {docs.reduce((a, d) => a + d.ingestion.records, 0)} indexed source
            records
          </small>
        </article>
        <article>
          <span>Agent executions</span>
          <strong>{runs.length}</strong>
          <small>Persisted workflow history</small>
        </article>
        <article>
          <span>Awaiting review</span>
          <strong>
            {runs.filter((r) => r.status === "review_required").length}
          </strong>
          <small>Discrepancies need attention</small>
        </article>
      </div>
      <div className="two-columns">
        <section className="card">
          <div className="section-head">
            <h2>Knowledge library</h2>
            <button className="secondary" disabled={busy} onClick={ingest}>
              {busy ? "Indexing…" : "Ingest documents"}
            </button>
          </div>
          {docs.length ? (
            docs.map((d) => (
              <div className="list-row" key={d.id}>
                <div>
                  <strong>{d.name}</strong>
                  <small>
                    {d.ingestion.records} records · {date(d.ingestion.at)}
                  </small>
                </div>
                <Badge value="indexed" />
              </div>
            ))
          ) : (
            <div className="empty">
              Ingest the structured documents to start asking questions.
            </div>
          )}
          <Link className="text-link" to="/knowledge">
            Open Knowledge Assistant →
          </Link>
        </section>
        <section className="card">
          <h2>Integration status</h2>
          {status && (
            <>
              <div className="list-row">
                <span>Gemini</span>
                <Badge
                  value={
                    status.gemini_configured ? "configured" : "not_configured"
                  }
                />
              </div>
              <div className="list-row">
                <span>Google Calendar & Gmail</span>
                <Badge
                  value={
                    status.google_connected ? "connected" : "not_connected"
                  }
                />
              </div>
              <div className="list-row">
                <span>HTTP directory</span>
                <Badge
                  value={
                    status.directory_configured
                      ? "configured"
                      : "not_configured"
                  }
                />
              </div>
              <small>
                Transport: {status.transport}.{" "}
                {status.mode === "fixture"
                  ? "Fixture mode uses synthetic local records and model test doubles."
                  : "Live mode calls configured external services."}
              </small>
            </>
          )}
        </section>
      </div>
      <section className="card">
        <div className="section-head">
          <h2>Recent activity</h2>
          <Link to="/history" className="text-link">
            All executions →
          </Link>
        </div>
        <RunRows runs={runs.slice(0, 4)} />
      </section>
    </>
  );
}
function Knowledge() {
  const [messages, setMessages] = useState<Message[]>([]),
    [question, setQuestion] = useState(""),
    [cid, setCid] = useState<string | null>(null),
    [sessions, setSessions] = useState<{ id: string; created_at: string }[]>(
      [],
    ),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    api<{ id: string; created_at: string }[]>("/conversations")
      .then(async (s) => {
        setSessions(s);
        if (s[0]) {
          setCid(s[0].id);
          setMessages(await api<Message[]>("/conversations/" + s[0].id));
        }
      })
      .catch((e) => setError(e.message));
  }, []);
  async function change(id: string) {
    setError("");
    setCid(id || null);
    if (!id) {
      setMessages([]);
      return;
    }
    setBusy(true);
    try {
      setMessages(await api("/conversations/" + id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function ask(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api<{ conversation_id: string }>("/rag/query", {
        method: "POST",
        body: JSON.stringify({ question, conversation_id: cid }),
      });
      setCid(r.conversation_id);
      setMessages(await api("/conversations/" + r.conversation_id));
      setSessions(await api("/conversations"));
      setQuestion("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Header eyebrow="KNOWLEDGE ASSISTANT" title="Answers you can trace." />
      <div className="section-head">
        <p>Ask about schedules, registration policies, or participants.</p>
        <select
          aria-label="Saved conversation"
          value={cid || ""}
          disabled={busy}
          onChange={(e) => void change(e.target.value)}
        >
          <option value="">New conversation</option>
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {date(s.created_at)}
            </option>
          ))}
        </select>
      </div>
      <ErrorBox error={error} />
      <div className="conversation card">
        {!messages.length && (
          <div className="empty">
            <h2>Start with a question.</h2>
            <p>Try “When does registration close for EVT-101?”</p>
            <div className="suggestions">
              {["What is the refund policy?", "Where is EVT-102 held?"].map(
                (q) => (
                  <button
                    className="secondary"
                    key={q}
                    onClick={() => setQuestion(q)}
                  >
                    {q}
                  </button>
                ),
              )}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <article className={"message " + m.role} key={m.id}>
            <p className="eyebrow">
              {m.role === "user" ? "YOU" : "EVENTOPS KNOWLEDGE"}{" "}
              {m.details?.mode === "fixture" && " / FIXTURE"}
            </p>
            <p className="answer">{m.content}</p>
            {m.details?.supported === false && (
              <Badge value="insufficient_evidence" />
            )}
            {m.evidence.length > 0 && (
              <>
                <small>
                  Retrieved evidence · expand to inspect the original record
                </small>
                <EvidenceList items={m.evidence} />
              </>
            )}
          </article>
        ))}
        {busy && (
          <div role="status" className="empty">
            Retrieving evidence and preparing an answer…
          </div>
        )}
      </div>
      <form className="query-form" onSubmit={ask}>
        <input
          aria-label="Question"
          placeholder="Ask an operational question…"
          required
          minLength={3}
          maxLength={2000}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button disabled={busy || !question.trim()}>
          {busy ? "Working…" : "Ask question"}
        </button>
      </form>
    </>
  );
}
function useRuns() {
  const [runs, setRuns] = useState<Run[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    const load = () =>
      api<Run[]>("/runs")
        .then(setRuns)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    void load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, []);
  return { runs, error, loading };
}
function RunRows({ runs }: { runs: Run[] }) {
  return runs.length ? (
    <div>
      {runs.map((r) => (
        <Link className="run-row" to={"/agent?run=" + r.id} key={r.id}>
          <div>
            <strong>{r.event_id}</strong>
            <p>{r.objective}</p>
            <small>
              {date(r.created_at)} · {r.mode}
            </small>
          </div>
          <Badge value={r.status} />
        </Link>
      ))}
    </div>
  ) : (
    <div className="empty">
      No agent executions yet. Start a verification workflow to build the
      history.
    </div>
  );
}
function Agent() {
  const navigate = useNavigate();
  const { runs } = useRuns();
  const [eid, setEid] = useState("EVT-101"),
    [objective, setObjective] = useState(
      "Prepare a verified attendee list for EVT-101 using calendar invitations, registration emails and the published reference directory.",
    ),
    [selected, setSelected] = useState(
      new URLSearchParams(location.search).get("run") || "",
    ),
    [run, setRun] = useState<Run | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [note, setNote] = useState(""),
    [reviewMessage, setReviewMessage] = useState(""),
    [status, setStatus] = useState<Status | null>(null);
  useEffect(() => {
    api<Status>("/status")
      .then(setStatus)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!selected) return;
    let active = true;
    const load = () =>
      api<Run>("/runs/" + selected)
        .then((r) => {
          if (active) setRun(r);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    void load();
    const id = setInterval(load, 2000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [selected]);
  async function start(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api<Run>("/runs", {
        method: "POST",
        body: JSON.stringify({
          objective,
          event_id: eid,
          idempotency_key: crypto.randomUUID(),
        }),
      });
      setSelected(r.id);
      setRun(r);
      navigate("/agent?run=" + r.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function review(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/runs/" + selected + "/review", {
        method: "POST",
        body: JSON.stringify({ note }),
      });
      setNote("");
      setReviewMessage(
        "Review note recorded. Correct source data and rerun to resolve discrepancies.",
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <Header
        eyebrow="AGENT WORKSPACE"
        title="From request to verified record."
      >
        <Badge value={status?.mode || "loading"} />
      </Header>
      <ErrorBox error={error} />
      <div className="two-columns">
        <section className="card">
          <h2>Define the objective</h2>
          <form onSubmit={start}>
            <label>
              Event
              <select
                value={eid}
                onChange={(e) => {
                  setEid(e.target.value);
                  setObjective(
                    "Prepare a verified attendee list for " +
                      e.target.value +
                      " using calendar invitations, registration emails and the published reference directory.",
                  );
                }}
              >
                {["EVT-101", "EVT-102", "EVT-103"].map((id) => (
                  <option key={id}>{id}</option>
                ))}
              </select>
            </label>
            <label>
              Operational request
              <textarea
                rows={5}
                minLength={10}
                maxLength={2000}
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                required
              />
            </label>
            <button disabled={busy}>
              {busy ? "Starting…" : "Run verification"}
            </button>
          </form>
          <p className="muted">
            The agent selects read-only tools. Deterministic rules decide
            verification outcomes.
          </p>
        </section>
        <section className="card">
          <h2>Connected sources</h2>
          {[
            "Google Calendar",
            "Gmail registration messages",
            "Published HTTP directory",
          ].map((t) => (
            <div className="list-row" key={t}>
              <span>{t}</span>
              <span className="source-dot" />
            </div>
          ))}
          {status?.mode === "fixture" ? (
            <p className="muted">
              Fixture mode: synthetic records, with no external tool calls.
            </p>
          ) : (
            <>
              <p className="muted">
                Use a dedicated test account with fictional event data.
              </p>
              {status?.transport === "direct" && (
                <a
                  className="button secondary"
                  href={API + "/api/integrations/google/start"}
                >
                  Connect Google test account
                </a>
              )}
              {status?.transport === "n8n" && (
                <p>Configure Google credentials in the n8n workflows.</p>
              )}
            </>
          )}
        </section>
      </div>
      <section className="card">
        <div className="section-head">
          <h2>Execution detail</h2>
          <select
            aria-label="Agent execution"
            value={selected}
            onChange={(e) => {
              setSelected(e.target.value);
              setReviewMessage("");
            }}
          >
            <option value="">Select execution</option>
            {runs.map((r) => (
              <option value={r.id} key={r.id}>
                {r.event_id} · {date(r.created_at)} · {r.status}
              </option>
            ))}
          </select>
        </div>
        {run ? (
          <>
            <div className="run-heading">
              <p>{run.objective}</p>
              <Badge value={run.status} />
            </div>
            {run.state.plan && (
              <p className="muted">
                Plan: {run.state.plan.tools.join(" → ")}.{" "}
                {run.state.plan.rationale}
              </p>
            )}
            <ErrorBox error={run.error || ""} />
            <div className="timeline">
              {run.events?.map((e) => (
                <div className="timeline-row" key={e.id}>
                  <span className="timeline-dot" />
                  <div>
                    <strong>{e.stage.replaceAll("_", " ")}</strong>
                    <Badge value={e.outcome} />
                    <small>{date(e.created_at)}</small>
                    <details>
                      <summary>Inspect execution data</summary>
                      <pre>{JSON.stringify(e.detail, null, 2)}</pre>
                    </details>
                  </div>
                </div>
              ))}
            </div>
            {run.status === "review_required" && (
              <form onSubmit={review}>
                <label>
                  Human review note
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    required
                    minLength={10}
                    placeholder="Record the discrepancy and next action…"
                  />
                </label>
                <button className="secondary">Save review note</button>
                <p role="status">{reviewMessage}</p>
              </form>
            )}
            <Link className="button secondary" to={"/results?run=" + run.id}>
              View verification results
            </Link>
          </>
        ) : (
          <div className="empty">
            Start a workflow or select a previous execution.
          </div>
        )}
      </section>
    </>
  );
}
function Results() {
  const { runs, error: loadError } = useRuns();
  const [selected, setSelected] = useState(
      new URLSearchParams(location.search).get("run") || "",
    ),
    [results, setResults] = useState<Result[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false),
    [filter, setFilter] = useState("all");
  useEffect(() => {
    if (!selected && runs[0]) setSelected(runs[0].id);
  }, [runs, selected]);
  useEffect(() => {
    if (!selected) return;
    let active = true;
    setLoading(true);
    const load = () =>
      api<Result[]>("/runs/" + selected + "/results")
        .then((r) => {
          if (active) setResults(r);
        })
        .catch((e) => {
          if (active) setError(e.message);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    void load();
    const id = setInterval(load, 4000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [selected]);
  const current = runs.find((r) => r.id === selected);
  async function download() {
    try {
      const response = await fetch(
        API + "/api/runs/" + selected + "/export.csv",
        { credentials: "include" },
      );
      if (!response.ok)
        throw new Error("Export failed. Sign in and try again.");
      const url = URL.createObjectURL(await response.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "verified-" + current?.event_id + ".csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <Header
        eyebrow="VERIFICATION RESULTS"
        title="Confidence, record by record."
      >
        <button className="secondary" onClick={download} disabled={!selected}>
          Export verified CSV
        </button>
      </Header>
      <ErrorBox error={error || loadError} />
      <div className="section-head">
        <select
          aria-label="Result execution"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Select execution</option>
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              {r.event_id} · {date(r.created_at)} · {r.mode}
            </option>
          ))}
        </select>
        {current && <Badge value={current.status} />}
      </div>
      <div className="filters">
        {["all", "verified", "review_required", "unverified"].map((f) => (
          <button
            className={filter === f ? "" : "secondary"}
            key={f}
            onClick={() => setFilter(f)}
          >
            {f.replaceAll("_", " ")} ·{" "}
            {f === "all"
              ? results.length
              : results.filter((r) => r.status === f).length}
          </button>
        ))}
      </div>
      {loading ? (
        <Loading />
      ) : results.length ? (
        <section className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Participant</th>
                <th>Organization</th>
                <th>Status</th>
                <th>Evidence & explanation</th>
              </tr>
            </thead>
            <tbody>
              {results
                .filter((r) => filter === "all" || r.status === filter)
                .map((r) => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.record.name || "Name not supplied"}</strong>
                      <small>{r.record.email || "Email not supplied"}</small>
                      <small>
                        {r.record.participant_id || "No participant ID"}
                      </small>
                    </td>
                    <td>{r.record.organization || "Not supplied"}</td>
                    <td>
                      <Badge value={r.status} />
                    </td>
                    <td>
                      <details>
                        <summary>{r.reasons[0]}</summary>
                        <ul>
                          {r.reasons.map((s) => (
                            <li key={s}>{s}</li>
                          ))}
                        </ul>
                        <EvidenceList items={r.evidence} />
                      </details>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>
      ) : (
        <div className="card empty">
          No verification records yet. Run a workflow and inspect its completion
          status.
        </div>
      )}
    </>
  );
}
function History() {
  const { runs, error, loading } = useRuns();
  return (
    <>
      <Header
        eyebrow="EXECUTION HISTORY"
        title="A complete account of the work."
      />
      <ErrorBox error={error} />
      <section className="card">
        {loading ? <Loading /> : <RunRows runs={runs} />}
      </section>
    </>
  );
}
export function App() {
  const [session, setSession] = useState<{
      username: string;
      mode?: string;
    } | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const check = () =>
    api<{ username: string; mode: string }>("/session")
      .then(setSession)
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  useEffect(() => {
    void check();
  }, []);
  if (loading) return <Loading />;
  if (!session) return <Login onLogin={() => void check()} />;
  async function logout() {
    try {
      await api("/session", { method: "DELETE" });
      setSession(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <div className="app">
      <aside>
        <Link className="brand" to="/">
          <span className="brand-mark">e</span>
          <span>
            EventOps
            <br />
            <small>INTELLIGENCE</small>
          </span>
        </Link>
        <p className="eyebrow nav-label">WORKSPACE</p>
        <nav>
          {[
            ["/", "Overview", "◉"],
            ["/knowledge", "Knowledge Assistant", "◎"],
            ["/agent", "Agent Workspace", "◇"],
            ["/results", "Verification Results", "✓"],
            ["/history", "Execution History", "◷"],
          ].map(([to, label, icon]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <Badge value={session.mode || "live"} />
          <p>{session.username}</p>
          <button className="secondary" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main>
        <div className="topbar">
          <span>Operations workspace</span>
          <span>Evidence first. Always.</span>
        </div>
        <ErrorBox error={error} />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/agent" element={<Agent />} />
          <Route path="/results" element={<Results />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <footer>
          EventOps Intelligence{" "}
          <span>Fictional event data · traceable operations</span>
        </footer>
      </main>
    </div>
  );
}
const root = document.getElementById("root");
if (root)
  createRoot(root).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>,
  );
