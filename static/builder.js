(() => {
  const state = { data: null, template: "classic", accent: "#2d6a4f", ink: "#1f2933", paper: "#ffffff" };
  const form = document.querySelector("#upload-form");
  const fileInput = document.querySelector("#resume-file");
  const fileLabel = document.querySelector("#file-label");
  const status = document.querySelector("#upload-status");
  const extractButton = document.querySelector("#extract-button");
  const preview = document.querySelector("#resume-preview");

  const text = (value) => typeof value === "string" ? value.trim() : "";
  const values = (items) => Array.isArray(items) ? items.filter(Boolean) : [];

  function element(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content) node.textContent = content;
    return node;
  }

  function addSection(parent, title) {
    const section = element("section");
    section.append(element("h2", "", title));
    parent.append(section);
    return section;
  }

  function renderEntries(parent, entries, kind) {
    values(entries).forEach((record) => {
      const entry = element("div", "entry");
      const title = kind === "education" ? text(record.degree) : text(record.role || record.title);
      const place = kind === "education" ? text(record.institution) : text(record.company || record.technologies);
      const dates = text(record.year || record.dates);
      if (title) entry.append(element("p", "entry-title", title));
      const meta = [place, dates].filter(Boolean).join("  |  ");
      if (meta) entry.append(element("p", "entry-meta", meta));
      const description = text(record.description);
      if (description) entry.append(element("p", kind === "projects" ? "project-description" : "", description));
      parent.append(entry);
    });
  }

  function renderResume() {
    preview.replaceChildren();
    preview.className = `resume template-${state.template}`;
    preview.style.setProperty("--accent", state.accent);
    preview.style.setProperty("--ink", state.ink);
    preview.style.setProperty("--paper", state.paper);
    const data = state.data;
    if (!data) {
      preview.innerHTML = '<div class="empty-preview"><span>✦</span><h2>Your resume preview will appear here.</h2><p>Upload a .txt file to begin.</p></div>';
      return;
    }

    const header = element("header", "resume-header");
    header.append(element("h1", "", text(data.name) || "Your Name"));
    if (text(data.headline)) header.append(element("p", "resume-headline", text(data.headline)));
    const contactItems = [data.contact?.email, data.contact?.phone, data.contact?.linkedin, data.contact?.github, data.contact?.website].map(text).filter(Boolean);
    if (contactItems.length) {
      const contact = element("div", "contact");
      contactItems.forEach((item) => contact.append(element("span", "", item)));
      header.append(contact);
    }
    preview.append(header);

    if (text(data.summary)) {
      const section = addSection(preview, "Profile");
      section.append(element("p", "summary", text(data.summary)));
    }
    if (values(data.skills).length) {
      const section = addSection(preview, "Skills");
      const skills = element("div", "skills");
      values(data.skills).forEach((skill) => skills.append(element("span", "skill", text(skill))));
      section.append(skills);
    }
    if (values(data.experience).length) {
      const section = addSection(preview, "Experience");
      renderEntries(section, data.experience, "experience");
    }
    if (values(data.projects).length) {
      const section = addSection(preview, "Projects");
      renderEntries(section, data.projects, "projects");
    }
    if (values(data.education).length) {
      const section = addSection(preview, "Education");
      renderEntries(section, data.education, "education");
    }
    if (values(data.achievements).length) {
      const section = addSection(preview, "Achievements");
      const list = element("ul", "list");
      values(data.achievements).forEach((achievement) => list.append(element("li", "", text(achievement))));
      section.append(list);
    }
    document.querySelector("#preview-name").textContent = text(data.name) || "Your resume";
  }

  function activateDesigner() {
    document.querySelectorAll(".disabled-until-data").forEach((panel) => panel.classList.remove("disabled-until-data"));
  }

  fileInput.addEventListener("change", () => {
    fileLabel.textContent = fileInput.files[0]?.name || "Choose a .txt file";
    status.textContent = "";
    status.className = "status";
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!fileInput.files[0]) return;
    extractButton.disabled = true;
    extractButton.textContent = "Extracting details…";
    status.className = "status";
    status.textContent = "Reading your resume and arranging its information…";
    try {
      const response = await fetch("/api/extract", { method: "POST", body: new FormData(form) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not extract the resume.");
      state.data = result.data;
      activateDesigner();
      renderResume();
      status.className = result.warning ? "status" : "status success";
      status.textContent = result.warning || "Details extracted. Choose a style and save your resume.";
    } catch (error) {
      status.className = "status error";
      status.textContent = error.message || "Something went wrong. Please try again.";
    } finally {
      extractButton.disabled = false;
      extractButton.textContent = "Extract resume details";
    }
  });

  document.querySelectorAll(".template-option").forEach((button) => button.addEventListener("click", () => {
    state.template = button.dataset.template;
    document.querySelectorAll(".template-option").forEach((option) => option.classList.toggle("selected", option === button));
    renderResume();
  }));
  [["#accent-colour", "accent"], ["#ink-colour", "ink"], ["#paper-colour", "paper"]].forEach(([selector, key]) => {
    document.querySelector(selector).addEventListener("input", (event) => { state[key] = event.target.value; renderResume(); });
  });

  function exportDocument(extension, mimeType) {
    if (!state.data) return;
    const style = document.querySelector('link[href*="builder.css"]');
    const styleUrl = style ? new URL(style.href, window.location.href).href : "";
    const documentHtml = `<!doctype html><html><head><meta charset="utf-8"><title>${text(state.data.name) || "Resume"}</title><link rel="stylesheet" href="${styleUrl}"></head><body><main class="workspace"><section class="preview-area"><div class="paper-wrap">${preview.outerHTML}</div></section></main></body></html>`;
    const blob = new Blob([documentHtml], { type: mimeType });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${(text(state.data.name) || "resume").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-resume.${extension}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
  document.querySelector("#pdf-button").addEventListener("click", () => { if (state.data) window.print(); });
  document.querySelector("#word-button").addEventListener("click", () => exportDocument("doc", "application/msword"));
  document.querySelector("#html-button").addEventListener("click", () => exportDocument("html", "text/html"));
  renderResume();
})();
