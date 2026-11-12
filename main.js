/* Página de la Iglesia Cristiana Camino al Cielo (ICCCMT), Los Patios.
   Basada en la plantilla web-1200 v2 de Luis. Los datos de la iglesia viven solo en el bloque IGLESIA.
   Horas siempre en hora de Colombia (UTC−5, sin horario de verano), sin importar dónde esté quien visita. */
'use strict';

/* ===== DATOS DE LA IGLESIA (edita aquí) ===== */
// Coordenadas de la ficha "Iglesia Cristiana Camino al Cielo" en Google Maps (Calle 32 # 2-35, La Cordialidad).
const COORD = '7.8390849,-72.5015306';
const IGLESIA = {
  whatsapp: '573226825028',
  mensajes: {
    general: 'Hola, vi la página de la iglesia y quiero más información.',
    visita: 'Hola, quiero visitar la iglesia. ¿Me ayudan a llegar?',
    oracion: 'Hola, quiero pedir oración por ',
    pastores: 'Hola, quiero hablar con los pastores.',
    comprobante: 'Hola. Envié mi (diezmo / ofrenda) a la llave de la iglesia. Adjunto el comprobante.',
  },
  mapa: 'https://www.google.com/maps/dir/?api=1&destination=' + COORD,
  mapaEmbed: 'https://maps.google.com/maps?q=' + encodeURIComponent('Iglesia Cristiana Camino al Cielo, Los Patios, Norte de Santander') + '&ll=' + COORD + '&z=17&output=embed',
  envivo: 'https://www.youtube.com/@ICCCMT714/live',
  llave: '3188338874', // llave Bre-B de ofrendas y diezmos (celular); en pantalla va con espacios, se copia sin ellos
  // dia: 0 = domingo … 6 = sábado. Mismo orden en que se muestran.
  cultos: [
    { dia: 0, h: 9, m: 30, nombre: 'Culto dominical' },
    { dia: 0, h: 17, m: 0, nombre: 'Culto dominical de la tarde' },
    { dia: 2, h: 19, m: 0, nombre: 'Culto de enseñanza' },
    { dia: 4, h: 19, m: 0, nombre: 'Culto de oración' },
    { dia: 6, h: 19, m: 0, nombre: 'Culto de jóvenes' },
  ],
  duracionMin: 120,
  // Película de la portada (mp4 de scripts/pelicula.sh). Mientras sea null, la imagen se acerca con el scroll.
  pelicula: null, // { escritorio: 'img/film/camino-desktop.mp4', movil: 'img/film/camino-mobile.mp4' }
};

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
document.documentElement.classList.remove('no-js');
if (reduced) document.documentElement.classList.add('motion-off');

