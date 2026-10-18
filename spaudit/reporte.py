"""Genera el informe en HTML (autocontenido), JSON y Markdown.

El HTML no carga nada externo: se abre con doble clic, funciona sin Internet y
se imprime o guarda en PDF desde el navegador.
"""

import datetime
import html
import io
import json
import os

from .controles_comunes import (
    CUMPLE, NO_CUMPLE, PARCIAL, NO_VERIFICADO, NO_APLICA, COLOR_ESTADO, RIESGOS,
)

ESTADO_ETIQUETA = {
    CUMPLE: "Cumple",
    PARCIAL: "Parcial",
    NO_CUMPLE: "No cumple",
    NO_VERIFICADO: "Sin verificar",
    NO_APLICA: "No aplica",
}

RIESGO_ETIQUETA = {
    "critico": "Crítico", "alto": "Alto", "medio": "Medio", "bajo": "Bajo",
}

ESTILO = """
:root{
  --fondo:#f6f7f9; --panel:#ffffff; --texto:#1f2328; --tenue:#656d76;
  --borde:#d8dee4; --acento:#1f4e79; --sombra:0 1px 3px rgba(0,0,0,.08);
}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:15px;line-height:1.55}
.envoltura{max-width:1180px;margin:0 auto;padding:28px 20px 80px}
header.cabecera{background:var(--acento);color:#fff;border-radius:10px;padding:26px 28px;
  margin-bottom:22px;box-shadow:var(--sombra)}
header.cabecera h1{margin:0 0 6px;font-size:24px;letter-spacing:-.2px}
header.cabecera p{margin:4px 0 0;opacity:.88;font-size:14px}
h2{font-size:19px;margin:34px 0 12px;padding-bottom:7px;border-bottom:2px solid var(--borde)}
h3{font-size:16px;margin:22px 0 8px}
p.ayuda{color:var(--tenue);font-size:13.5px;margin:6px 0 14px}
.panel{background:var(--panel);border:1px solid var(--borde);border-radius:10px;
  padding:18px 20px;box-shadow:var(--sombra);margin-bottom:16px}
.tarjetas{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:8px}
.tarjeta{background:var(--panel);border:1px solid var(--borde);border-left-width:5px;
  border-radius:8px;padding:13px 15px}
.tarjeta .n{display:block;font-size:27px;font-weight:650;line-height:1.15}
.tarjeta .t{display:block;font-size:12px;color:var(--tenue);text-transform:uppercase;
  letter-spacing:.5px;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);font-size:13.5px;
  border:1px solid var(--borde);border-radius:8px;overflow:hidden}
th{background:#eef1f4;text-align:left;padding:9px 11px;font-weight:600;font-size:12px;
  text-transform:uppercase;letter-spacing:.4px;color:#3d444d;border-bottom:1px solid var(--borde)}
td{padding:9px 11px;border-bottom:1px solid #eceff2;vertical-align:top}
tr:last-child td{border-bottom:none}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px}
code{background:#eef1f4;padding:1px 5px;border-radius:4px}
.etiqueta{display:inline-block;padding:2px 8px;border-radius:11px;color:#fff;font-size:11.5px;
  font-weight:600;white-space:nowrap}
.riesgo{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11.5px;
  font-weight:600;border:1px solid}
.riesgo.critico{background:#fdecea;color:#a1160a;border-color:#f5c2bd}
.riesgo.alto{background:#fff3e0;color:#8a4b00;border-color:#ffd8a8}
.riesgo.medio{background:#fff8e1;color:#7a5b00;border-color:#f2e3a0}
.riesgo.bajo{background:#e8f5e9;color:#1b5e20;border-color:#bfe3c4}
.campo{margin:5px 0}
.campo b{color:#3d444d;font-weight:600}
.controles{display:grid;gap:10px}
.tarjeta-control{background:var(--panel);border:1px solid var(--borde);border-radius:8px;
  overflow:hidden}
.cabecera-control{display:flex;gap:10px;align-items:flex-start;padding:11px 14px;cursor:pointer;
  user-select:none}
.cabecera-control:hover{background:#f2f5f8}
.cabecera-control .id{font-weight:650;font-family:ui-monospace,monospace;font-size:12.5px;
  white-space:nowrap;margin-top:1px}
.cabecera-control .txt{flex:1}
.cuerpo-control{display:none;padding:2px 16px 16px;border-top:1px solid var(--borde);
  background:#fbfcfd}
.tarjeta-control.abierto .cuerpo-control{display:block}
.flecha{color:var(--tenue);transition:transform .15s;flex-shrink:0}
.tarjeta-control.abierto .flecha{transform:rotate(90deg)}
.barra{height:9px;border-radius:5px;overflow:hidden;display:flex;background:#e6e9ed;margin:8px 0 4px}
.barra span{display:block;height:100%}
.leyenda{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--tenue);margin-top:8px}
.leyenda b{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;
  vertical-align:-1px}
.aviso{background:#fff8e1;border-left:4px solid #e8a33d;padding:12px 15px;border-radius:6px;
  margin:12px 0;font-size:13.5px}
.aviso.urgente{background:#fdecea;border-left-color:#d93025}
.filtros{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}
.filtros button{border:1px solid var(--borde);background:#fff;border-radius:16px;padding:5px 13px;
  font-size:12.5px;cursor:pointer;color:#3d444d;font-family:inherit}
.filtros button.activo{background:var(--acento);color:#fff;border-color:var(--acento)}
.oculto{display:none !important}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--borde);color:var(--tenue);
  font-size:12.5px}
@media print{
  body{background:#fff;font-size:11.5pt}
  .filtros,.flecha{display:none}
  .cuerpo-control{display:block !important}
  .tarjeta-control{break-inside:avoid}
  header.cabecera{background:#fff;color:#000;border:1px solid #999}
}
"""

