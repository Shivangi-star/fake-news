const scanTabs = document.querySelectorAll(".scan-tab");
const panelImage = document.getElementById("panel-image");
const panelText = document.getElementById("panel-text");
const imageInput = document.getElementById("image-input");
const dropzone = document.getElementById("dropzone");
const dropzoneInner = document.getElementById("dropzone-inner");
const imagePreview = document.getElementById("image-preview");
const imageCaption = document.getElementById("image-caption");
const newsText = document.getElementById("news-text");
const btnScanImage = document.getElementById("btn-scan-image");
const btnScanText = document.getElementById("btn-scan-text");
const results = document.getElementById("results");
const errorBanner = document.getElementById("error-banner");
const imageMeta = document.getElementById("image-meta");

let selectedFile = null;
const MAX_BYTES = 10 * 1024 * 1024;

scanTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const mode = tab.dataset.tab;
    scanTabs.forEach((t) => t.classList.toggle("active", t === tab));
    panelImage.classList.toggle("hidden", mode !== "image");
    panelText.classList.toggle("hidden", mode !== "text");
    hideError();
  });
});

function hideError() {
  errorBanner.classList.add("hidden");
  errorBanner.textContent = "";
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove("hidden");
  results.classList.add("hidden");
}

function setLoading(button, loading) {
  const label = button.querySelector(".btn-label");
  const spinner = button.querySelector(".spinner");
  button.disabled = loading || (button === btnScanImage && !selectedFile);
  if (label) label.classList.toggle("hidden", loading);
  if (spinner) spinner.classList.toggle("hidden", !loading);
}

function verdictClass(verdict) {
  const v = (verdict || "").toLowerCase();
  if (v.includes("fake")) return "fake";
  if (v.includes("real")) return "real";
  return "unverified";
}

function fillList(id, items) {
  const ul = document.getElementById(id);
  ul.innerHTML = "";
  const list = items && items.length ? items : ["None identified"];
  list.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });
}

function passScore(pass) {
  if (!pass || pass.score == null) return "—";
  return `Score: ${pass.score}/100`;
}

function renderResult(data, isImage) {
  hideError();
  const r = data.result;
  const score = r.score ?? r.confidence ?? "—";

  document.getElementById("score-value").textContent = score;
  const ring = document.getElementById("score-ring");
  ring.style.borderColor =
    score >= 70 ? "var(--real)" : score <= 40 ? "var(--fake)" : "var(--unverified)";

  const badge = document.getElementById("verdict-badge");
  badge.textContent = r.verdict || "Unverified";
  badge.className = `verdict-badge ${verdictClass(r.verdict)}`;

  document.getElementById("summary").textContent = r.summary || "—";

  const incidentLoc = document.getElementById("incident-loc");
  if (r.incident || r.location) {
    incidentLoc.textContent = [
      r.incident ? `Incident: ${r.incident}` : "",
      r.location ? `Location: ${r.location}` : "",
    ]
      .filter(Boolean)
      .join(" · ");
    incidentLoc.classList.remove("hidden");
  } else {
    incidentLoc.classList.add("hidden");
  }

  if (isImage) {
    imageMeta.classList.remove("hidden");
    document.getElementById("image-description").textContent =
      r.image_description || "—";
    document.getElementById("image-date").textContent =
      r.image_created_date || "Unknown";
    let dateNote = r.date_source ? `Source: ${r.date_source}` : "";
    if (r.exif_date) dateNote += (dateNote ? " · " : "") + `EXIF: ${r.exif_date}`;
    document.getElementById("date-source").textContent = dateNote;
  } else {
    imageMeta.classList.add("hidden");
  }

  document.getElementById("pixel-score").textContent = passScore(r.pixel_forensics);
  document.getElementById("claim-score").textContent = passScore(r.claim_reasoning);
  fillList("pixel-findings", r.pixel_forensics?.findings);
  fillList("claim-findings", r.claim_reasoning?.findings);
  document.getElementById("rationale").textContent =
    r.rationale || r.reasoning || "—";
  fillList("red-flags", r.red_flags);
  fillList("suggested-actions", r.suggested_actions);

  results.classList.remove("hidden");
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

btnScanText.addEventListener("click", async () => {
  const text = newsText.value.trim();
  if (!text) {
    showError("Paste a headline, article, or claim to scan.");
    return;
  }
  hideError();
  setLoading(btnScanText, true);
  try {
    const res = await fetch("/api/forensic/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    renderResult(data, false);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(btnScanText, false);
  }
});

function setPreview(file) {
  if (file.size > MAX_BYTES) {
    showError("Image must be under 10 MB.");
    selectedFile = null;
    btnScanImage.disabled = true;
    return;
  }
  selectedFile = file;
  btnScanImage.disabled = false;
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreview.src = e.target.result;
    imagePreview.classList.remove("hidden");
    dropzoneInner.classList.add("hidden");
  };
  reader.readAsDataURL(file);
}

dropzone.addEventListener("click", () => imageInput.click());
imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (file) setPreview(file);
});
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file && /^image\/(jpeg|png|webp)$/i.test(file.type)) {
    imageInput.files = e.dataTransfer.files;
    setPreview(file);
  } else {
    showError("Only JPEG, PNG or WEBP images are supported.");
  }
});

btnScanImage.addEventListener("click", async () => {
  if (!selectedFile) {
    showError("Drop or select an image first.");
    return;
  }
  hideError();
  setLoading(btnScanImage, true);
  const form = new FormData();
  form.append("image", selectedFile);
  form.append("caption", imageCaption.value.trim());
  try {
    const res = await fetch("/api/forensic/image", {
      method: "POST",
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    renderResult(data, true);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(btnScanImage, false);
  }
});
