"""/trabaja-con-nosotros: the Spanish version of /work-with-us.

The first real contractor conversation (2026-10-14) was in Spanish, over
WhatsApp, from a cleaner who found the Spanish Facebook recruiting post. She was
then sent to an English-only application form. Most of the people who clean
houses in Tampa Bay for a living speak Spanish first, so the apply page needs
to exist in their language, with the same numbers and the same honesty as the
English one.

Pay figures come from economics.contractor_share, exactly as in careers_page.py,
so the two pages cannot drift apart. The form posts through the same
/js/careers.js and lands in the same leads inbox, tagged IDIOMA: es so the
owner knows to answer in Spanish.

Wording is gender-neutral ("profesionales de limpieza"), never "limpiadoras".

Called from build_markets.py.
"""
import json
import os

from home_v2 import E, faq_items, money
from inner_v2 import call_btn, page_hero

URL_PATH = "/trabaja-con-nosotros"
EN_PATH = "/work-with-us"


def _pay(cfg, tier_id, freq="biweekly"):
    t = next(x for x in cfg["home_tiers"] if x["id"] == tier_id)
    return round(t["prices"][freq] * cfg["economics"]["contractor_share"])


def body_for(cfg, origin):
    share = cfg["economics"]["contractor_share"]
    pct = int(round(share * 100))
    svc = {s["id"]: s for s in cfg["services"]}
    p2, p3, p4 = (_pay(cfg, t) for t in ("t2", "t3", "t4"))
    mv_lo = round(svc["move"]["price_min"] * share)
    mv_hi = round(svc["move"]["price_max"] * share)
    pc_hi = round(svc["construction"]["price_max"] * share)
    phone, phone_raw = cfg["phone"], cfg["phone_raw"]

    hero = page_hero(
        "Trabaja con nosotros",
        "Trabajo de limpieza en Tampa, pagado por trabajo.",
        "La mitad del precio de cada limpieza que haces, y te lo decimos antes de "
        "que aceptes. Sin tarifa por hora, sin mandarte a un lugar por menos de lo "
        "que vale.",
        ctas=['<a class="btn btn-primary" href="#apply">Solicitar</a>', call_btn(cfg)],
        proof=["%d%% del precio del trabajo" % pct,
               "Tú eliges qué trabajos", "Pago semanal"])

    pay = f'''
<section class="h-sec"><div class="wrap narrow">
  <div class="rv"><h2>Lo que paga el trabajo</h2>
  <p class="lede">Recibes el <strong>{pct}% de lo que paga el cliente</strong>,
  y ves ese número antes de aceptar el trabajo. No es una tarifa por hora que
  se queda igual si una casa toma dos horas o cinco.</p></div>
  <div class="p-table-wrap rv"><table class="p-table">
    <thead><tr><th>Trabajo</th><th>Tú recibes</th></tr></thead>
    <tbody>
      <tr><td><strong>2 recámaras, cada dos semanas</strong><span>Unas 2.5&ndash;3 horas</span></td>
        <td class="amt">{money(p2)}</td></tr>
      <tr><td><strong>3 recámaras, cada dos semanas</strong><span>Unas 4&ndash;5 horas</span></td>
        <td class="amt">{money(p3)}</td></tr>
      <tr><td><strong>4 recámaras, cada dos semanas</strong></td><td class="amt">{money(p4)}</td></tr>
      <tr><td><strong>Limpieza de mudanza</strong><span>Medio día a día completo</span></td>
        <td class="amt">{money(mv_lo)}&ndash;{money(mv_hi)}</td></tr>
      <tr><td><strong>Post-construcción</strong><span>Los trabajos más grandes que tomamos</span></td>
        <td class="amt">hasta {money(pc_hi)}</td></tr>
    </tbody></table></div>
  <p class="h-note rv" style="text-align:left">Pago semanal, cada viernes, por los
  trabajos que terminaste la semana anterior. Las propinas son 100% tuyas.</p>
</div></section>'''

    honest = '''
<section class="h-sec alt"><div class="wrap narrow rv">
  <h2>Qué es esto, en palabras claras</h2>
  <p class="lede">Es <strong>trabajo de contratista independiente (1099), no un
  empleo</strong>. Eso tiene dos lados y debes conocerlos antes de solicitar.</p>
  <h3>Lo que recibes</h3>
  <p>Tú eliges los trabajos que quieres. Nadie te pone horario a la fuerza. Se te
  paga por trabajo a un precio acordado de antemano, y un trabajo que te toma
  menos tiempo paga lo mismo. Las propinas son tuyas. Puedes seguir con tus
  propios clientes y trabajar con otras empresas.</p>
  <h3>Lo que pones tú</h3>
  <p>Tu propio transporte, tus propios productos y equipo, y tu propio seguro de
  responsabilidad civil (general liability). Tú te encargas de tus impuestos;
  no se retiene nada. No hay horas garantizadas, ni días festivos pagados, ni
  beneficios.</p>
  <p>Si lo que buscas es horario fijo y cheque de nómina, honestamente este no
  es el arreglo correcto, y preferimos decírtelo ahora que en la segunda semana.</p>
</div></section>'''

    expect = '''
<section class="h-sec"><div class="wrap">
  <div class="rv"><h2>Lo que esperamos</h2></div>
  <div class="h-grid-4 h-promises">
    <div class="rv"><h3>Llegar cuando dijiste</h3><p>Es lo único que hace perder
      clientes. Si algo sale mal, avísanos temprano, no en silencio.</p></div>
    <div class="rv"><h3>Seguir la lista</h3><p>Cada trabajo tiene una lista escrita.
      Así "limpio" deja de ser cuestión de opinión, y te protege a ti tanto como
      al cliente.</p></div>
    <div class="rv"><h3>Fotos al terminar</h3><p>Antes y después, subidas al
      terminar. Es la prueba de que el trabajo se hizo bien.</p></div>
    <div class="rv"><h3>Decir si no puedes</h3><p>Nadie es penalizado por rechazar
      un trabajo. Se deja de ofrecer trabajo a quien acepta y no aparece.</p></div>
  </div>
</div></section>'''

    faqs = [
      {"q": "¿Cuánto trabajo hay?",
       "a": "Somos una empresa nueva y lo decimos con honestidad: hoy no hay una semana "
            "completa de trabajo esperándote. Le sirve a quien está construyendo su propia "
            "cartera de clientes o llenando huecos entre otros trabajos, y crece conforme "
            "crecemos nosotros."},
      {"q": "¿Necesito mi propio seguro?",
       "a": "Sí, seguro de responsabilidad civil (general liability) de $1,000,000 por "
            "incidente / $2,000,000 total, con Tampa Maids Cleaning LLC como asegurado "
            "adicional. Para una persona que limpia por su cuenta cuesta unos $38 a $60 al "
            "mes (Thimble, Insurance Canopy, NEXT, Hiscox) y se saca en línea el mismo día. "
            "No podemos mandarte a la casa de un cliente sin él."},
      {"q": "¿Necesito mis propios productos?",
       "a": "Sí. Productos, equipo y transporte son tuyos. Por eso el reparto es del %d%% "
            "y no un sueldo por hora." % pct},
      {"q": "¿Cuándo me pagan?",
       "a": "Cada semana, los viernes, por los trabajos que terminaste de lunes a domingo "
            "la semana anterior, después de aprobar la lista de verificación."},
      {"q": "¿Tengo que aceptar todos los trabajos que me ofrezcan?",
       "a": "No. Los trabajos se ofrecen y tú aceptas o rechazas. Lo que importa es que, "
            "una vez que aceptas, llegues."},
      {"q": "¿Tengo que ir a algún lado a tomarme las huellas?",
       "a": "No. La verificación de antecedentes se hace en línea con una empresa de "
            "verificación, con tu autorización por escrito, después de que llenes la "
            "solicitud. No tienes que ir a ninguna oficina."},
      {"q": "¿Puedo hablar con alguien en español?",
       "a": "Sí. Escribe o llama al %s, o manda un mensaje de WhatsApp al mismo número."
            % phone},
    ]
    faq_sec = '''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>Preguntas</h2></div>
  <div class="p-faq rv">%s</div>
</div></section>''' % faq_items(faqs)

    apply = '''
<section class="h-sec" id="apply"><div class="wrap narrow rv">
  <h2>Solicitud</h2>
  <p class="lede">Cuéntanos en qué zonas trabajas, cuánta experiencia tienes y
  cuándo estás disponible. Respondemos a todas las personas, en español.</p>
  <form id="applyForm" class="p-form" novalidate data-lang="es"
        data-msg-need="Necesitamos tu nombre, celular y correo para poder responderte."
        data-msg-sending="Enviando…"
        data-msg-ok="¡Gracias! Te respondemos a todas las personas, en español."
        data-msg-err="No se pudo enviar. Por favor llama o manda texto al %s.">
    <div class="field"><label for="a-name">Tu nombre *</label>
      <input id="a-name" type="text" autocomplete="name" required></div>
    <div class="field-row">
      <div class="field"><label for="a-phone">Celular *</label>
        <input id="a-phone" type="tel" autocomplete="tel" required></div>
      <div class="field"><label for="a-email">Correo electrónico *</label>
        <input id="a-email" type="email" autocomplete="email" required></div>
    </div>
    <div class="field"><label for="a-area">¿En qué zonas puedes trabajar?</label>
      <input id="a-area" type="text" placeholder="p. ej. South Tampa, Brandon, Wesley Chapel"></div>
    <div class="field"><label for="a-exp">Experiencia, seguro y disponibilidad</label>
      <textarea id="a-exp" placeholder="Cuánto tiempo llevas limpiando, si ya tienes seguro de
        responsabilidad civil, y qué días tienes libres."></textarea></div>
    <div class="nav-row"><button type="submit" class="btn btn-primary btn-lg"
      id="applyBtn">Enviar solicitud</button></div>
    <p class="hint" id="applyMsg"></p>
  </form>
  <p class="h-note" style="text-align:left"><a href="%s">Read this page in English</a></p>
</div></section>''' % (E(phone), EN_PATH)

    cta = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-final rv">
      <h2>¿Tienes preguntas antes de solicitar?</h2>
      <p>Llama o manda un WhatsApp. Preferimos responderlas ahora y no que te
      enteres después.</p>
      <div class="h-cta" style="justify-content:center;margin:0">
        <a class="btn btn-accent btn-lg" href="#apply">Llenar la solicitud</a>
        <a class="btn btn-white btn-lg" href="tel:{phone_raw}" data-biz-href="phone">Llamar al <span data-biz="phone">{E(phone)}</span></a>
      </div>
    </div>
  </div>
