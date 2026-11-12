/* Páginas de las iglesias hijas (/<barrio>/), generadas por _sedes/hacer_sedes.py.
   Los datos de cada iglesia vienen del bloque <script type="application/json" id="sede-datos"> de su página.
   Horas siempre en hora de Colombia (UTC−5, sin horario de verano). */
'use strict';

const SEDE = JSON.parse(document.getElementById('sede-datos').textContent);
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
document.documentElement.classList.remove('no-js');
if (reduced) document.documentElement.classList.add('motion-off');

/* ---- enlaces de WhatsApp y mapa ---- */
const externo = (a, url) => { a.href = url; a.target = '_blank'; a.rel = 'noopener'; };
const waUrl = (tipo) => `https://wa.me/${SEDE.whatsapp}?text=${encodeURIComponent(SEDE.mensajes[tipo] || SEDE.mensajes.general)}`;
document.querySelectorAll('[data-wa]').forEach(a => externo(a, waUrl(a.dataset.wa)));
document.querySelectorAll('[data-map]').forEach(a => externo(a, SEDE.mapa));
const mapa = document.getElementById('mapa');
if (mapa) mapa.src = `https://maps.google.com/maps?q=${SEDE.coord}&z=17&output=embed`;

/* ---- navegación ---- */
const nav = document.getElementById('nav');
const onScrollNav = () => nav.classList.toggle('solid', window.scrollY > 40);
onScrollNav(); window.addEventListener('scroll', onScrollNav, { passive: true });
const burger = document.getElementById('burger'), menu = document.getElementById('menu');
const cerrarMenu = () => { menu.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; };
burger.addEventListener('click', () => { const open = menu.classList.toggle('open'); burger.setAttribute('aria-expanded', open); document.body.style.overflow = open ? 'hidden' : ''; });
menu.querySelectorAll('a').forEach(a => a.addEventListener('click', cerrarMenu));
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && menu.classList.contains('open')) cerrarMenu(); });

/* ---- horario: hoy, próximo culto y "en culto ahora" (hora de Colombia) ---- */
(function horario() {
  const dias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
  const hora = (c) => `${c.h % 12 || 12}:${String(c.m).padStart(2, '0')} ${c.h < 12 ? 'a. m.' : 'p. m.'}`;
  const bogota = new Date(Date.now() - 5 * 3600e3);
  const hoy = bogota.getUTCDay(), ahora = bogota.getUTCHours() * 60 + bogota.getUTCMinutes();

  let prox = null;
  for (let k = 0; k < 8 && !prox; k++) {
    const d = (hoy + k) % 7;
    const delDia = SEDE.cultos.filter(c => c.dia === d).sort((a, b) => (a.h * 60 + a.m) - (b.h * 60 + b.m));
    for (const c of delDia) {
      const ini = c.h * 60 + c.m;
      if (k > 0 || ahora < ini + SEDE.duracionMin) { prox = { c, k, enCurso: k === 0 && ahora >= ini }; break; }
    }
  }

  const cuando = (p) => p.k === 0 ? 'hoy' : p.k === 1 ? 'mañana' : dias[p.c.dia].toLowerCase();
  if (prox) {
    const corto = prox.enCurso ? `Ahora: ${prox.c.nombre.toLowerCase()}` : `Próximo culto: ${cuando(prox)}, ${hora(prox.c)}`;
    const largo = prox.enCurso ? `Estamos en culto ahora · ${prox.c.nombre}` : `Próximo culto: ${cuando(prox)} a las ${hora(prox.c)} · ${prox.c.nombre}`;
    document.querySelectorAll('[data-proximo]').forEach(el => { el.textContent = corto; });
    document.querySelectorAll('[data-proximo-largo]').forEach(el => { el.textContent = largo; });
    const estado = document.getElementById('estado'); if (estado) estado.classList.toggle('on', prox.enCurso);
  }

  // se arma con nodos de texto (sin innerHTML)
  const box = document.getElementById('horario'); if (!box) return;
  const nodo = (tag, cls, txt) => { const n = document.createElement(tag); if (cls) n.className = cls; if (txt) n.textContent = txt; return n; };
  box.textContent = '';
  SEDE.cultos.forEach(c => {
    const esHoy = c.dia === hoy, esProx = prox && prox.c === c;
    const marca = esProx ? (prox.enCurso ? 'ahora' : 'próximo') : esHoy ? 'hoy' : '';
    const fila = nodo('div', `fila${esHoy ? ' hoy' : ''}${esProx ? ' prox' : ''}`);
    fila.setAttribute('role', 'listitem');
    const dia = nodo('span', 'dia', `${dias[c.dia]} `);
    if (marca) dia.appendChild(nodo('em', '', marca));
    fila.append(dia, nodo('span', 'nombre', c.nombre), nodo('span', 'hora', hora(c)));
    box.appendChild(fila);
  });
})();

