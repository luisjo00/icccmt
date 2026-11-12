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
