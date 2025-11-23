document.addEventListener("click", async (e) => {
  const btn = e.target.closest("form.chk-item .btn");
  if (!btn) return;

  const form = btn.closest("form.chk-item");
  const estado = btn.getAttribute("data-estado");
  const submitBtnList = form.querySelectorAll(".btn");
  const hidden = form.querySelector('input[name="estado"]');
  hidden.value = estado;

  // Lock UI
  submitBtnList.forEach(b => b.disabled = true);
  btn.classList.add("is-loading");

  try {
    const resp = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: {"X-Requested-With": "XMLHttpRequest"}
    });
    if (!resp.ok) throw new Error("Error");
    const data = await resp.json();

    // Progress
    const bar = document.querySelector(".progress .progress-bar");
    if (bar) bar.style.width = data.pct + "%";
    const h3 = form.closest("section").querySelector("h3");
    if (h3) h3.innerHTML = `Checklist (avance ${data.ok}/${data.total} – ${data.pct}%)`;

    // Visual active state
    const area = form.querySelector(".chk-actions");
    area.querySelectorAll(".btn")
        .forEach(b => { b.classList.remove("btn-success","btn-warning","btn-muted","is-active"); b.setAttribute("aria-pressed","false"); });

    if (estado === "OK") btn.classList.add("btn-success");
    else if (estado === "PENDIENTE") btn.classList.add("btn-warning");
    else btn.classList.add("btn-muted");

    btn.classList.add("is-active");
    btn.setAttribute("aria-pressed","true");

    // Toast
    window?.showToast && showToast("Ítem actualizado", "success");
  } catch (err) {
    window?.showToast && showToast("No se pudo actualizar el ítem", "error");
    alert("No se pudo actualizar el ítem.");
  } finally {
    submitBtnList.forEach(b => b.disabled = false);
    btn.classList.remove("is-loading");
  }
});