/* ---- entradas de sección (solo transform, sin ocultar contenido) ---- */
if (!reduced && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => { entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
}

/* ---- copiar la llave Bre-B ---- */
(function copiar() {
  const btn = document.getElementById('copiar'), code = document.getElementById('llave');
  if (!btn || !code) return;
  btn.addEventListener('click', async () => {
    let ok = false;
    try { await navigator.clipboard.writeText(SEDE.llave); ok = true; } catch (e) {
      const r = document.createRange(); r.selectNodeContents(code); const s = getSelection(); s.removeAllRanges(); s.addRange(r);
      try { ok = document.execCommand('copy'); } catch (e2) { ok = false; }
    }
    btn.textContent = ok ? 'Llave copiada' : 'Mantén presionada la llave para copiarla';
    setTimeout(() => { btn.textContent = 'Copiar llave'; }, 2500);
  });
})();

/* ---- compartir la página: menú del celular si existe, si no WhatsApp ---- */
(function compartir() {
  const btn = document.getElementById('compartir'); if (!btn) return;
  btn.addEventListener('click', async () => {
    if (navigator.share) { try { await navigator.share({ title: SEDE.nombre, text: SEDE.compartir, url: SEDE.url }); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
    window.open(`https://wa.me/?text=${encodeURIComponent(SEDE.compartir + ' ' + SEDE.url)}`, '_blank', 'noopener');
  });
})();

/* ---- portada que avanza con el scroll: la imagen se acerca (igual que la principal) ---- */
(function portada() {
  const film = document.querySelector('.film'), stage = document.querySelector('.film-stage');
  const chapters = Array.from(document.querySelectorAll('.chapter'));
  const index = Array.from(document.querySelectorAll('.film-index button'));
  if (!film || !stage) return;

  const progress = () => { const total = film.offsetHeight - window.innerHeight; if (total <= 0) return 0; const p = -film.getBoundingClientRect().top / total; return Math.min(1, Math.max(0, p)); };
  const setChapter = (p) => {
    const i = Math.min(chapters.length - 1, Math.floor(p * chapters.length));
    chapters.forEach((c, k) => c.classList.toggle('on', k === i));
    index.forEach((b, k) => b.classList.toggle('on', k === i));
  };
  index.forEach(b => b.addEventListener('click', () => {
    const k = +b.dataset.go; const total = film.offsetHeight - window.innerHeight;
    window.scrollTo({ top: film.offsetTop + total * ((k + .5) / chapters.length), behavior: reduced ? 'auto' : 'smooth' });
  }));
  if (reduced) { chapters.forEach(c => c.classList.add('on')); return; }

  film.classList.add('still');
  const update = () => { const p = progress(); setChapter(p); stage.style.setProperty('--p', p.toFixed(4)); };
  let ticking = false;
  window.addEventListener('scroll', () => { if (ticking) return; ticking = true; requestAnimationFrame(() => { ticking = false; update(); }); }, { passive: true });
  window.addEventListener('resize', update);
  update();
})();