SCRIPT = """
document.addEventListener('click', function(ev){
  var cab = ev.target.closest('.cabecera-control');
  if(cab){ cab.parentElement.classList.toggle('abierto'); return; }
  var boton = ev.target.closest('.filtros button');
  if(boton){
    var grupo = boton.parentElement;
    grupo.querySelectorAll('button').forEach(function(b){b.classList.remove('activo');});
    boton.classList.add('activo');
    var filtro = boton.dataset.filtro;
    // El estado interno usa guion bajo (NO_CUMPLE) y la etiqueta usa espacio
    // (No cumple): se normalizan antes de comparar.
    var normalizar = function(s){ return (s || '').trim().replace(/\\s+/g, '_').toUpperCase(); };
    var objetivo = normalizar(filtro);
    document.querySelectorAll('[data-estado]').forEach(function(nodo){
      var visible = objetivo === 'TODOS' || normalizar(nodo.dataset.estado) === objetivo;
      nodo.classList.toggle('oculto', !visible);
    });
  }
});
"""

TITULO_RIESGO = {
    "critico": "Crítico",
    "alto": "Alto",
    "medio": "Medio",
    "bajo": "Bajo",
}


def _e(texto):
    return html.escape("" if texto is None else str(texto))


def _etiqueta(estado):
    return ('<span class="etiqueta" style="background:%s">%s</span>'
            % (COLOR_ESTADO.get(estado, "#5f6368"), _e(ESTADO_ETIQUETA.get(estado, estado))))


def _riesgo(riesgo):
    return '<span class="riesgo %s">%s</span>' % (
        _e(riesgo), _e(TITULO_RIESGO.get(riesgo, riesgo)))


def _barra(estados, total):
    if not total:
        return ""
    partes = []
    for estado in (CUMPLE, PARCIAL, NO_CUMPLE, NO_VERIFICADO):
        n = estados.get(estado, 0)
        if n:
            partes.append('<span style="width:%.2f%%;background:%s" title="%s %d"></span>'
                          % (100.0 * n / total, COLOR_ESTADO[estado],
                             _e(ESTADO_ETIQUETA[estado]), n))
    return '<div class="barra">%s</div>' % "".join(partes)


def _tarjeta_control(r):
    c = r.control
    pagina = "pág. %d" % c["pagina"] if c["pagina"] else "sin página"
    proc = "Procedimiento %d" % c["proc"] if c["proc"] else "marco legal / documento"
    return """
<div class="tarjeta-control" data-estado="{estado}">
  <div class="cabecera-control">
    <span class="flecha">&#9656;</span>
    <span class="id">{cid}</span>
    <span class="txt"><strong>{enunciado}</strong><br>
      <span style="color:var(--tenue);font-size:12.5px">{proc} &middot; {pagina} &middot; {categoria}</span>
    </span>
    {riesgo} {etiqueta}
  </div>
  <div class="cuerpo-control">
    <div class="campo"><b>Lo que dice el manual o la norma:</b> {enunciado}</div>
    <div class="campo"><b>Resultado de la verificación:</b> {detalle}</div>
    {evidencia}
    <div class="campo"><b>Brecha detectada:</b> {brecha}</div>
    <div class="campo"><b>Cómo se verifica a mano:</b> {verificacion}</div>
    <div class="campo"><b>Acción recomendada:</b> {fix}</div>
    <div class="campo"><b>Referencia:</b> <span class="mono">{ref}</span></div>
  </div>
</div>""".format(
        estado=_e(r.estado), cid=_e(c["id"]), enunciado=_e(c["enunciado"]),
        proc=_e(proc), pagina=_e(pagina), categoria=_e(c["categoria"]),
        riesgo=_riesgo(c["riesgo"]), etiqueta=_etiqueta(r.estado),
        detalle=_e(r.detalle),
        evidencia=('<div class="campo"><b>Evidencia:</b> <span class="mono">%s</span></div>'
                   % _e(r.evidencia)) if r.evidencia else "",
        brecha=_e(c["brecha"]), verificacion=_e(c["verificacion"]),
        fix=_e(c["fix"]), ref=_e(c["ref"]),
    )


