import { ChangeEvent, useState } from "react";
import { API_BASE, postJson } from "./api";

type JsonObject = Record<string, any>;
const PROFILE_EXAMPLE = {
  username: "sample_user",
  full_name: "Sample User",
  biography: "A short biography.",
  external_url: "https://example.com",
  followers: 150,
  followees: 180,
  mediacount: 25,
  posts_count: 25,
  stories_count: 3,
  is_private: false,
  is_verified: false,
};
const pretty = (value: unknown) =>
  typeof value === "object"
    ? JSON.stringify(value, null, 2)
    : String(value ?? "—");
const percent = (value: unknown) => {
  const n = Number(value);
  return Number.isFinite(n) ? `${(n * 100).toFixed(1)}%` : "—";
};
const title = (value: unknown) =>
  String(value ?? "—")
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

function LinkList({ items }: { items?: unknown }) {
  if (!Array.isArray(items) || !items.length)
    return <p className="muted">No links found.</p>;
  return (
    <ul className="link-list">
      {items.map((item, i) => {
        const x = item as JsonObject;
        const url = String(x.url ?? x.source ?? x.explorer_url ?? "");
        return (
          <li key={`${url}-${i}`}>
            {url ? (
              <a href={url} target="_blank" rel="noreferrer">
                {String(x.title ?? x.provider ?? x.effect ?? url)}
              </a>
            ) : (
              pretty(item)
            )}
          </li>
        );
      })}
    </ul>
  );
}

function ProfileResult({
  result,
  profile,
  index,
}: {
  result: JsonObject;
  profile?: JsonObject;
  index: number;
}) {
  const probability = Number(result.probability_fake ?? result.risk_score ?? 0);
  const fake = Boolean(result.is_fake ?? probability >= 0.6);
  const summary = {
    Username: profile?.username ?? result.username,
    "Full Name": profile?.full_name ?? "N/A",
    Followers: Number(profile?.followers ?? 0),
    Following: Number(profile?.followees ?? 0),
    Posts: Number(profile?.mediacount ?? 0),
    Stories: Number(profile?.stories_count ?? 0),
    Private: profile?.is_private ? "Yes" : "No",
    Verified: profile?.is_verified ? "Yes" : "No",
    "Has Link": Boolean(profile?.external_url),
    "Has Bio": String(profile?.biography ?? "").length > 10,
  };
  return (
    <article className="card profile-card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Profile {index + 1}</span>
          <h3>{String(summary.Username || "Unnamed account")}</h3>
        </div>
        <span className={`pill ${fake ? "danger" : "safe"}`}>
          {fake ? "FAKE / HIGH RISK" : "REAL-APPEARING"}
        </span>
      </div>
      <div className="metrics">
        <Metric
          label="Fake probability"
          value={percent(result.probability_fake)}
        />
        <Metric label="Verdict" value={fake ? "FAKE" : "REAL"} />
        <Metric label="Confidence" value={result.confidence} />
        <Metric
          label="Risk score"
          value={percent(result.risk_score ?? result.probability_fake)}
        />
        <Metric
          label="Classification"
          value={result.classification ?? "supervised-only"}
        />
        <Metric
          label="Cluster"
          value={result.cluster_label ?? "not calculated"}
        />
      </div>
      <div className="likelihood">
        <div className="likelihood-label">
          <b>Fake likelihood</b>
          <span>{percent(probability)}</span>
        </div>
        <div className="bar">
          <i
            style={{
              width: `${Math.max(0, Math.min(100, probability * 100))}%`,
              background: fake ? "#fb7185" : "#4ade80",
            }}
          />
        </div>
        <div className="scale">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      </div>
      <details open>
        <summary>Profile summary</summary>
        <dl>
          {Object.entries(summary).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
      </details>
      <details>
        <summary>Advanced evidence</summary>
        <pre>
          {pretty({
            "Anomaly score": result.anomaly_score,
            "Cluster ID": result.cluster_id,
            "Image analysis": result.image_analysis,
            "Reverse image analysis": result.reverse_image_analysis,
            "Network analysis": result.network_analysis,
          })}
        </pre>
      </details>
      <p className={fake ? "error" : "success"}>
        {fake
          ? "High risk of being fake or bot."
          : "Profile appears legitimate."}
      </p>
    </article>
  );
}
function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <b>{label}</b>
      <span>{String(value ?? "—")}</span>
    </div>
  );
}

