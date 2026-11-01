(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  if (params.get("embed") === "1") document.body.classList.add("embed");

  const el = {
    card: document.querySelector(".card"), brand: $("brand"), title: $("title"),
    subtitle: $("subtitle"), img: $("captcha"), prompt: $("prompt"), answer: $("answer"),
    submit: $("submit"), status: $("status"), refresh: $("refresh"),
    profileSel: $("profile-select"), kindSel: $("kind-select"),
  };
  const state = { profile: null, token: null, kind: params.get("kind") || "", busy: false, done: false };

  const getJSON = async (url, opts) => {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(String(res.status));
    return res.json();
  };

  const setStatus = (text, cls = "") => { el.status.textContent = text; el.status.className = "status " + cls; };

  function showChallenge(c) {
    state.token = c.token;
    el.img.src = c.image;
    el.img.classList.remove("loading");
    el.prompt.textContent = c.prompt;
    el.answer.value = "";
    el.answer.inputMode = c.kind === "math" ? "numeric" : "text";
    el.answer.placeholder = c.kind === "math" ? "Answer" : "Characters";
  }

  async function loadChallenge() {
    el.img.classList.add("loading");
    const q = new URLSearchParams({ profile: state.profile.key });
    if (state.kind) q.set("kind", state.kind);
    showChallenge(await getJSON("/api/challenge?" + q));
  }

  async function submit() {
    if (state.busy || state.done || !el.answer.value.trim()) return;
    state.busy = true; el.submit.disabled = true;
    try {
      const r = await getJSON("/api/verify", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: state.token, answer: el.answer.value, profile: state.profile.key, kind: state.kind || undefined }),
      });
      if (r.ok) {
        state.done = true;
        setStatus(state.profile.success, "ok");
        el.answer.disabled = true; el.refresh.disabled = true;
        return;
      }
      const msg = { expired: "This challenge expired. Here is a new one.", exhausted: "Too many attempts. Here is a new challenge." }[r.reason];
      setStatus(msg || state.profile.failure, "error");
      el.card.classList.remove("shake"); void el.card.offsetWidth; el.card.classList.add("shake");
      if (r.challenge) showChallenge(r.challenge);
      el.answer.focus();
    } catch (e) {
      setStatus("Couldn't reach the server. Try again.", "error");
    } finally {
      state.busy = false; el.submit.disabled = state.done;
    }
  }

  function applyProfile(p) {
    state.profile = p;
    for (const [k, v] of Object.entries(p.theme)) document.documentElement.style.setProperty(k, v);
    document.title = p.brand + " · Verification";
    el.brand.textContent = p.brand;
    el.title.textContent = p.title;
    el.subtitle.textContent = p.subtitle;
    el.submit.textContent = p.button;
  }

  async function init() {
    const list = await getJSON("/api/profiles");
    const key = params.get("profile") || list[0].key;
    el.profileSel.innerHTML = list.map((p) => `<option value="${p.key}">${p.key}</option>`).join("");
    el.profileSel.value = key;
    el.kindSel.value = state.kind;
    applyProfile(await getJSON("/api/profile/" + encodeURIComponent(key)));
    await loadChallenge();
  }

  const navigate = () => {
    const q = new URLSearchParams(location.search);
    q.set("profile", el.profileSel.value);
    el.kindSel.value ? q.set("kind", el.kindSel.value) : q.delete("kind");
    location.search = q.toString();
  };
  el.profileSel.addEventListener("change", () => { el.kindSel.value = ""; navigate(); });
  el.kindSel.addEventListener("change", navigate);
  el.refresh.addEventListener("click", () => { setStatus(""); loadChallenge(); });
  el.submit.addEventListener("click", submit);
  el.answer.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });

  init().catch(() => setStatus("Couldn't load the verification. Reload the page.", "error"));
})();