</section>'''

    body = hero + pay + honest + expect + faq_sec + apply + cta

    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "@id": origin + URL_PATH + "#faq", "inLanguage": "es",
             "mainEntity": [{"@type": "Question", "name": f["q"],
                             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                            for f in faqs]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": origin + "/"},
                {"@type": "ListItem", "position": 2, "name": "Trabaja con nosotros",
                 "item": origin + URL_PATH}]},
        ]}, separators=(",", ":"), ensure_ascii=False)

    title = "Trabajo de Limpieza en Tampa | Tampa Maids"
    desc = ("Trabajo de limpieza en Tampa pagado por trabajo, no por hora: %d%% del "
            "precio, tú eliges los trabajos, pago semanal. Contratista 1099." % pct)
    return body, schema, desc, title


def build_careers_page_es(cfg, page, origin, web_dir):
    body, schema, desc, title = body_for(cfg, origin)
    assert len(desc) <= 160, len(desc)
    assert len(title) <= 60, len(title)
    head = ('<script type="application/ld+json">%s</script>\n'
            '<link rel="alternate" hreflang="en" href="%s%s">\n'
            '<link rel="alternate" hreflang="es" href="%s%s">'
            % (schema, origin, EN_PATH, origin, URL_PATH))
    slug = "trabaja-con-nosotros.html"
    page(slug, title, E(desc), body, head=head,
         scripts='<script src="/js/careers.js"></script>', photo="hero")
    # The shared shell hard-codes lang="en"; this is the one Spanish page.
    path = os.path.join(web_dir, slug)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    html = html.replace('<html lang="en">', '<html lang="es">', 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return [URL_PATH]