function PostResult({ result }: { result: JsonObject }) {
  const report = (result.report ?? {}) as JsonObject,
    post = (result.post ?? {}) as JsonObject;
  const content = (report.content_analysis ??
    result.content_analysis ??
    {}) as JsonObject;
  const image = (result.image_analysis ?? {}) as JsonObject,
    blockchain = (result.blockchain ?? {}) as JsonObject;
  const imageRef = String(result.image_reference ?? post.image_reference ?? "");
  const imageUrl = imageRef
    ? new URL(imageRef, API_BASE || window.location.origin).toString()
    : "";
  const verdictClass =
    report.verdict === "likely-fraudulent-or-misleading"
      ? "error"
      : report.verdict === "needs-verification"
        ? "warning"
        : "success";
  return (
    <section className="result-stack">
      {imageUrl && (
        <img
          className="post-image"
          src={imageUrl}
          alt="Validated public Instagram post media"
          onError={(e) => {
            e.currentTarget.hidden = true;
          }}
        />
      )}
      <div className="metrics post-metrics">
        <Metric label="Research status" value={title(result.research_status)} />
        <Metric
          label="Wallets found"
          value={
            Array.isArray(blockchain.addresses_found)
              ? blockchain.addresses_found.length
              : 0
          }
        />
        <Metric label="Image risk" value={percent(image.image_risk)} />
      </div>
      <article className={`card verdict-card ${verdictClass}`}>
        <span className="eyebrow">Evidence report</span>
        <h2>{String(report.conclusion ?? "Analysis complete")}</h2>
        <p>{String(report.basis ?? "")}</p>
        <div className="metrics">
          <Metric label="Assessment" value={title(report.verdict)} />
          <Metric label="Risk score" value={percent(report.risk_score)} />
          <Metric label="Confidence" value={title(report.confidence)} />
          <Metric label="Content risk" value={percent(content.content_risk)} />
        </div>
        {Array.isArray(report.claims_detected) &&
          report.claims_detected.join(", ") !== "general-claim" && (
            <p>
              <b>Claim types:</b> {report.claims_detected.join(", ")}
            </p>
          )}
      </article>
      <div className="result-grid">
        <article className="card">
          <h3>Post details</h3>
          <dl>
            {["title", "url", "accessible", "html_bytes"].map((key) => (
              <div key={key}>
                <dt>{title(key)}</dt>
                <dd>{String(post[key] ?? "—")}</dd>
              </div>
            ))}
          </dl>
        </article>
        <article className="card">
          <h3>Post content analysis</h3>
          <p>
            <b>Content risk:</b> {percent(content.content_risk)}
          </p>
          <p>
            {String(content.character_count ?? 0)} characters ·{" "}
            {String(content.exclamation_count ?? 0)} exclamations
          </p>
          {Array.isArray(content.signals) && content.signals.length ? (
            <ul>
              {content.signals.map((s: JsonObject) => (
                <li key={s.signal}>
                  <b>{title(s.signal)}:</b> {s.matches?.join(", ")}
                </li>
              ))}
            </ul>
          ) : (
            <p>No high-risk content patterns detected.</p>
          )}
          <small>{String(content.method ?? "")}</small>
          {content.supervised_model?.available ? (
            <p>
              <b>Supervised fake probability:</b>{" "}
              {percent(content.supervised_model.fake_probability)}
            </p>
          ) : (
            <p className="muted">
              No trained post-content model installed; rules used.
            </p>
          )}
        </article>
      </div>
      <div className="result-grid">
        <article className="card">
          <h3>Proof and source trail</h3>
          {(report.proof ?? []).map((item: JsonObject, i: number) => (
            <p key={i}>
              <b>{title(item.effect)}:</b> {item.finding}
              {item.source && (
                <>
                  {" "}
                  —{" "}
                  <a href={item.source} target="_blank" rel="noreferrer">
                    source
                  </a>
                </>
              )}
            </p>
          ))}
          <h4>Reverse-image research</h4>
          <LinkList items={result.reverse_image_links} />
          <h4>Search providers</h4>
          {(result.search_engines ?? []).map(
            (engine: JsonObject, i: number) => (
              <div key={i}>
                <b>{engine.provider}</b>
                {engine.error && <p className="muted">{engine.error}</p>}
                <LinkList items={engine.results} />
              </div>
            ),
          )}
        </article>
        <article className="card">
          <h3>Official-source verification</h3>
          {(report.official_source_verification ?? []).length ? (
            (report.official_source_verification as JsonObject[]).map(
              (group, i) => (
                <div key={i}>
                  <h4>{title(group.claim_type)}</h4>
                  {(group.sources ?? []).map(
                    (engine: JsonObject, j: number) => (
                      <div key={j}>
                        <b>{engine.provider}</b>
                        {!engine.configured && (
                          <p className="muted">{engine.note}</p>
                        )}
                        <LinkList items={engine.results} />
                      </div>
                    ),
                  )}
                </div>
              ),
            )
          ) : (
            <p>No job, offer, payment, or news claim detected.</p>
          )}
        </article>
      </div>
      <div className="result-grid">
        <article className="card">
          <h3>Blockchain source tracing</h3>
          <pre>{pretty(blockchain)}</pre>
        </article>
        <article className="card">
          <h3>Image provenance</h3>
          <pre>
            {pretty(
              report.image_provenance ?? {
                status: "No provenance evidence available.",
              },
            )}
          </pre>
        </article>
      </div>
      <article className="card">
        <h3>Limitations</h3>
        <ul>
          {(
            report.limitations ?? [
              "Results are triage signals, not proof of identity or fraud.",
            ]
          ).map((x: unknown) => (
            <li key={String(x)}>{String(x)}</li>
          ))}
        </ul>
      </article>
      <details className="card">
        <summary>Raw response</summary>
        <pre>{pretty(result)}</pre>
      </details>
    </section>
  );
}