/* ---- enlaces de WhatsApp, mapa y en vivo ---- */
const externo = (a, url) => { a.href = url; a.target = '_blank'; a.rel = 'noopener'; };
const waUrl = (tipo) => `https://wa.me/${IGLESIA.whatsapp}?text=${encodeURIComponent(IGLESIA.mensajes[tipo] || IGLESIA.mensajes.general)}`;
document.querySelectorAll('[data-wa]').forEach(a => externo(a, waUrl(a.dataset.wa)));
document.querySelectorAll('[data-map]').forEach(a => externo(a, IGLESIA.mapa));
document.querySelectorAll('[data-live]').forEach(a => externo(a, IGLESIA.envivo));
const mapa = document.getElementById('mapa');
if (mapa) mapa.src = IGLESIA.mapaEmbed;

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

  // primer culto que aún no ha terminado, buscando desde hoy
  let prox = null;
  for (let k = 0; k < 8 && !prox; k++) {
    const d = (hoy + k) % 7;
    const delDia = IGLESIA.cultos.filter(c => c.dia === d).sort((a, b) => (a.h * 60 + a.m) - (b.h * 60 + b.m));
    for (const c of delDia) {
      const ini = c.h * 60 + c.m;
      if (k > 0 || ahora < ini + IGLESIA.duracionMin) { prox = { c, k, enCurso: k === 0 && ahora >= ini }; break; }
    }
  }

  const cuando = (p) => p.k === 0 ? 'hoy' : p.k === 1 ? 'mañana' : dias[p.c.dia].toLowerCase();
  const corto = prox && (prox.enCurso ? `Ahora: ${prox.c.nombre.toLowerCase()}, en vivo` : `Próximo culto: ${cuando(prox)}, ${hora(prox.c)}`);
  const largo = prox && (prox.enCurso ? `Estamos en culto ahora · ${prox.c.nombre}` : `Próximo culto: ${cuando(prox)} a las ${hora(prox.c)} · ${prox.c.nombre}`);
  if (prox) {
    document.querySelectorAll('[data-proximo]').forEach(el => { el.textContent = corto; });
    document.querySelectorAll('[data-proximo-largo]').forEach(el => { el.textContent = largo; });
    const estado = document.getElementById('estado'); if (estado) estado.classList.toggle('on', prox.enCurso);
    const enVivo = document.getElementById('en-vivo'); if (enVivo) enVivo.hidden = !prox.enCurso;
  }

  // se arma con nodos de texto (sin innerHTML): nada de lo que se escribe aquí se interpreta como HTML
  const box = document.getElementById('horario'); if (!box) return;
  const nodo = (tag, cls, txt) => { const n = document.createElement(tag); if (cls) n.className = cls; if (txt) n.textContent = txt; return n; };
  box.textContent = '';
  IGLESIA.cultos.forEach(c => {
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

/* ---- copiar la llave Bre-B ---- */
(function copiar() {
  const btn = document.getElementById('copiar'), code = document.getElementById('llave');
  if (!btn || !code) return;
  btn.addEventListener('click', async () => {
    let ok = false;
    try { await navigator.clipboard.writeText(IGLESIA.llave); ok = true; } catch (e) {
      const r = document.createRange(); r.selectNodeContents(code); const s = getSelection(); s.removeAllRanges(); s.addRange(r);
      try { ok = document.execCommand('copy'); } catch (e2) { ok = false; }
    }
    btn.textContent = ok ? 'Llave copiada' : 'Mantén presionada la llave para copiarla';
    setTimeout(() => { btn.textContent = 'Copiar llave'; }, 2500);
  });
})();

/* ---- compartir la web: menú del celular si existe, si no WhatsApp ---- */
(function compartir() {
  const btn = document.getElementById('compartir'); if (!btn) return;
  const url = 'https://caminoalcielo714.org';
  const texto = 'Mira la página de la Iglesia Cristiana Camino al Cielo: horarios de los cultos, cómo llegar y las prédicas.';
  btn.addEventListener('click', async () => {
    if (navigator.share) { try { await navigator.share({ title: 'Iglesia Cristiana Camino al Cielo', text: texto, url }); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
    window.open(`https://wa.me/?text=${encodeURIComponent(texto + ' ' + url)}`, '_blank', 'noopener');
  });
})();

/* ---- entradas de sección (solo transform, sin ocultar contenido) ---- */
if (!reduced && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => { entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
}

/* ---- portada que avanza con el scroll: película si hay, si no la imagen se acerca ---- */
(function portada() {
  const film = document.querySelector('.film'), stage = document.querySelector('.film-stage'), video = document.getElementById('film-video');
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

  const conPelicula = !!(IGLESIA.pelicula && video);
  if (!conPelicula) film.classList.add('still');

  let duration = 0, ready = false, seeking = false, pending = null;
  const seekTo = (t) => { if (Math.abs(video.currentTime - t) < .02) return; seeking = true; video.currentTime = t; };
  const update = () => {
    const p = progress();
    setChapter(p);
    if (!conPelicula) { stage.style.setProperty('--p', p.toFixed(4)); return; }
    if (!ready) return;
    const t = p * Math.max(0, duration - .06);
    if (seeking) pending = t; else seekTo(t);
  };
  let ticking = false;
  window.addEventListener('scroll', () => { if (ticking) return; ticking = true; requestAnimationFrame(() => { ticking = false; update(); }); }, { passive: true });
  window.addEventListener('resize', update);
  update();
  if (!conPelicula) return;

  video.addEventListener('loadedmetadata', () => { duration = video.duration || 0; ready = duration > 0; update(); });
  video.addEventListener('seeked', () => { seeking = false; if (pending !== null) { const t = pending; pending = null; seekTo(t); } });
  const mobile = window.matchMedia('(max-width: 760px)').matches;
  const src = mobile ? IGLESIA.pelicula.movil : IGLESIA.pelicula.escritorio;
  // descarga completa en memoria para que el scroll busque cualquier fotograma al instante
  fetch(src).then(r => r.ok ? r.blob() : Promise.reject(r.status)).then(b => { video.src = URL.createObjectURL(b); video.load(); }).catch(() => { /* queda la imagen */ });
  // iOS: el primer toque habilita la búsqueda de fotogramas
  const prime = () => { video.play().then(() => video.pause()).catch(() => {}); window.removeEventListener('touchstart', prime); };
  window.addEventListener('touchstart', prime, { passive: true });
})();