def _tabla_hallazgos(hallazgos, limite=None):
    if not hallazgos:
        return '<div class="panel">No se detectaron incumplimientos con la evidencia disponible.</div>'
    filas = []
    for r in hallazgos[:limite] if limite else hallazgos:
        c = r.control
        origen = ("P%d &middot; pág. %d" % (c["proc"], c["pagina"])) if c["proc"] else "Marco legal"
        filas.append(
            "<tr><td><strong>%s</strong><br><span style='color:var(--tenue);font-size:12px'>%s</span></td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                _e(c["id"]), _e(c["enunciado"])[:150], _e(origen), _riesgo(c["riesgo"]),
                _etiqueta(r.estado), _e(r.detalle)[:230]))
    return """
<table>
 <thead><tr><th style="width:34%%">Control</th><th style="width:10%%">Origen</th>
 <th style="width:8%%">Riesgo</th><th style="width:10%%">Estado</th>
 <th style="width:38%%">Detalle</th></tr></thead>
 <tbody>%s</tbody>
</table>""" % "".join(filas)


def html_informe(resultados, tablero_, contexto, catalogo_info):
    e = estados = tablero_["estados"]
    total = tablero_["total"]
    hallazgos = [r for r in resultados if r.es_hallazgo]
    ordenados = sorted(hallazgos, key=lambda r: (RIESGOS.index(r.control["riesgo"]),
                                                 r.control["proc"], r.control["id"]))
    criticos = [r for r in ordenados if r.control["riesgo"] == "critico"]
    altos = [r for r in ordenados if r.control["riesgo"] == "alto"]

    tarjetas = "".join(
        '<div class="tarjeta" style="border-left-color:%s"><span class="n" style="color:%s">%d</span>'
        '<span class="t">%s</span></div>' % (
            COLOR_ESTADO[estado], COLOR_ESTADO[estado], e.get(estado, 0),
            _e(ESTADO_ETIQUETA[estado]))
        for estado in (NO_CUMPLE, PARCIAL, NO_VERIFICADO, CUMPLE))

    criticos_html = "".join(
        '<li><strong>%s</strong> &mdash; %s<br><span style="color:var(--tenue)">%s</span></li>'
        % (_e(r.control["id"]), _e(r.control["brecha"])[:300], _e(r.detalle)[:220])
        for r in criticos[:10]) or "<li>Sin hallazgos críticos.</li>"

    por_proc = {}
    for r in resultados:
        clave = r.control["proc"]
        por_proc.setdefault(clave, []).append(r)
    filas_proc = []
    for proc in sorted(por_proc):
        grupo = por_proc[proc]
        cuenta = {}
        for r in grupo:
            cuenta[r.estado] = cuenta.get(r.estado, 0) + 1
        titulo = ("Procedimiento %d" % proc) if proc else "Marco legal y documento"
        filas_proc.append(
            "<tr><td>%s</td><td>%d</td>%s</tr>" % (
                _e(titulo), len(grupo),
                "".join('<td style="text-align:center">%d</td>' % cuenta.get(estado, 0)
                        for estado in (CUMPLE, PARCIAL, NO_CUMPLE, NO_VERIFICADO))))

    archivos = contexto.evidencia.archivos()

    return """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Auditoría de cumplimiento y ciberseguridad &mdash; Saint Patrick School</title>
<style>{estilo}</style></head><body><div class="envoltura">

<header class="cabecera">
  <h1>Auditoría de cumplimiento y ciberseguridad</h1>
  <p>Saint Patrick School &middot; Manual de Procedimientos 2026-II y Directiva de
     Contratación Pública N° 44/2026</p>
  <p>Generado el {fecha} &middot; {total} controles evaluados &middot;
     dominio auditado: <span class="mono">{dominio}</span></p>
</header>

<div class="aviso urgente">
  <strong>Qué es este informe.</strong> Compara lo que el manual de procedimientos
  declara con lo que se puede verificar realmente. Un control marcado
  <em>Sin verificar</em> no significa que falle: significa que todavía no hay
  evidencia que lo compruebe. La diferencia entre un manual que dice «se hace» y una
  organización donde se hace, es exactamente la distancia que este informe mide.
</div>

<h2>1. Resultado general</h2>
<div class="tarjetas">{tarjetas}</div>
{barra}
<div class="leyenda">
  <span><b style="background:{c_ok}"></b>Cumple</span>
  <span><b style="background:{c_par}"></b>Parcial</span>
  <span><b style="background:{c_noc}"></b>No cumple</span>
  <span><b style="background:{c_nv}"></b>Sin verificar</span>
</div>

<div class="panel" style="margin-top:16px">
  <strong>Cobertura de la verificación automática:</strong>
  {evaluados} de {verificables} controles verificables ({cobertura}% del catálogo técnico).
  Los {humanos} controles restantes son organizacionales, documentales o legales y
  requieren revisión humana: no se pueden verificar sin mirar el documento o la
  práctica real.<br>
  <strong>Hallazgos abiertos:</strong> {hallazgos_n} ({criticos_n} críticos,
  {altos_n} de riesgo alto).
</div>

<h2>2. Los {n_criticos} hallazgos críticos</h2>
<p class="ayuda">Ordenados por impacto. Cada uno cita el control del manual y la
razón por la que importa.</p>
<div class="panel"><ol>{criticos_html}</ol></div>

<h2>3. Plan de acción por prioridad</h2>
<p class="ayuda">Riesgo crítico y alto, con la acción concreta que cierra la brecha.</p>
{plan_accion}

<h2>4. Matriz por procedimiento del manual</h2>
<p class="ayuda">Permite ver de un vistazo qué capítulos están más expuestos.
Un procedimiento con muchos controles «sin verificar» es un procedimiento que
nadie está aplicando en la práctica.</p>
<table>
 <thead><tr><th>Procedimiento</th><th>Controles</th>
 <th style="text-align:center">Cumple</th><th style="text-align:center">Parcial</th>
 <th style="text-align:center">No cumple</th><th style="text-align:center">Sin verificar</th>
 </tr></thead>
 <tbody>{filas_proc}</tbody>
</table>

<h2>5. Detalle de todos los controles</h2>
<p class="ayuda">Haga clic en cualquier control para ver el texto del manual, la
brecha detectada, cómo verificarlo a mano y la acción recomendada.</p>
<div class="filtros">
  <button class="activo" data-filtro="TODOS">Todos ({total})</button>
  <button data-filtro="NO CUMPLE">No cumple ({e_noc})</button>
  <button data-filtro="PARCIAL">Parcial ({e_par})</button>
  <button data-filtro="NO VERIFICADO">Sin verificar ({e_nv})</button>
  <button data-filtro="CUMPLE">Cumple ({e_ok})</button>
</div>
<div class="controles">{controles_html}</div>

<h2>6. Evidencia utilizada</h2>
<div class="panel">
  <p style="margin-top:0">Archivos encontrados en <code>evidencia/</code>:</p>
  {archivos_html}
  <p style="margin-bottom:0">{evidencia_nota}</p>
</div>

<footer>
  Generado por <strong>spaudit</strong> 1.0 &middot; los controles están definidos en
  <code>spaudit/controles_*.py</code> y se pueden editar sin tocar el motor.<br>
  Los controles se basan en el texto del Manual de Procedimientos Saint Patrick School 2026-II
  (páginas citadas en cada ficha) y en la Directiva de Contratación Pública N° 44/2026
  (Resolución Exenta de 12-03-2026). Las referencias externas (CIS, NIST, ISO 27001, OWASP)
  provienen de marcos públicos de ciberseguridad. La verificación legal corresponde
  Confirmarse con asesoría jurídica.
</footer>

</div><script>{script}</script></body></html>
""".format(
        estilo=ESTILO, script=SCRIPT,
        fecha=tablero_["generado"], total=total, dominio=_e(contexto.dominio),
        tarjetas=tarjetas,
        barra=_barra(e, total),
        c_ok=COLOR_ESTADO[CUMPLE], c_par=COLOR_ESTADO[PARCIAL],
        c_noc=COLOR_ESTADO[NO_CUMPLE], c_nv=COLOR_ESTADO[NO_VERIFICADO],
        evaluados=tablero_["evaluados"], verificables=tablero_["verificables"],
        cobertura=tablero_["evaluados_pct"],
        humanos=tablero_["total"] - tablero_["verificables"],
        hallazgos_n=len(hallazgos), criticos_n=len(criticos), altos_n=len(altos),
        n_criticos=len(criticos), criticos_html=criticos_html,
        plan_accion=_tabla_hallazgos(ordenados, limite=40),
        filas_proc="".join(filas_proc),
        controles_html="".join(_tarjeta_control(r) for r in resultados),
        e_noc=e.get(NO_CUMPLE, 0), e_par=e.get(PARCIAL, 0),
        e_nv=e.get(NO_VERIFICADO, 0), e_ok=e.get(CUMPLE, 0),
        archivos_html=("<ul>" + "".join("<li><code>%s</code></li>" % _e(a) for a in archivos) + "</ul>")
                       if archivos else "<em>No se encontró ningún archivo de evidencia.</em>",
        evidencia_nota=("Los controles técnicos marcados «Sin verificar» se pueden evaluar "
                        "ejecutando el script <code>powershell\\recolectar-evidencia.ps1</code> "
                        "en el equipo y copiando el resultado a esta carpeta.")
                       if not archivos else "",
    )