export function App() {
  const [tab, setTab] = useState<"profiles" | "posts">("profiles"),
    [inputTab, setInputTab] = useState<"paste" | "upload" | "sample">("paste");
  const [profileJson, setProfileJson] = useState(
      JSON.stringify(PROFILE_EXAMPLE, null, 2),
    ),
    [postUrl, setPostUrl] = useState("");
  const [result, setResult] = useState<JsonObject | null>(null),
    [profiles, setProfiles] = useState<JsonObject[]>([]),
    [error, setError] = useState(""),
    [warnings, setWarnings] = useState<string[]>([]),
    [fileMessages, setFileMessages] = useState<string[]>([]),
    [loading, setLoading] = useState(false);
  const validate = (payload: unknown) => {
    const list = Array.isArray(payload) ? payload : [payload];
    if (
      !list.length ||
      list.some((x) => !x || typeof x !== "object" || Array.isArray(x))
    )
      throw new Error("Use one profile object or an array of profile objects.");
    const nextWarnings: string[] = [];
    list.forEach((x, i) => {
      const p = x as JsonObject;
      if (!String(p.username ?? "").trim())
        throw new Error(`Profile ${i + 1}: username is required.`);
      if (
        p.followers === undefined ||
        p.followees === undefined ||
        p.mediacount === undefined
      )
        nextWarnings.push(
          `Profile ${i + 1}: missing numeric fields default to 0.`,
        );
      if (p.is_private === undefined || p.is_verified === undefined)
        nextWarnings.push(
          `Profile ${i + 1}: missing boolean fields default to false.`,
        );
    });
    setWarnings(nextWarnings);
    return list as JsonObject[];
  };
  async function analyzeProfile() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const list = validate(JSON.parse(profileJson));
      setProfiles(list);
      setResult(
        await postJson<JsonObject>(
          list.length > 1
            ? "/api/v1/profiles/batch"
            : "/api/v1/profiles/analyze",
          list.length > 1 ? { profiles: list } : { profile: list[0] },
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invalid JSON or request.");
    } finally {
      setLoading(false);
    }
  }
  async function loadSample() {
    setError("");
    try {
      const r = await fetch("/sample.json");
      if (!r.ok) throw new Error();
      const data = await r.json();
      setProfileJson(JSON.stringify(data, null, 2));
      setInputTab("paste");
    } catch {
      setProfileJson(JSON.stringify(PROFILE_EXAMPLE, null, 2));
      setInputTab("paste");
      setError(
        "sample.json was not found; loaded the built-in example instead.",
      );
    }
  }
  function uploadJson(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;
    setFileMessages([]);
    const loaded: JsonObject[] = [];
    let remaining = files.length;
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const list = validate(JSON.parse(String(reader.result)));
          loaded.push(...list);
          setFileMessages((m) => [
            ...m,
            `Loaded ${list.length} profile(s) from ${file.name}.`,
          ]);
        } catch (e) {
          setFileMessages((m) => [
            ...m,
            `Error reading ${file.name}: ${e instanceof Error ? e.message : "invalid JSON"}`,
          ]);
        } finally {
          remaining -= 1;
          if (!remaining && loaded.length) {
            setProfiles(loaded);
            setProfileJson(
              JSON.stringify(loaded.length === 1 ? loaded[0] : loaded, null, 2),
            );
          }
        }
      };
      reader.readAsText(file);
    });
    event.target.value = "";
  }
  async function analyzePost() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await postJson<JsonObject>("/api/v1/posts/analyze", {
          post_url: postUrl.trim(),
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Post analysis failed.");
    } finally {
      setLoading(false);
    }
  }
  const batch = result?.results as JsonObject[] | undefined;
  let readyCount = 0;
  try {
    const payload = JSON.parse(profileJson);
    const list = Array.isArray(payload) ? payload : [payload];
    readyCount =
      list.length &&
      list.every(
        (x) =>
          x &&
          typeof x === "object" &&
          !Array.isArray(x) &&
          String((x as JsonObject).username ?? "").trim(),
      )
        ? list.length
        : 0;
  } catch {
    readyCount = 0;
  }
  return (
    <main>
      <header>
        <span className="eyebrow">AI-assisted safety research</span>
        <h1>Fake Profile Detector</h1>
        <p>
          Detect suspicious Instagram profiles and investigate public posts with
          transparent evidence.
        </p>
      </header>
      <nav>
        <button
          className={tab === "profiles" ? "active" : ""}
          onClick={() => {
            setTab("profiles");
            setError("");
          }}
        >
          Account analysis
        </button>
        <button
          className={tab === "posts" ? "active" : ""}
          onClick={() => {
            setTab("posts");
            setError("");
          }}
        >
          Post analysis
        </button>
      </nav>
      {tab === "profiles" ? (
        <>
          <aside className="help">
            <h3>How to use</h3>
            <p>
              Paste raw JSON, upload one or more files, or load sample.json.
              Each payload can be one profile or an array.
            </p>
            <ul>
              <li>
                <code>username</code> is required
              </li>
              <li>followers, followees, mediacount are numeric</li>
              <li>is_private and is_verified are boolean</li>
              <li>missing optional values default safely</li>
            </ul>
            <details>
              <summary>Expected JSON template</summary>
              <pre>{pretty(PROFILE_EXAMPLE)}</pre>
            </details>
          </aside>
          <section className="panel">
            <div className="tabs">
              {(["paste", "upload", "sample"] as const).map((x) => (
                <button
                  key={x}
                  className={inputTab === x ? "active" : "secondary"}
                  onClick={() => setInputTab(x)}
                >
                  {x === "paste"
                    ? "Paste JSON"
                    : x === "upload"
                      ? "Upload files"
                      : "sample.json"}
                </button>
              ))}
            </div>
            {inputTab === "paste" && (
              <>
                <label htmlFor="profile-json">Paste your JSON</label>
                <textarea
                  id="profile-json"
                  value={profileJson}
                  onChange={(e) => setProfileJson(e.target.value)}
                  spellCheck={false}
                />
                <p className="muted">
                  {readyCount
                    ? `${readyCount} profile(s) ready`
                    : "Enter valid profile JSON to continue."}
                </p>
              </>
            )}
            {inputTab === "upload" && (
              <>
                <label className="upload-drop">
                  Choose one or more .json files
                  <input
                    type="file"
                    accept=".json,application/json"
                    multiple
                    onChange={uploadJson}
                  />
                </label>
                {fileMessages.map((m, i) => (
                  <p
                    className={m.startsWith("Error") ? "error" : "success"}
                    key={i}
                  >
                    {m}
                  </p>
                ))}
              </>
            )}
            {inputTab === "sample" && (
              <div className="sample-box">
                <p>Load the bundled sample profile payload.</p>
                <button onClick={loadSample}>Load sample.json</button>
              </div>
            )}
            <button onClick={analyzeProfile} disabled={loading || !readyCount}>
              {loading
                ? "Analyzing…"
                : `Analyze ${readyCount || ""} profile${readyCount === 1 ? "" : "s"}`}
            </button>
          </section>
        </>
      ) : (
        <section className="panel">
          <h2>Post analysis</h2>
          <p className="muted">
            Research a public Instagram post, reel, or video using bounded
            public metadata and search providers. Private posts and login walls
            are not bypassed.
          </p>
          <label htmlFor="post-url">Instagram post link</label>
          <input
            id="post-url"
            value={postUrl}
            onChange={(e) => setPostUrl(e.target.value)}
            placeholder="https://www.instagram.com/p/POST_ID/"
          />
          <button onClick={analyzePost} disabled={loading || !postUrl.trim()}>
            {loading ? "Fetching public evidence…" : "Run post analysis"}
          </button>
        </section>
      )}
      {warnings.map((w) => (
        <p className="warning" key={w}>
          {w}
        </p>
      ))}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {result &&
        (tab === "posts" ? (
          result.post?.accessible === false ? (
            <>
              <p className="error">
                {String(
                  result.post.error ?? "Public post metadata was unavailable.",
                )}
              </p>
              <PostResult result={result} />
            </>
          ) : (
            <PostResult result={result} />
          )
        ) : batch ? (
          <section className="result-stack">
            <div className="summary">
              <strong>
                {String(result.count ?? batch.length)} profiles analyzed
              </strong>
              <span>Compare risk, anomaly, and enrichment signals below.</span>
            </div>
            {batch.map((item, i) => (
              <ProfileResult
                key={i}
                result={item}
                profile={profiles[i]}
                index={i}
              />
            ))}
          </section>
        ) : (
          <ProfileResult result={result} profile={profiles[0]} index={0} />
        ))}
      <footer>
        Model-assisted triage only. Results are not definitive fraud
        determinations. Use for research and safety.
      </footer>
    </main>
  ); 
}
