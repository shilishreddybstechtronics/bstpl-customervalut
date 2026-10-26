const RENDER_BACKEND_URL = "https://bstpl-customervalut-l40y.onrender.com";
const isLocal = window.location.protocol === "file:" ||
  ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") && window.location.port !== "8000");
const API_URL = window.API_URL || localStorage.getItem("API_URL") || (
  isLocal ? "http://127.0.0.1:8000" : (window.location.origin.includes("onrender.com") ? "" : RENDER_BACKEND_URL)
);

const $ = (id) => document.getElementById(id);
const ID_RE = /^[A-Za-z0-9_.-]{3,30}$/;

// Already signed in? Go straight to the dashboard.
if (localStorage.getItem("token")) location.replace("dashboard.html");

let mode = "login";

/* ---------- Sign in <-> Create ID ---------- */
function setMode(next) {
  mode = next;
  const isLogin = next === "login";
  $("name-wrap").hidden = isLogin;
  $("id-hint").hidden = isLogin;
  $("pw-hint").hidden = isLogin;
  $("meter").hidden = isLogin;
  $("f-pw").autocomplete = isLogin ? "current-password" : "new-password";
  $("f-id").placeholder = isLogin ? "Your login ID" : "Choose a login ID";
  $("f-pw").placeholder = isLogin ? "Your password" : "Choose a password";
  $("title").textContent = isLogin ? "Sign in" : "Create your ID";
  $("sub").textContent = isLogin ? "Enter your ID and password to continue." : "Choose how you will sign in to CustomerVault.";
  $("submit").querySelector(".label").textContent = isLogin ? "Sign in" : "Create my ID";
  $("switch-text").textContent = isLogin ? "New to CustomerVault?" : "Already have an ID?";
  $("switch-btn").textContent = isLogin ? "Create your ID" : "Sign in";
  showError("");
  (isLogin ? $("f-id") : $("f-name")).focus();
}
$("switch-btn").addEventListener("click", () => setMode(mode === "login" ? "register" : "login"));

/* ---------- Password helpers ---------- */
$("toggle-pw").addEventListener("click", (e) => {
  const show = $("f-pw").type === "password";
  $("f-pw").type = show ? "text" : "password";
  e.currentTarget.textContent = show ? "Hide" : "Show";
  e.currentTarget.setAttribute("aria-label", show ? "Hide password" : "Show password");
});

function strength(pw) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw) || pw.length >= 14) s++;
  return s;
}
$("f-pw").addEventListener("input", () => { $("meter").dataset.s = strength($("f-pw").value); });

// Caps Lock warning
["keydown", "keyup"].forEach((ev) =>
  $("f-pw").addEventListener(ev, (e) => { $("caps").hidden = !(e.getModifierState && e.getModifierState("CapsLock")); })
);
$("f-pw").addEventListener("blur", () => { $("caps").hidden = true; });

/* ---------- Errors ---------- */
function showError(msg, fields = []) {
  $("error").textContent = msg;
  document.querySelectorAll("input").forEach((i) => i.classList.remove("invalid"));
  fields.forEach((i) => i.classList.add("invalid"));
  if (msg) {
    $("card").classList.remove("shake");
    void $("card").offsetWidth;
    $("card").classList.add("shake");
    window.Scene3D && window.Scene3D.setMode("error");
    if (fields[0]) fields[0].focus();
  }
}
document.querySelectorAll("input").forEach((i) => i.addEventListener("input", () => { if ($("error").textContent) showError(""); }));

/* ---------- Submit ---------- */
$("auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");
  const name = $("f-name").value.trim();
  const userId = $("f-id").value.trim();
  const password = $("f-pw").value;

  if (mode === "register" && !name) return showError("Please enter your name.", [$("f-name")]);
  if (!userId) return showError("Please enter your login ID.", [$("f-id")]);
  if (mode === "register" && userId !== "0001") return showError("The first account must use the master ID 0001.", [$("f-id")]);
  if (mode === "register" && !ID_RE.test(userId))
    return showError("Your ID must be 3–30 characters: letters, numbers, _ . or -", [$("f-id")]);
  if (!password) return showError("Please enter your password.", [$("f-pw")]);
  if (mode === "register" && password.length < 8) return showError("Your password needs at least 8 characters.", [$("f-pw")]);

  const btn = $("submit");
  btn.disabled = true;
  btn.classList.add("loading");
  try {
    const res = await fetch(`${API_URL}/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mode === "login" ? { user_id: userId, password } : { name, user_id: userId, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(Array.isArray(data.detail) ? "Please check your details and try again." : data.detail || "Something went wrong. Please try again.");
    }
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    btn.classList.remove("loading");
    btn.classList.add("done");
    btn.querySelector(".label").textContent = "Signed in";
    window.Scene3D && window.Scene3D.setMode("success");
    setTimeout(() => location.replace("dashboard.html"), 700);
  } catch (err) {
    const offline = err instanceof TypeError;
    showError(offline ? "Can't reach the server. Make sure the backend is running." : err.message,
      mode === "login" ? [$("f-id")] : []);
    btn.disabled = false;
    btn.classList.remove("loading");
  }
});

/* ---------- Database status ---------- */
(async function () {
  try {
    const res = await fetch(`${API_URL}/health/db`);
    if (!res.ok) throw new Error();
    $("db-status").textContent = "Connected to database";
    $("db-status").className = "db ok";
  } catch {
    $("db-status").textContent = "Server or database is offline";
    $("db-status").className = "db fail";
  }
})();

$("f-id").focus();

/* ---------- Minimal 3D: card leans toward the pointer, shapes spin a little while typing ---------- */
if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  window.addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse") return;
    const x = e.clientX / window.innerWidth - 0.5, y = e.clientY / window.innerHeight - 0.5;
    $("tilt").style.setProperty("--ry", `${(x * 7).toFixed(2)}deg`);
    $("tilt").style.setProperty("--rx", `${(-y * 5).toFixed(2)}deg`);
  });
  document.addEventListener("pointerleave", () => {
    $("tilt").style.setProperty("--ry", "0deg");
    $("tilt").style.setProperty("--rx", "0deg");
  });
}
document.querySelectorAll("input").forEach((i) => i.addEventListener("input", () => window.Scene3D && window.Scene3D.nudge()));