def markdown(resultados, tablero_):
    e = tablero_["estados"]
    lineas = [
        "# Auditoría de cumplimiento y ciberseguridad — Saint Patrick School",
        "",
        "Generado el %s · %d controles · dominio: %s"
        % (tablero_["generado"], tablero_["total"], "saintpatricktemuco.cl"),
        "",
        "## Resumen",
        "",
        "| Estado | Controles |",
        "|---|---:|",
    ]
    for estado in (CUMPLE, PARCIAL, NO_CUMPLE, NO_VERIFICADO, NO_APLICA):
        if e.get(estado):
            lineas.append("| %s | %d |" % (ESTADO_ETIQUETA[estado], e[estado]))
    lineas += [
        "",
        "Cobertura de la verificación automática: %d de %d controles verificables (%d%%)."
        % (tablero_["evaluados"], tablero_["verificables"], tablero_["evaluados_pct"]),
        "",
        "## Hallazgos",
        "",
        "| Control | Origen | Riesgo | Estado | Detalle | Acción |",
        "|---|---|---|---|---|---|",
    ]
    ordenados = sorted([r for r in resultados if r.es_hallazgo],
                       key=lambda r: (RIESGOS.index(r.control["riesgo"]), r.control["proc"]))
    for r in ordenados:
        c = r.control
        origen = ("P%d pág.%d" % (c["proc"], c["pagina"])) if c["proc"] else "Marco legal"
        lineas.append("| `%s` | %s | %s | %s | %s | %s |" % (
            c["id"], origen, RIESGO_ETIQUETA.get(c["riesgo"], c["riesgo"]),
            ESTADO_ETIQUETA.get(r.estado, r.estado),
            r.detalle.replace("|", "/")[:200], c["fix"].replace("|", "/")[:200]))
    lineas += ["", "## Detalle de controles", "",
               "| Control | Procedimiento | Estado | Enunciado |", "|---|---|---|---|"]
    for r in resultados:
        c = r.control
        proc = "P%d pág.%d" % (c["proc"], c["pagina"]) if c["proc"] else "Marco legal"
        lineas.append("| `%s` | %s | %s | %s |" % (
            c["id"], proc, ESTADO_ETIQUETA.get(r.estado, r.estado),
            c["enunciado"].replace("|", "/")[:160]))
    return "\n".join(lineas) + "\n"


