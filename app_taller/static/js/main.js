document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".chk-item .btn");
  if (!btn) return;

  // evita clicks repetidos durante envío
  if (btn.dataset.busy === "1") return;
  btn.dataset.busy = "1";

  const form = btn.closest("form.chk-item");
  const estado = btn.getAttribute("data-estado");
  form.querySelector('input[name="estado"]').value = estado;

  // quita color a todos antes de aplicar el nuevo
  form.querySelectorAll(".btn").forEach(b => {
    b.classList.remove("btn-success", "btn-warning", "btn-muted", "is-selected");
  });

  try {
    const resp = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (!resp.ok) throw new Error("Error");
    const data = await resp.json();

    // actualiza barra de progreso
    const bar = document.querySelector(".progress .progress-bar");
    if (bar) bar.style.width = data.pct + "%";
    const h3 = form.closest("section").querySelector("h3");
    if (h3) h3.innerHTML = `Checklist (avance ${data.ok}/${data.total} – ${data.pct}%)`;

    // marca el botón actual
    if (estado === "OK") btn.classList.add("btn-success");
    else if (estado === "PENDIENTE") btn.classList.add("btn-warning");
    else btn.classList.add("btn-muted");
    btn.classList.add("is-selected");

  } catch (err) {
    alert("No se pudo actualizar el ítem.");
  } finally {
    btn.dataset.busy = "0";
  }
});
// Feedback de envío en formularios con botones .btn-primary
document.addEventListener("submit", (e)=>{
  const form = e.target;
  const btn = form.querySelector("button[type=submit].btn, .btn-primary");
  if(!btn) return;
  const original = btn.innerHTML;
  btn.dataset.original = original;
  btn.disabled = true;
  btn.innerHTML = "Guardando…";
  setTimeout(()=>{ // fallback por si no hay redirección
    btn.disabled = false;
    btn.innerHTML = btn.dataset.original || original;
  }, 5000);
});



// Tabs
document.addEventListener("click", (e)=>{
  const btn=e.target.closest(".tab-btn"); if(!btn) return;
  const wrap=btn.closest(".tabs"); if(!wrap) return;
  wrap.querySelectorAll(".tab-btn").forEach(b=>b.setAttribute("aria-selected","false"));
  btn.setAttribute("aria-selected","true");
  const id=btn.dataset.tab;
  wrap.querySelectorAll(".tab-panel").forEach(p=>p.classList.remove("is-active"));
  wrap.querySelector(`#tab-${id}`)?.classList.add("is-active");
});

// Observaciones: autosave discreto (Enter+Ctrl o cada 3 s de pausa)
(function(){
  const form=document.getElementById("obs-form");
  const ta=document.getElementById("obs-text");
  const badge=document.getElementById("obs-status");
  if(!form||!ta) return;

  let t=null;
  const doSave=async ()=>{
    const fd=new FormData(form);
    const resp=await fetch(form.action,{method:"POST",body:fd,headers:{"X-Requested-With":"XMLHttpRequest"}});
    if(resp.ok){ badge.style.display="inline-block"; setTimeout(()=>badge.style.display="none",1200); }
  };
  ta.addEventListener("input",()=>{
    clearTimeout(t); t=setTimeout(doSave,3000);
  });
  form.addEventListener("submit",(e)=>{ e.preventDefault(); doSave(); });
})();




