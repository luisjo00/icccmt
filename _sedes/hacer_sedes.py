"""Genera las páginas de las iglesias hijas de Camino al Cielo.

Lee _sedes/sedes.json y escribe:
  - /<slug>/index.html de cada iglesia (desde _sedes/plantilla.html)
  - la lista «Nuestras iglesias» de index.html (entre <!-- iglesias:inicio --> y <!-- iglesias:fin -->)

Uso (desde cualquier carpeta):  python _sedes/hacer_sedes.py
No toca nada más del sitio. Después: revisar en la vista previa, commit y push (con el OK de Luis).
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
SEDES = RAIZ / '_sedes'
DOMINIO = 'https://caminoalcielo714.org'
DURACION_MIN = 120  # duración de cada culto (para "en culto ahora" y el horario de Google)

DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
DIAS_EN = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
CONTEO = {1: 'Un culto', 2: 'Dos cultos', 3: 'Tres cultos', 4: 'Cuatro cultos', 5: 'Cinco cultos',
          6: 'Seis cultos', 7: 'Siete cultos', 8: 'Ocho cultos'}

e = html.escape  # escapa & < > " '


def hora(c):
    return f"{c['h'] % 12 or 12}:{c['m']:02d} {'a. m.' if c['h'] < 12 else 'p. m.'}"


def y_lista(cosas):
    cosas = list(cosas)
    return cosas[0] if len(cosas) == 1 else ', '.join(cosas[:-1]) + ' y ' + cosas[-1]


def resumen(cultos, sep=' · '):
    """'Domingo 9:30 a. m. · martes, jueves y viernes 7:00 p. m.' (días agrupados por hora, en orden)."""
    grupos = {}
    for c in cultos:
        grupos.setdefault(hora(c), [])
        if DIAS[c['dia']] not in grupos[hora(c)]:
            grupos[hora(c)].append(DIAS[c['dia']])
    partes = [f'{y_lista(dias)} {h}' for h, dias in grupos.items()]
    texto = sep.join(partes)
    return texto[0].upper() + texto[1:]


def whatsapp_pantalla(num):
    local = num[2:] if num.startswith('57') and len(num) == 12 else num
    return f'{local[:3]} {local[3:6]} {local[6:]}' if len(local) == 10 else local


def wa(num, texto):
    return f'https://wa.me/{num}?text={quote(texto)}'


def json_en_script(obj):
    # dentro de <script> no puede aparecer "</": se escapa para que el bloque no se corte
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def pagina(s, plantilla):
    url = f"{DOMINIO}/{s['slug']}/"
    barrio, ciudad = s['barrio'], s['ciudad']
    cultos = s['cultos']
    pastores = s.get('pastores', [])
    pastores_frase = y_lista(f"{'el' if p['titulo'] == 'pastor' else 'la'} {p['titulo']} {p['nombre']}" for p in pastores)
    pastores_frase = pastores_frase[0].upper() + pastores_frase[1:] if pastores_frase else 'Los pastores'
    pastores_corto = 'Pastores ' + y_lista(p['nombre'] for p in pastores) if pastores else ''
    mensajes = {
        'general': f'Hola, vi la página de la iglesia Camino al Cielo del barrio {barrio} y quiero más información.',
        'visita': f'Hola, quiero visitar la iglesia Camino al Cielo del barrio {barrio}. ¿Me ayudan a llegar?',
        'oracion': 'Hola, quiero pedir oración por ',
        'pastores': 'Hola, quiero hablar con los pastores.',
        'comprobante': 'Hola, pastor. Envié mi (diezmo / ofrenda / primicia) a la llave de la iglesia. Adjunto el comprobante.',
    }
    lat, lon = (x.strip() for x in s['coord'].split(','))
    mapa = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

    filas = []
    for c in cultos:
        filas.append(f'          <div class="fila" role="listitem"><span class="dia">{e(DIAS[c["dia"]].capitalize())}</span>'
                     f'<span class="nombre">{e(c["nombre"])}</span><span class="hora">{e(hora(c))}</span></div>')

    def cierre(c):
        t = c['h'] * 60 + c['m'] + DURACION_MIN
        return f'{t // 60 % 24:02d}:{t % 60:02d}'

    jsonld = {
        '@context': 'https://schema.org',
        '@type': 'Church',
        '@id': f'{url}#iglesia',
        'name': f'Iglesia Cristiana Camino al Cielo · Barrio {barrio}',
        'url': url,
        'logo': f'{DOMINIO}/img/sello.svg',
        'telephone': '+' + s['whatsapp'],
        'address': {'@type': 'PostalAddress', 'streetAddress': f"{s['direccion']}, barrio {barrio}",
                    'addressLocality': ciudad, 'addressRegion': s['departamento'], 'addressCountry': 'CO'},
        'geo': {'@type': 'GeoCoordinates', 'latitude': float(lat), 'longitude': float(lon)},
        'openingHoursSpecification': [
            {'@type': 'OpeningHoursSpecification', 'dayOfWeek': DIAS_EN[c['dia']],
             'opens': f"{c['h']:02d}:{c['m']:02d}", 'closes': cierre(c)} for c in cultos],
        'parentOrganization': {'@id': f'{DOMINIO}/#iglesia'},
    }
    if pastores:
        jsonld['employee'] = [{'@type': 'Person', 'name': p['nombre'], 'jobTitle': p['titulo'].capitalize()} for p in pastores]
    redes = s.get('redes', [])
    if redes:
        jsonld['sameAs'] = [r['url'] for r in redes]
    if s.get('foto_pastores'):
        jsonld['image'] = url + s['foto_pastores']

    datos = {'whatsapp': s['whatsapp'], 'mensajes': mensajes, 'coord': f'{lat},{lon}', 'mapa': mapa,
             'cultos': cultos, 'duracionMin': DURACION_MIN, 'url': url, 'llave': s.get('llave', '').replace(' ', ''),
             'nombre': f'Iglesia Cristiana Camino al Cielo · Barrio {barrio}',
             'compartir': f'Mira la página de la Iglesia Cristiana Camino al Cielo del barrio {barrio}: horarios de los cultos y cómo llegar.'}

    def enlace(r, dentro):
        return f'<a href="{e(r["url"])}" target="_blank" rel="noopener">{dentro}</a>'

    redes_lista = ''
    if redes:
        items = [f'        <li>' + enlace(r, f'<b>{e(r["red"])}</b><code>{e(r["usuario"])}</code><span>{e(r["nota"])}</span>') + '</li>'
                 for r in redes]
        redes_lista = '<ul class="redes reveal">\n' + '\n'.join(items) + '\n      </ul>'
    redes_dato = ('<dt>Redes</dt><dd>' + ' · '.join(enlace(r, e(r['red'])) for r in redes) + '</dd>') if redes else ''
    def archivo(clave):
        nombre = s.get(clave)
        if nombre and not (RAIZ / s['slug'] / nombre).exists():
            sys.exit(f"Falta /{s['slug']}/{nombre} ({clave})")
        return nombre

    def figura(nombre, alt, titulo, nota):
        return (f'<figure class="reveal"><img src="{e(nombre)}" alt="{e(alt)}" width="800" height="1000" loading="lazy">'
                f'<figcaption><b>{e(titulo)}</b><span>{e(nota)}</span></figcaption></figure>')

    figuras = []
    if archivo('foto_pastores'):
        figuras.append(figura(s['foto_pastores'], pastores_frase, pastores_corto, f'Iglesia del barrio {barrio}'))
    if archivo('foto_familia'):
        figuras.append(figura(s['foto_familia'], 'Los pastores con sus hijos', 'La familia pastoral', 'Los pastores con sus hijos'))
    pastores_fotos = ('<div class="pastores">\n        ' + '\n        '.join(figuras) + '\n      </div>') if figuras else ''

    templo = archivo('foto_templo')
    fachada = ''
    if archivo('foto_fachada'):
        texto = s.get('fachada_texto', 'Así se ve la entrada de la iglesia.')
        fachada = (f'<figure class="fachada"><img src="{e(s["foto_fachada"])}" alt="Fachada de la iglesia del barrio {e(barrio)}" loading="lazy">'
                   f'<figcaption>{e(texto)}</figcaption></figure>')

    llave = s.get('llave', '')
    if llave and not llave.replace(' ', '').isalnum() and not llave.startswith('@'):
        sys.exit(f"Llave Bre-B rara en {s['slug']}: {llave!r}")
    solo = llave.replace(' ', '')
    llave_pantalla = f'{solo[:3]} {solo[3:6]} {solo[6:]}' if solo.isdigit() and len(solo) == 10 else llave
    tipo = ' (celular)' if solo.isdigit() and len(solo) == 10 else ''
    ofrenda = (f'''<div class="reveal ofrenda">
        <h3>Ofrendas, diezmos y primicias</h3>
        <p>Desde la app de tu banco o de Nequi, envía a la llave Bre-B{tipo} de la iglesia:</p>
        <div class="llave"><code id="llave">{e(llave_pantalla)}</code><button type="button" class="btn btn-line" id="copiar">Copiar llave</button></div>
        <p class="nota">Si quieres, envíanos el comprobante por WhatsApp para que los pastores lo registren como diezmo, ofrenda o primicia.</p>
        <div class="actions"><a class="btn btn-wa" data-wa="comprobante" href="{e(wa(s['whatsapp'], mensajes['comprobante']))}">Enviar comprobante</a></div>
        <p class="nota">Gracias por tu generosidad. Dios bendiga tu siembra.</p>
      </div>''') if llave else ''
    mapa_nota = (f'<p class="nota">El punto del mapa es aproximado: la iglesia queda {e(s["referencia"])}. '
                 f'Si te pierdes, escríbenos por WhatsApp.</p>' if s.get('coord_aproximada') else '')

    descripcion = (f"Iglesia Cristiana Camino al Cielo en el barrio {barrio}, {ciudad}. "
                   f"{pastores_corto + '. ' if pastores_corto else ''}Cultos: {resumen(cultos, '; ').rstrip('.')}. {s['direccion']}.")
    valores = {
        'titulo': f'Camino al Cielo · Barrio {barrio}, {ciudad} | Cultos y horarios',
        'descripcion': descripcion,
        'url': url,
        'og_titulo': f'Iglesia Cristiana Camino al Cielo · Barrio {barrio}',
        'og_descripcion': f"Te esperamos: {resumen(cultos, '; ').rstrip('.')}. {s['direccion']}, barrio {barrio}, {ciudad}.",
        'barrio': barrio, 'ciudad': ciudad, 'departamento': s['departamento'], 'direccion': s['direccion'],
        'resumen': resumen(cultos),
        'resumen_punto': resumen(cultos, '; ').rstrip('.') + '.',
        'slug': s['slug'],
        'banda_foto': templo or '/img/hero.jpg',
        'banda_clase': '' if templo else ' band-sede',
        'ofrenda_clase': ' split' if llave else '',
        'redes_titulo': 'Síguenos en redes.' if redes else 'Comparte esta página.',
        'redes_lead': ('Aquí publicamos lo que pasa en la iglesia. Síguenos y comparte.' if redes
                       else 'Ayúdanos a que más vecinos conozcan la iglesia.'),
        'conteo': CONTEO.get(len(cultos), f'{len(cultos)} cultos'),
        'pastores_frase': pastores_frase,
        'whatsapp_pantalla': whatsapp_pantalla(s['whatsapp']),
        'mapa': mapa,
        'wa_general': wa(s['whatsapp'], mensajes['general']),
        'wa_visita': wa(s['whatsapp'], mensajes['visita']),
        'wa_oracion': wa(s['whatsapp'], mensajes['oracion']),
        'wa_pastores': wa(s['whatsapp'], mensajes['pastores']),
    }
    # todo lo de texto va escapado; los bloques ya armados (HTML/JSON) entran tal cual
    salida = plantilla
    for k, v in valores.items():
        salida = salida.replace('{{' + k + '}}', e(v))
    crudos = {
        'filas': '\n'.join(filas),
        'pastores_fotos': pastores_fotos,
        'fachada': fachada,
        'ofrenda': ofrenda,
        'redes_lista': redes_lista,
        'redes_dato': redes_dato,
        'mapa_nota': mapa_nota,
        'jsonld': json_en_script(jsonld),
        'datos': json_en_script(datos),
    }
    for k, v in crudos.items():
        salida = salida.replace('{{' + k + '}}', v)
    sobrantes = re.findall(r'\{\{\w+\}\}', salida)
    if sobrantes:
        sys.exit(f'Faltan valores en la plantilla: {sorted(set(sobrantes))}')
    return salida


def tarjeta(s):
    pastores = s.get('pastores', [])
    spans = f'<span class="nowrap">{e(s["direccion"])}</span>'
    if pastores:
        spans += f'<span>{e("Pastores " + y_lista(p["nombre"] for p in pastores))}</span>'
    spans += f'<span>{e(resumen(s["cultos"]))}</span>'
    return (f'        <li><a href="/{e(s["slug"])}/"><small>{e(s["ciudad"])}</small><b>Barrio {e(s["barrio"])}</b>'
            f'{spans}<em>Horarios y cómo llegar →</em></a></li>')


def main():
    datos = json.loads((SEDES / 'sedes.json').read_text(encoding='utf-8'))
    sedes = datos['sedes']
    plantilla = (SEDES / 'plantilla.html').read_text(encoding='utf-8')
    slugs = set()
    for s in sedes:
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', s['slug']) or s['slug'] in slugs or s['slug'] in {'img', '_sedes'}:
            sys.exit(f"Slug inválido o repetido: {s['slug']!r} (solo minúsculas, números y guiones)")
        if not re.fullmatch(r'57\d{10}', s['whatsapp']):
            sys.exit(f"WhatsApp de {s['slug']} debe ser 57 + 10 dígitos, sin espacios: {s['whatsapp']!r}")
        slugs.add(s['slug'])
        destino = RAIZ / s['slug'] / 'index.html'
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(pagina(s, plantilla), encoding='utf-8', newline='\n')
        if not (destino.parent / 'qr.png').exists():
            print(f'OJO /{s["slug"]}/qr.png no existe: python iglesia/marca/qr/hacer_qr_sede.py {s["slug"]}')
        print(f'ok  /{s["slug"]}/')

    indice = RAIZ / 'index.html'
    texto = indice.read_text(encoding='utf-8')
    patron = re.compile(r'(<!-- iglesias:inicio -->).*?(<!-- iglesias:fin -->)', re.S)
    if not patron.search(texto):
        sys.exit('index.html no tiene las marcas <!-- iglesias:inicio --> / <!-- iglesias:fin -->')
    lista = '\n'.join(tarjeta(s) for s in sedes)
    texto = patron.sub(lambda m: m.group(1) + '\n' + lista + '\n' + m.group(2), texto, count=1)
    indice.write_text(texto, encoding='utf-8', newline='\n')
    print(f'ok  index.html: {len(sedes)} iglesia(s) en "Nuestras iglesias"')

    # aviso de carpetas generadas antes que ya no están en la lista (no se borran solas)
    for d in RAIZ.iterdir():
        f = d / 'index.html'
        if d.is_dir() and d.name not in slugs and f.exists() and 'hacer_sedes.py' in f.read_text(encoding='utf-8')[:600]:
            print(f'OJO /{d.name}/ ya no está en sedes.json: bórrala si la iglesia salió de la lista')


if __name__ == '__main__':
    main()
