// --- util: refrescar cronómetro si tuvieras una función global ---
window.setInicioEstado = function (iso) {
  const el = document.getElementById("cronometro");
  if (el) {
    el.dataset.inicio = iso;
    // si ya tienes un timer que lee el dataset, no hace falta nada más
  }
};

// --- Acciones rápidas ---
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".quick-action");
  if (!btn) return;

  const wrap = btn.closest(".quick-actions");
  const accion = btn.dataset.accion;
  const urlTpl = wrap.dataset.url; // contiene __ACCION__ como placeholder
  const url = urlTpl.replace("__ACCION__", accion);

  const fd = new FormData();
  fd.append("csrfmiddlewaretoken", getCsrf());
  if (accion === "PAUSAR") {
    const motivo = document.getElementById("motivo-pausa")?.value || "";
    fd.append("motivo", motivo);
  }

  // feedback visual
  btn.disabled = true;
  try {
    const r = await fetch(url, { method: "POST", body: fd, headers: { "X-Requested-With": "XMLHttpRequest" } });
    const data = await r.json();
    if (!r.ok || !data.ok) throw new Error(data.msg || "Error");

    // Actualiza estado y cronómetro
    const est = document.getElementById("estado-ot");
    if (est && data.estado) est.textContent = data.estado;
    if (data.inicio_estado_iso) window.setInicioEstado(data.inicio_estado_iso);

    toast(data.msg || "Ok"); // si ya tienes una función toast; si no, usa alert
  } catch (err) {
    alert(err.message || "No se pudo completar la acción.");
  } finally {
    btn.disabled = false;
  }
});

// --- Observaciones ---
const obsForm = document.getElementById("obs-form");
if (obsForm) {
  obsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(obsForm);
    try {
      const r = await fetch(obsForm.action, { method: "POST", body: fd, headers: { "X-Requested-With": "XMLHttpRequest" } });
      const data = await r.json();
      if (!r.ok || !data.ok) throw new Error(data.msg || "Error");
      toast("Observaciones guardadas"); // o alert
    } catch (err) {
      alert(err.message || "No se pudo guardar");
    }
  });
}

// --- helper CSRF (si no lo tienes ya) ---
function getCsrf() {
  const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (el) return el.value;
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : "";
}