def json_informe(resultados, tablero_, contexto):
    return {
        "generado": datetime.datetime.now().isoformat(timespec="seconds"),
        "dominio": contexto.dominio,
        "resumen": tablero_,
        "archivos_evidencia": contexto.evidencia.archivos(),
        "resultados": [r.a_dict() for r in resultados],
    }


def escribir(resultados, tablero_, contexto, carpeta_salida):
    if not os.path.isdir(carpeta_salida):
        os.makedirs(carpeta_salida, exist_ok=True)

    rutas = {}
    html_ = html_informe(resultados, tablero_, contexto, None)
    rutas["html"] = os.path.join(carpeta_salida, "informe-auditoria.html")
    with io.open(rutas["html"], "w", encoding="utf-8") as fh:
        fh.write(html_)

    datos = json_informe(resultados, tablero_, contexto)
    rutas["json"] = os.path.join(carpeta_salida, "informe-auditoria.json")
    with io.open(rutas["json"], "w", encoding="utf-8") as fh:
        json.dump(datos, fh, indent=2, ensure_ascii=False)

    rutas["md"] = os.path.join(carpeta_salida, "informe-auditoria.md")
    with io.open(rutas["md"], "w", encoding="utf-8") as fh:
        fh.write(markdown(resultados, tablero_))

    return rutas