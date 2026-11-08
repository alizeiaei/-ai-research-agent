const form = document.querySelector("#research-form");
const button = document.querySelector("#submit-button");
const message = document.querySelector("#message");
const results = document.querySelector("#results");
const evidenceList = document.querySelector("#evidence-list");
const insightSections = document.querySelector("#insight-sections");
const downloadButton = document.querySelector("#download-button");
let currentMarkdown = "";

function setMessage(text, kind = "info") {
  message.textContent = text;
  message.className = `message ${kind}`;
  message.hidden = !text;
}

function evidenceCard(item, index) {
  const article = document.createElement("article");
  article.className = "evidence-card";

  const number = document.createElement("span");
  number.className = "evidence-number";
  number.textContent = String(index + 1).padStart(2, "0");

  const title = document.createElement("h3");
  title.textContent = item.title;

  const excerpt = document.createElement("p");
  excerpt.textContent = item.excerpt || "خلاصه‌ای ارائه نشده است.";

  const footer = document.createElement("div");
  footer.className = "card-footer";
  const score = document.createElement("span");
  score.textContent = `ارتباط: ${Math.round(item.score * 100)}٪`;
  const link = document.createElement("a");
  link.href = item.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "مشاهده منبع ↗";
  footer.append(score, link);

  article.append(number, title, excerpt, footer);
  return article;
}

function insightSection(title, items) {
  const section = document.createElement("section");
  section.className = "insight-panel";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const list = document.createElement("ul");

  if (!items.length) {
    const empty = document.createElement("li");
    empty.textContent = "مورد مستندی در منابع بازیابی‌شده پیدا نشد.";
    list.append(empty);
  }
  for (const item of items) {
    const row = document.createElement("li");
    const text = document.createElement("span");
    text.textContent = item.text;
    row.append(text);
    if (item.source_url) {
      const source = document.createElement("a");
      source.href = item.source_url;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      source.textContent = item.source_title;
      row.append(source);
    }
    list.append(row);
  }
  section.append(heading, list);
  return section;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.querySelector("span").textContent = "در حال تحقیق…";
  results.hidden = true;
  setMessage("در حال دریافت و ارزیابی منابع…");

  const payload = {
    query: form.query.value.trim(),
    provider: form.provider.value,
    language: form.language.value,
    count: Number(form.count.value),
  };

  try {
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "تحقیق ناموفق بود.");

    currentMarkdown = data.markdown;
    document.querySelector("#result-title").textContent = data.query;
    document.querySelector("#result-meta").textContent = `${data.evidence.length} منبع مرتبط پیدا شد`;
    document.querySelector("#direct-answer").textContent = data.answer;
    insightSections.replaceChildren(
      insightSection("نکات کلیدی", data.key_findings),
      insightSection("کاربردهای عملی", data.practical_applications),
      insightSection("ریسک‌ها و محدودیت‌ها", data.limitations),
    );
    evidenceList.replaceChildren(...data.evidence.map(evidenceCard));
    results.hidden = false;
    setMessage("");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "شروع تحقیق";
  }
});

downloadButton.addEventListener("click", () => {
  const blob = new Blob([currentMarkdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "research-report.md";
  link.click();
  URL.revokeObjectURL(url);
});
