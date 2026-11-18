"""
datos.py — Contenido completo del juego Clic Seguro.

33 incidentes: Nivel 0 (1) + N1 (6) + N2 (8) + N3 (8) + N4 (10).
Escala monetaria: $800 iniciales, $500 matrícula, fraudes -$15 a -$150.

Los campos interaccion/monto_solicitado/cuenta_destino/titular_destino
están rellenos pero INACTIVOS hasta Bloque E (config.INTERACCION_ACTIVA).
"""

# ============================================================
# CONSEJOS
# ============================================================
CONSEJOS = {
    "otp_nunca_se_comparte": {
        "titulo": "El código OTP nunca se comparte",
        "texto": (
            "Ninguna empresa legítima te pedirá el código de 6 dígitos que llega "
            "a tu celular. Ese código es tu llave personal: quien lo recibe, "
            "entra a tu cuenta. Si alguien lo pide, es una estafa."
        ),
        "tipo": "otp", "key_voz": "consejo_otp",
    },
    "urgencia_es_tactica": {
        "titulo": "La urgencia es la táctica del estafador",
        "texto": (
            "Frases como AHORA, ÚLTIMA OPORTUNIDAD o SU CUENTA SERÁ BLOQUEADA "
            "buscan que no pienses. Detenerte y verificar es tu mejor defensa."
        ),
        "tipo": "urgencia", "key_voz": "consejo_urgencia",
    },
    "typosquatting": {
        "titulo": "Un carácter puede cambiar todo",
        "texto": (
            "Los estafadores imitan dominios reales cambiando una letra "
            "(banc0lombia con cero en vez de o). Mira siempre la URL exacta."
        ),
        "tipo": "enlace", "key_voz": "consejo_typo",
    },
    "verificar_por_voz": {
        "titulo": "Ante un conocido que pide dinero, llama",
        "texto": (
            "Si un amigo o familiar pide plata por chat, llámalo por voz al "
            "número que ya tienes guardado. Las cuentas se roban; la voz no."
        ),
        "tipo": "acoso", "key_voz": "consejo_llamar",
    },
    "no_callar_acoso": {
        "titulo": "Callar deja libre al agresor",
        "texto": (
            "El acoso no se resuelve ignorando. Guarda evidencia, bloquea, "
            "reporta en la plataforma y en el CAI Virtual, y cuéntale a alguien."
        ),
        "tipo": "acoso", "key_voz": "consejo_acoso",
    },
    "banco_canal_oficial": {
        "titulo": "El banco no pide datos por llamada",
        "texto": (
            "Ningún banco pide contraseñas, claves ni transferencias por "
            "teléfono. Cuelga y llama al número del reverso de tu tarjeta."
        ),
        "tipo": "banco", "key_voz": "consejo_banco",
    },
    "activar_2fa": {
        "titulo": "El 2FA es tu mejor escudo",
        "texto": (
            "Activar la verificación en dos pasos y el perfil privado reduce "
            "drásticamente el riesgo de robo de cuenta."
        ),
        "tipo": "urgencia", "key_voz": "consejo_2fa",
    },
    "desconfiar_tambien_cuesta": {
        "titulo": "Desconfiar de todo también cuesta",
        "texto": (
            "Bloquear o ignorar mensajes legítimos te aísla y te hace perder "
            "oportunidades. La clave no es desconfiar de todo, sino verificar."
        ),
        "tipo": "urgencia", "key_voz": "consejo_desconfiar",
    },
    "verificar_titular": {
        "titulo": "Revisa el titular antes de transferir",
        "texto": (
            "Antes de confirmar una transferencia, mira el nombre del titular. "
            "Si dice un nombre distinto al de tu contacto, cancela."
        ),
        "tipo": "banco", "key_voz": "consejo_titular",
    },
}


# ============================================================
# NIVEL 0 — DOMINGO: tutorial narrativo
# ============================================================
INCIDENTES_N0 = [
    {
        "id": "n0_01", "nivel": 0, "dia": "Domingo",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {
            "nombre": "Mamá", "numero": "+57 310 555 0011",
            "en_contactos": True, "cuenta_dias": 3650, "reportes": 0,
            "verificado": True, "pista": "Es tu mamá. Está en tus contactos.",
        },
        "texto": "Hijo, cuídate mucho mañana en tu primer día. Cualquier cosa me llamas. Te quiero.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Respondiste a tu mamá. Es un mensaje real.",
        "feedback_err": "Era tu mamá. Ignorarla o bloquearla cuesta reputación.",
        "consejo": None,
        "verificacion_llamada": "Mamá contesta: '¿Mi amor, todo bien?'",
        "verificacion_oficial": "Contacto verificado en tu agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n0_02", "nivel": 0, "dia": "Domingo",
        "tipo": "whatsapp", "categoria": "fraude",
        "remitente": {
            "nombre": "Premios Campus", "numero": "+1 555 013 7742",
            "en_contactos": False, "cuenta_dias": 2, "reportes": 11,
            "verificado": False,
            "pista": "Cuenta nueva, número internacional y muchos reportes.",
        },
        "texto": "¡Felicidades! Ganaste una beca de $300. Reclámala HOY en beca-campus-premios.com",
        "enlace": {"url": "beca-campus-premios.com/reclamar", "oficial": False,
                   "pista": "Imita a la universidad, pero no es su dominio oficial (.edu.co)."},
        "requiere_urgencia": False,
        "respuesta_correcta": "REPORTAR",
        "respuestas_aceptables": ["REPORTAR", "IGNORAR", "BLOQUEAR"],
        # Práctica: equivocarse aquí no cuesta nada ni suma puntos.
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": 0, "xp": 0},
        "feedback_ok": "Reportaste la estafa de práctica. Reportar protege a otros.",
        "feedback_err": "Era una estafa de práctica. Mira el dominio: imitaba a la universidad.",
        "consejo": "typosquatting",
        "verificacion_llamada": "Nadie contesta ese número internacional.",
        "verificacion_oficial": "La universidad confirma que esa beca no existe.",
        "verificacion_busqueda": "Decenas de reportes: es una estafa conocida.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
        "es_tutorial": True,
    },
]


# ============================================================
# NIVEL 1 — LUNES: señales claras
# ============================================================
INCIDENTES_N1 = [
    {
        "id": "n1_01", "nivel": 1, "dia": "Lunes",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Mamá", "numero": "+57 310 555 0011",
                      "en_contactos": True, "cuenta_dias": 3650,
                      "reportes": 0, "verificado": True,
                      "pista": "Es tu mamá. Está en tus contactos."},
        "texto": "Hijo, ¿ya llegaste a la U? Cuéntame cómo te va. Te quiero.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Respondiste a tu mamá. Es un mensaje real.",
        "feedback_err": "Era tu mamá. Ignorarla cuesta reputación.",
        "consejo": "desconfiar_tambien_cuesta",
        "verificacion_llamada": "Mamá contesta: '¿Si hijo, qué pasó?'",
        "verificacion_oficial": "Número en tu agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n1_02", "nivel": 1, "dia": "Lunes",
        "tipo": "email", "categoria": "legitimo",
        "remitente": {"nombre": "Universidad - Registro",
                      "numero": "registro@universidad.edu.co",
                      "en_contactos": True, "cuenta_dias": 2000,
                      "reportes": 0, "verificado": True,
                      "pista": "Dominio institucional oficial."},
        "texto": "Bienvenido al semestre 2026-2. Tu horario está disponible en el portal estudiantil.",
        "enlace": {"url": "portal.universidad.edu.co", "oficial": True,
                   "pista": "Dominio oficial."},
        "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Aviso legítimo de la universidad.",
        "feedback_err": "Era la universidad. Ignorar cuesta reputación.",
        "consejo": None,
        "verificacion_llamada": "Conmutador universitario, mensaje pregrabado.",
        "verificacion_oficial": "Dominio institucional oficial.",
        "verificacion_busqueda": "Institución verificada, sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n1_03", "nivel": 1, "dia": "Lunes",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Valentina", "numero": "+57 315 555 0042",
                      "en_contactos": True, "cuenta_dias": 800,
                      "reportes": 0, "verificado": True,
                      "pista": "Es tu mejor amiga."},
        "texto": "Cami, ¿nos vemos en la biblioteca a las 3? Llevo apuntes de cálculo.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es Valentina. Responder refuerza tu círculo.",
        "feedback_err": "Era Valentina. Ignorarla daña la relación.",
        "consejo": None,
        "verificacion_llamada": "Valentina contesta: 'Cami, ¿qué pasó?'",
        "verificacion_oficial": "En tu agenda hace años.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n1_04", "nivel": 1, "dia": "Lunes",
        "tipo": "whatsapp", "categoria": "fraude",
        "remitente": {"nombre": "Sorteo Universitario",
                      "numero": "+1 555 013 2290",
                      "en_contactos": False, "cuenta_dias": 2,
                      "reportes": 14, "verificado": False,
                      "pista": "Número internacional, cuenta nueva, 14 reportes."},
        "texto": "¡Felicidades! Ganaste un iPhone 15. Reenvía a 10 amigos y reclama tu premio.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "IGNORAR",
        "respuestas_aceptables": ["IGNORAR", "REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": -10, "dinero": 0, "reputacion": -5, "xp": 0},
        "feedback_ok": "Ignoraste el sorteo falso. Las cadenas no dan premios.",
        "feedback_err": "Era un sorteo falso. Reenviar quema privacidad.",
        "consejo": "urgencia_es_tactica",
        "verificacion_llamada": "Número internacional, no contesta.",
        "verificacion_oficial": "NO es un canal oficial de la universidad.",
        "verificacion_busqueda": "14 usuarios lo reportaron como estafa.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n1_05", "nivel": 1, "dia": "Lunes",
        "tipo": "email", "categoria": "fraude",
        "remitente": {"nombre": "Soporte Universitario",
                      "numero": "soporte@univers1dad-soporte.com",
                      "en_contactos": False, "cuenta_dias": 5,
                      "reportes": 8, "verificado": False,
                      "pista": "La i de universidad fue cambiada por 1."},
        "texto": "Su correo sera suspndido por falta de actualisacion. Haga clic aqui.",
        "enlace": {"url": "univers1dad-soporte.com/activar", "oficial": False,
                   "pista": "Dominio con 1 en vez de i."},
        "requiere_urgencia": False,
        "respuesta_correcta": "IGNORAR",
        "respuestas_aceptables": ["IGNORAR", "REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": -20, "dinero": 0, "reputacion": -5, "xp": 0},
        "feedback_ok": "Detectaste el correo falso. Los typos son señal.",
        "feedback_err": "Abriste un enlace malicioso.",
        "consejo": "typosquatting",
        "verificacion_llamada": "No aplica (es email).",
        "verificacion_oficial": "El dominio 'univers1dad-soporte.com' NO existe.",
        "verificacion_busqueda": "Reportado 8 veces como phishing.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n1_06", "nivel": 1, "dia": "Lunes",
        "tipo": "instagram", "categoria": "fraude",
        "remitente": {"nombre": "Tienda Ganga Oficial",
                      "numero": "@tienda_ganga_oficial",
                      "en_contactos": False, "cuenta_dias": 3,
                      "reportes": 22, "verificado": False,
                      "pista": "Cuenta nueva, 22 reportes, sin verificar."},
        "texto": "Últimos iPhone 14 a $30. Solo hoy. Compra aquí antes que se agoten.",
        "enlace": {"url": "tienda-ganga-ofertas.net/iphone", "oficial": False,
                   "pista": "Precio imposible. Dominio sin reputación."},
        "requiere_urgencia": False,
        "respuesta_correcta": "IGNORAR",
        "respuestas_aceptables": ["IGNORAR", "REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": -5, "dinero": -30, "reputacion": 0, "xp": 0},
        "feedback_ok": "Ignoraste la oferta falsa. Precio imposible = estafa.",
        "feedback_err": "Transferiste $30 a un sitio falso. No vuelve.",
        "consejo": "urgencia_es_tactica",
        "verificacion_llamada": "Número no contesta.",
        "verificacion_oficial": "Cuenta de Instagram sin verificar.",
        "verificacion_busqueda": "22 reportes. Precio imposible.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
]


# ============================================================
# NIVEL 2 — MIÉRCOLES: + Rappi legítimo + urgencia legítima
# ============================================================
INCIDENTES_N2 = [
    {
        "id": "n2_01", "nivel": 2, "dia": "Miércoles",
        "tipo": "email", "categoria": "legitimo",
        "remitente": {"nombre": "Universidad - Tesorería",
                      "numero": "tesoreria@universidad.edu.co",
                      "en_contactos": True, "cuenta_dias": 2000,
                      "reportes": 0, "verificado": True,
                      "pista": "Canal institucional oficial."},
        "texto": "AVISO IMPORTANTE: el pago de matrícula vence el viernes. Ingresa al portal oficial.",
        "enlace": {"url": "portal.universidad.edu.co/pagos", "oficial": True,
                   "pista": "Subdominio del dominio oficial."},
        "requiere_urgencia": True,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Verificar el aviso por el canal oficial es correcto.",
        "feedback_err": "Era la universidad real. Ignorarla cuesta reputación.",
        "consejo": None,
        "verificacion_llamada": "Tesoría universitaria confirma el plazo.",
        "verificacion_oficial": "Dominio oficial de la universidad.",
        "verificacion_busqueda": "Sin reportes. Institución verificada.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_02", "nivel": 2, "dia": "Miércoles",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Andrés (compañero)",
                      "numero": "+57 316 555 0077",
                      "en_contactos": True, "cuenta_dias": 200,
                      "reportes": 0, "verificado": True,
                      "pista": "Compañero de clase, número guardado."},
        "texto": "Parce, ¿me pasas el taller de cálculo? Te lo agradezco.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es un compañero real.",
        "feedback_err": "Era tu compañero. Ignorarlo daña la relación.",
        "consejo": None,
        "verificacion_llamada": "Andrés contesta.",
        "verificacion_oficial": "En tu agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_03", "nivel": 2, "dia": "Miércoles",
        "tipo": "sms", "categoria": "legitimo",
        "remitente": {"nombre": "Banco Nacional",
                      "numero": "+57 601 555 0000",
                      "en_contactos": True, "cuenta_dias": 3650,
                      "reportes": 0, "verificado": True,
                      "pista": "Canal oficial del banco."},
        "texto": "Tu extracto de octubre está disponible en la app oficial. No compartas tus claves.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Verificar el aviso por la app oficial es correcto.",
        "feedback_err": "Era el banco real.",
        "consejo": None,
        "verificacion_llamada": "Banco confirma el extracto.",
        "verificacion_oficial": "Número oficial en tu tarjeta.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_04", "nivel": 2, "dia": "Miércoles",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Domiciliario Rappi",
                      "numero": "+57 305 555 0312",
                      "en_contactos": False, "cuenta_dias": 60,
                      "reportes": 0, "verificado": False,
                      "pista": "Número desconocido. Pero es un domiciliario."},
        "texto": "Hola, soy tu domiciliario de Rappi. Estoy abajo con tu pedido. ¿Bajo o subo?",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Verificar en la app confirma que sí pediste Rappi.",
        "feedback_err": "Era real. Ignorar al domiciliario te deja sin pedido.",
        "consejo": "desconfiar_tambien_cuesta",
        "verificacion_llamada": "Un domiciliario dice que está abajo.",
        "verificacion_oficial": "La app de Rappi confirma tu pedido.",
        "verificacion_busqueda": "Número sin reportes. Normal para domiciliarios.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_05", "nivel": 2, "dia": "Miércoles",
        "tipo": "whatsapp", "categoria": "fraude",
        "remitente": {"nombre": "Soporte WhatsApp",
                      "numero": "+1 555 013 2290",
                      "en_contactos": False, "cuenta_dias": 2,
                      "reportes": 14, "verificado": False,
                      "pista": "Cuenta nueva, número internacional."},
        "texto": "Detectamos un inicio de sesión desde otro dispositivo. Envía el código de 6 dígitos AHORA.",
        "enlace": None, "requiere_urgencia": True,
        "respuesta_correcta": "IGNORAR",
        "respuestas_aceptables": ["IGNORAR", "REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": -40, "dinero": 0, "reputacion": -20, "xp": 0},
        "feedback_ok": "No caíste en la estafa del código.",
        "feedback_err": "Entregaste el código. Tu cuenta fue tomada.",
        "consejo": "otp_nunca_se_comparte",
        "verificacion_llamada": "No contesta.",
        "verificacion_oficial": "WhatsApp NUNCA pide el código por chat.",
        "verificacion_busqueda": "Reportado 14 veces como estafa.",
        "interaccion": "otp", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_06", "nivel": 2, "dia": "Miércoles",
        "tipo": "llamada", "categoria": "fraude",
        "remitente": {"nombre": "Banco Nacional - Seguridad",
                      "numero": "+57 300 555 0999",
                      "en_contactos": False, "cuenta_dias": 1,
                      "reportes": 30, "verificado": False,
                      "pista": "Este número NO es el del banco."},
        "texto": "Su cuenta será bloqueada. Confirme su clave para desbloquearla.",
        "enlace": None, "requiere_urgencia": True,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["VERIFICAR", "BLOQUEAR"],
        "impacto": {"privacidad": -20, "dinero": -50, "reputacion": 0, "xp": 0},
        "feedback_ok": "Colgaste y llamaste al banco por el canal oficial.",
        "feedback_err": "Diste tus datos al falso banco.",
        "consejo": "banco_canal_oficial",
        "verificacion_llamada": "Voz robótica pide datos.",
        "verificacion_oficial": "Este número NO es del banco.",
        "verificacion_busqueda": "30 reportes.",
        "interaccion": "transferencia", "monto_solicitado": 50,
        "cuenta_destino": "0987", "titular_destino": "J. Rodríguez",
        "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_07", "nivel": 2, "dia": "Miércoles",
        "tipo": "sms", "categoria": "fraude",
        "remitente": {"nombre": "Secretaría de Movilidad",
                      "numero": "sms@movilidad-pagos.co",
                      "en_contactos": False, "cuenta_dias": 3,
                      "reportes": 18, "verificado": False,
                      "pista": "Dominio oficial es movilidad.gov.co."},
        "texto": "Tiene una multa pendiente de $20. Pague antes del viernes o su vehículo será inmovilizado.",
        "enlace": {"url": "movilidad-pagos.co/pagar", "oficial": False,
                   "pista": "Dominio .co sin .gov. No es oficial."},
        "requiere_urgencia": True,
        "respuesta_correcta": "IGNORAR",
        "respuestas_aceptables": ["IGNORAR", "BLOQUEAR", "VERIFICAR"],
        "impacto": {"privacidad": -5, "dinero": -20, "reputacion": 0, "xp": 0},
        "feedback_ok": "Ignoraste la multa falsa. El dominio no era oficial.",
        "feedback_err": "Pagaste una multa falsa.",
        "consejo": "urgencia_es_tactica",
        "verificacion_llamada": "No aplica (SMS).",
        "verificacion_oficial": "El dominio oficial es movilidad.gov.co.",
        "verificacion_busqueda": "18 reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n2_08", "nivel": 2, "dia": "Miércoles",
        "tipo": "sms", "categoria": "fraude",
        "remitente": {"nombre": "Envíos Express",
                      "numero": "+57 301 555 0234",
                      "en_contactos": False, "cuenta_dias": 5,
                      "reportes": 11, "verificado": False,
                      "pista": "Empresa no guardada. 11 reportes."},
        "texto": "Su paquete está retenido en aduana. Pague $15 para liberarlo: bit.ly/envio-2024",
        "enlace": {"url": "bit.ly/envio-2024", "oficial": False,
                   "pista": "Acortador oculta el destino real."},
        "requiere_urgencia": False,
        "respuesta_correcta": "IGNORAR",
        "respuestas_aceptables": ["IGNORAR", "REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": -15, "dinero": -15, "reputacion": 0, "xp": 0},
        "feedback_ok": "Ignoraste el paquete falso.",
        "feedback_err": "Caíste en el fraude del paquete.",
        "consejo": "typosquatting",
        "verificacion_llamada": "No contesta.",
        "verificacion_oficial": "Empresas reales no usan bit.ly.",
        "verificacion_busqueda": "11 reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
]


# ============================================================
# NIVEL 3 — JUEVES: Valentina hackeada + fraudes sin typos
# ============================================================
INCIDENTES_N3 = [
    {
        "id": "n3_01", "nivel": 3, "dia": "Jueves",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Mamá", "numero": "+57 310 555 0011",
                      "en_contactos": True, "cuenta_dias": 3650,
                      "reportes": 0, "verificado": True,
                      "pista": "Está en tus contactos."},
        "texto": "Hijo, llámame cuando puedas, tengo una duda con el recibo de la luz.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es tu mamá. Contestar mantiene la confianza.",
        "feedback_err": "Era tu mamá.",
        "consejo": None,
        "verificacion_llamada": "Mamá contesta.",
        "verificacion_oficial": "Número en tu agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n3_02", "nivel": 3, "dia": "Jueves",
        "tipo": "email", "categoria": "legitimo",
        "remitente": {"nombre": "Prof. Rodríguez",
                      "numero": "prof.rodriguez@universidad.edu.co",
                      "en_contactos": True, "cuenta_dias": 1500,
                      "reportes": 0, "verificado": True,
                      "pista": "Correo institucional del profesor."},
        "texto": "Buenas tardes, las notas del segundo corte ya están publicadas en el portal.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Aviso real del profesor.",
        "feedback_err": "Era el profesor.",
        "consejo": None,
        "verificacion_llamada": "El profesor contesta.",
        "verificacion_oficial": "Correo institucional.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n3_03", "nivel": 3, "dia": "Jueves",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Valentina", "numero": "+57 315 555 0042",
                      "en_contactos": True, "cuenta_dias": 800,
                      "reportes": 0, "verificado": True,
                      "pista": "Tu mejor amiga, número guardado."},
        "texto": "JAJAJA mira este meme del profe de física.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es Valentina. Ignorarla te aísla.",
        "feedback_err": "Era Valentina.",
        "consejo": None,
        "verificacion_llamada": "Valentina contesta con su voz.",
        "verificacion_oficial": "Número verificado en tu agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n3_04", "nivel": 3, "dia": "Jueves",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Andrés (compañero)",
                      "numero": "+57 316 555 0077",
                      "en_contactos": True, "cuenta_dias": 200,
                      "reportes": 0, "verificado": True,
                      "pista": "Compañero de clase."},
        "texto": "¿Estudiamos mañana para el parcial? Llevo café.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es un compañero real.",
        "feedback_err": "Era tu compañero.",
        "consejo": None,
        "verificacion_llamada": "Andrés contesta.",
        "verificacion_oficial": "En tu agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n3_05", "nivel": 3, "dia": "Jueves",
        "tipo": "whatsapp", "categoria": "fraude",
        "remitente": {"nombre": "Valentina", "numero": "+57 315 555 0042",
                      "en_contactos": True, "cuenta_dias": 800,
                      "reportes": 0, "verificado": True,
                      "pista": "El número es de Valentina. Pero la cuenta puede estar hackeada."},
        "texto": "Cami, me quedé sin plata y no puedo pagar el bus. ¿Me prestas $50? Te los devuelvo mañana.",
        "enlace": None, "requiere_urgencia": True,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": -50, "reputacion": -10, "xp": 0},
        "feedback_ok": "Llamaste a Valentina y confirmaste que era falso.",
        "feedback_err": "Transferiste dinero a una cuenta hackeada.",
        "consejo": "verificar_por_voz",
        "verificacion_llamada": "Valentina contesta: 'No te escribí nada, mi cuenta está hackeada'.",
        "verificacion_oficial": "El titular de la cuenta destino es 'María P.', no Valentina.",
        "verificacion_busqueda": "No hay reportes, pero el número es de Valentina.",
        "interaccion": "transferencia", "monto_solicitado": 50,
        "cuenta_destino": "4821", "titular_destino": "María P.",
        "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n3_06", "nivel": 3, "dia": "Jueves",
        "penaliza_ignorar": True,   # callar ante el acoso es el error
        "tipo": "instagram", "categoria": "fraude",
        "remitente": {"nombre": "@_anon_2024_", "numero": "@_anon_2024_",
                      "en_contactos": False, "cuenta_dias": 1,
                      "reportes": 6, "verificado": False,
                      "pista": "Cuenta nueva, sin foto real, 6 reportes."},
        "texto": "Eres un gordo asqueroso, nadie te quiere. Deja de publicar fotos.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "REPORTAR",
        "respuestas_aceptables": ["REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -25, "xp": 0},
        "feedback_ok": "Reportaste al acosador. El silencio lo deja libre.",
        "feedback_err": "Callaste ante el acoso.",
        "consejo": "no_callar_acoso",
        "verificacion_llamada": "No aplica (perfil de Instagram).",
        "verificacion_oficial": "Cuenta creada hace 1 día, 6 reportes.",
        "verificacion_busqueda": "6 usuarios lo reportaron.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n3_07", "nivel": 3, "dia": "Jueves",
        "penaliza_ignorar": True,   # callar ante el acoso es el error
        "tipo": "instagram", "categoria": "fraude",
        "remitente": {"nombre": "@_anon_2024_", "numero": "@_anon_2024_",
                      "en_contactos": False, "cuenta_dias": 1,
                      "reportes": 6, "verificado": False,
                      "pista": "El mismo perfil anónimo sigue hostigando."},
        "texto": "Mira la foto que subí de ti, todos se están riendo. [imagen editada]",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "REPORTAR",
        "respuestas_aceptables": ["REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": -10, "dinero": 0, "reputacion": -25, "xp": 0},
        "feedback_ok": "Reportaste la publicación.",
        "feedback_err": "No reportaste la foto editada.",
        "consejo": "no_callar_acoso",
        "verificacion_llamada": "No aplica.",
        "verificacion_oficial": "Misma cuenta que el mensaje anterior.",
        "verificacion_busqueda": "6 reportes acumulados.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n3_08", "nivel": 3, "dia": "Jueves",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Papelería Universitaria",
                      "numero": "+57 602 555 0456",
                      "en_contactos": True, "cuenta_dias": 500,
                      "reportes": 0, "verificado": True,
                      "pista": "Proveedor oficial de la universidad."},
        "texto": "Hola Camilo, el material del semestre cuesta $40. ¿Confirmas para prepararlo?",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Pagaste el material a tiempo.",
        "feedback_err": "No pagaste el material. No tendrás con qué estudiar.",
        "consejo": None,
        "verificacion_llamada": "Papelería contesta, confirma el monto.",
        "verificacion_oficial": "Proveedor oficial de la universidad.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "transferencia", "monto_solicitado": 40,
        "cuenta_destino": "3231", "titular_destino": "Papelería Universitaria SAS",
        "es_familiar": False, "es_evento": False,
    },
]


# ============================================================
# NIVEL 4 — VIERNES: mix de todas las trampas
# ============================================================
INCIDENTES_N4 = [
    {
        "id": "n4_01", "nivel": 4, "dia": "Viernes",
        "tipo": "email", "categoria": "legitimo",
        "remitente": {"nombre": "Universidad - Registro",
                      "numero": "registro@universidad.edu.co",
                      "en_contactos": True, "cuenta_dias": 2000,
                      "reportes": 0, "verificado": True,
                      "pista": "Canal institucional."},
        "texto": "Los resultados del primer parcial están disponibles en el portal.",
        "enlace": {"url": "portal.universidad.edu.co/notas", "oficial": True,
                   "pista": "Subdominio oficial."},
        "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Aviso real de la universidad.",
        "feedback_err": "Era la universidad.",
        "consejo": None,
        "verificacion_llamada": "Conmutador universitario.",
        "verificacion_oficial": "Dominio oficial.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_02", "nivel": 4, "dia": "Viernes",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Mamá", "numero": "+57 310 555 0011",
                      "en_contactos": True, "cuenta_dias": 3650,
                      "reportes": 0, "verificado": True,
                      "pista": "Contacto real."},
        "texto": "Te quiero, hijo. Que te vaya bien hoy.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es tu mamá.",
        "feedback_err": "Era tu mamá.",
        "consejo": None,
        "verificacion_llamada": "Mamá contesta.",
        "verificacion_oficial": "En agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n4_03", "nivel": 4, "dia": "Viernes",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Valentina", "numero": "+57 315 555 0042",
                      "en_contactos": True, "cuenta_dias": 800,
                      "reportes": 0, "verificado": True,
                      "pista": "Contacto real."},
        "texto": "Cami, ¿vamos por un café después de clase?",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es Valentina.",
        "feedback_err": "Era Valentina.",
        "consejo": None,
        "verificacion_llamada": "Valentina contesta.",
        "verificacion_oficial": "En agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": True, "es_evento": False,
    },
    {
        "id": "n4_04", "nivel": 4, "dia": "Viernes",
        "tipo": "whatsapp", "categoria": "legitimo",
        "remitente": {"nombre": "Andrés (compañero)",
                      "numero": "+57 316 555 0077",
                      "en_contactos": True, "cuenta_dias": 200,
                      "reportes": 0, "verificado": True,
                      "pista": "Compañero real."},
        "texto": "Subí el archivo del proyecto al drive del grupo.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "CONFIAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Es tu compañero.",
        "feedback_err": "Era tu compañero.",
        "consejo": None,
        "verificacion_llamada": "Andrés contesta.",
        "verificacion_oficial": "En agenda.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_05", "nivel": 4, "dia": "Viernes",
        "tipo": "sms", "categoria": "legitimo",
        "remitente": {"nombre": "Banco Nacional", "numero": "+57 601 555 0000",
                      "en_contactos": True, "cuenta_dias": 3650,
                      "reportes": 0, "verificado": True,
                      "pista": "Canal oficial."},
        "texto": "Tu transacción de $15 en la cafetería fue aprobada.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["CONFIAR", "VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -10, "xp": 0},
        "feedback_ok": "Verificar en la app confirma el cargo.",
        "feedback_err": "Era el banco real.",
        "consejo": None,
        "verificacion_llamada": "Banco confirma la transacción.",
        "verificacion_oficial": "Número oficial.",
        "verificacion_busqueda": "Sin reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_06", "nivel": 4, "dia": "Viernes",
        "tipo": "whatsapp", "categoria": "fraude",
        "remitente": {"nombre": "Soporte WhatsApp", "numero": "+1 555 013 2290",
                      "en_contactos": False, "cuenta_dias": 2,
                      "reportes": 14, "verificado": False,
                      "pista": "Cuenta nueva, número internacional."},
        "texto": "Último aviso: tu cuenta será eliminada en 1 hora si no envías el código de 6 dígitos.",
        "enlace": None, "requiere_urgencia": True,
        "respuesta_correcta": "REPORTAR",
        "respuestas_aceptables": ["REPORTAR", "IGNORAR", "BLOQUEAR"],
        "impacto": {"privacidad": -40, "dinero": 0, "reputacion": -20, "xp": 0},
        "feedback_ok": "Reportaste el fraude del código.",
        "feedback_err": "Caíste en la estafa del código.",
        "consejo": "otp_nunca_se_comparte",
        "verificacion_llamada": "No contesta.",
        "verificacion_oficial": "WhatsApp NUNCA pide código por chat.",
        "verificacion_busqueda": "14 reportes.",
        "interaccion": "otp", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_07", "nivel": 4, "dia": "Viernes",
        "tipo": "instagram", "categoria": "fraude",
        "remitente": {"nombre": "Viajes Premium",
                      "numero": "@viajes_premium_oficial",
                      "en_contactos": False, "cuenta_dias": 4,
                      "reportes": 19, "verificado": False,
                      "pista": "Cuenta nueva, 19 reportes."},
        "texto": "¡Ganaste un viaje a Cancún todo pagado! Reclama antes de 24 horas.",
        "enlace": {"url": "premios-viajes.click/reclamar", "oficial": False,
                   "pista": "Dominio .click sin reputación."},
        "requiere_urgencia": False,
        "respuesta_correcta": "REPORTAR",
        "respuestas_aceptables": ["REPORTAR", "IGNORAR", "BLOQUEAR"],
        "impacto": {"privacidad": -15, "dinero": -50, "reputacion": 0, "xp": 0},
        "feedback_ok": "Reportaste el sorteo falso.",
        "feedback_err": "Caíste en el sorteo falso.",
        "consejo": "urgencia_es_tactica",
        "verificacion_llamada": "No contesta.",
        "verificacion_oficial": "Dominio .click sin reputación.",
        "verificacion_busqueda": "19 reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_08", "nivel": 4, "dia": "Viernes",
        "penaliza_ignorar": True,   # callar ante el acoso es el error
        "tipo": "instagram", "categoria": "fraude",
        "remitente": {"nombre": "@_anon_2024_", "numero": "@_anon_2024_",
                      "en_contactos": False, "cuenta_dias": 1,
                      "reportes": 6, "verificado": False,
                      "pista": "Cuenta nueva y reportada."},
        "texto": "¿Sigues publicando fotos? Deberías tener vergüenza.",
        "enlace": None, "requiere_urgencia": False,
        "respuesta_correcta": "REPORTAR",
        "respuestas_aceptables": ["REPORTAR", "BLOQUEAR"],
        "impacto": {"privacidad": 0, "dinero": 0, "reputacion": -25, "xp": 0},
        "feedback_ok": "Reportaste al acosador.",
        "feedback_err": "Callaste ante el acoso.",
        "consejo": "no_callar_acoso",
        "verificacion_llamada": "No aplica.",
        "verificacion_oficial": "Cuenta nueva.",
        "verificacion_busqueda": "6 reportes.",
        "interaccion": "ninguna", "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_09", "nivel": 4, "dia": "Viernes",
        "tipo": "llamada", "categoria": "fraude",
        "remitente": {"nombre": "Banco Nacional", "numero": "+57 300 555 0999",
                      "en_contactos": False, "cuenta_dias": 1,
                      "reportes": 30, "verificado": False,
                      "pista": "Este número NO es del banco."},
        "texto": "Su tarjeta fue clonada. Confirme su clave para cancelar la operación.",
        "enlace": None, "requiere_urgencia": True,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["VERIFICAR", "BLOQUEAR"],
        "impacto": {"privacidad": -20, "dinero": -50, "reputacion": 0, "xp": 0},
        "feedback_ok": "Colgaste y llamaste al banco por el canal oficial.",
        "feedback_err": "Diste tu clave al falso banco.",
        "consejo": "banco_canal_oficial",
        "verificacion_llamada": "Voz robótica pide datos.",
        "verificacion_oficial": "Este número NO es del banco.",
        "verificacion_busqueda": "30 reportes.",
        "interaccion": "transferencia", "monto_solicitado": 50,
        "cuenta_destino": "0987", "titular_destino": "J. Rodríguez",
        "es_familiar": False, "es_evento": False,
    },
    {
        "id": "n4_10", "nivel": 4, "dia": "Viernes",
        "tipo": "whatsapp", "categoria": "fraude",
        "remitente": {"nombre": "Tío Hernán", "numero": "+57 311 555 0777",
                      "en_contactos": False, "cuenta_dias": 1,
                      "reportes": 3, "verificado": False,
                      "pista": "Tu tío real usa otro número."},
        "texto": "Soy tu tío. Tu mamá tuvo un accidente. Necesito $150 para el hospital. Transfiere ya.",
        "enlace": None, "requiere_urgencia": True,
        "respuesta_correcta": "VERIFICAR",
        "respuestas_aceptables": ["VERIFICAR"],
        "impacto": {"privacidad": 0, "dinero": -150, "reputacion": -10, "xp": 0},
        "feedback_ok": "Verificaste por voz. Era un suplantador.",
        "feedback_err": "Transferiste al falso familiar.",
        "consejo": "verificar_por_voz",
        "verificacion_llamada": "Número no contesta.",
        "verificacion_oficial": "Número no está en contactos.",
        "verificacion_busqueda": "3 reportes.",
        "interaccion": "transferencia", "monto_solicitado": 150,
        "cuenta_destino": "9412", "titular_destino": "Carlos R.",
        "es_familiar": False, "es_evento": False,
    },
]


# ============================================================
# NIVELES
# ============================================================
NIVELES = [
    {
        "id": 0, "dia": "Domingo",
        "titulo": "Antes de todo",
        "objetivo": "Conocer a Camilo y a su mamá. Aprender a leer un mensaje.",
        "incidentes": INCIDENTES_N0,
        "tutorial": True,
    },
    {
        "id": 1, "dia": "Lunes",
        "titulo": "Bienvenida universitaria",
        "objetivo": "Aprender las acciones y herramientas sin perder recursos.",
        "incidentes": INCIDENTES_N1,
        "tutorial": True,
    },
    {
        "id": 2, "dia": "Miércoles",
        "titulo": "La llamada del pánico",
        "objetivo": "Resistir la urgencia: no dar códigos ni datos bajo presión.",
        "incidentes": INCIDENTES_N2,
        "tutorial": False,
    },
    {
        "id": 3, "dia": "Jueves",
        "titulo": "Círculo cercano vulnerado",
        "objetivo": "Verificar por voz y aplicar el protocolo ante acoso.",
        "incidentes": INCIDENTES_N3,
        "tutorial": False,
    },
    {
        "id": 4, "dia": "Viernes",
        "titulo": "El examen final",
        "objetivo": "Aplicar todo sin pistas visuales.",
        "incidentes": INCIDENTES_N4,
        "tutorial": False,
    },
]


# ============================================================
# CINEMÁTICA DE INTRO (spec 10): 5 pantallas narrativas
# "{dinero}" lo rellena main.py con config.DINERO_INICIAL_V2.
# "voz" es lo que se dice en voz alta (MODO_VOZ robot/grabado);
# key_voz es el nombre del audio grabado: intro_p1.ogg ...
# ============================================================
INTRO_PAGINAS = [
    {"key_voz": "intro_p1", "titulo": "Domingo, 6:00 PM",
     "texto": "Casa de Camilo. Último día antes de la universidad.",
     "voz": "Domingo, seis de la tarde. Casa de Camilo. "
            "Último día antes de la universidad."},
    {"key_voz": "intro_p2", "titulo": "Tu primer celular",
     "texto": "Tus padres te dieron tu primer celular y ${dinero} para el semestre. "
              "El viernes debes pagar ${matricula} de matrícula.",
     "voz": "Tus padres te dieron tu primer celular y {dinero} para el semestre. "
            "El viernes debes pagar la matrícula: {matricula}."},
    {"key_voz": "intro_p3", "titulo": "Pero hay un peligro",
     "texto": "Hay gente que usa mensajes falsos para robarte datos, dinero y reputación.",
     "voz": "Pero hay un peligro. Hay gente que usa mensajes falsos para robarte "
            "tus datos, tu dinero y tu reputación."},
    {"key_voz": "intro_p4", "titulo": "Tus tres recursos",
     "texto": "Cuida tu Privacidad, tu Dinero y tu Reputación. Si alguno llega a cero, pierdes el nivel.",
     "voz": "Cuida tus tres recursos: tu privacidad, tu dinero y tu reputación. "
            "Si alguno llega a cero, pierdes el nivel."},
    {"key_voz": "intro_p5", "titulo": "Tu misión",
     "texto": "Llega al viernes, paga la matrícula y aprende a detectar los engaños.",
     "voz": "Tu misión: llegar al viernes, pagar la matrícula y aprender a "
            "detectar los engaños."},
    {"key_voz": "intro_p6", "titulo": "Practica primero",
     "texto": "Llegan tus primeros mensajes. Te enseñaré cómo se juega, paso a paso.",
     "voz": "Llegan tus primeros mensajes. Te enseñaré cómo se juega, paso a paso."},
]


# ============================================================
# TUTORIAL GUIADO (specs/14_tutorial.md)
# Sigue la práctica del Domingo sobre las pantallas reales. Cada paso:
#   id      nombre corto (clave de la voz: tut_<id>)
#   estado  pantalla de main.py donde ocurre
#   tipo    "info"  -> explica; solo se pulsa "Siguiente"
#           "click" -> obliga a pulsar el botón `foco`
#   foco    botón (p. ej. "tool_remitente") o zona (p. ej. "hud") que se resalta
#   texto   lo que se lee en el globo
#   voz     lo que se dice (con cifras en palabras, para que suene bien)
#   boton   (opcional) texto del botón "Siguiente"
# ============================================================
TUTORIAL_PASOS = [
    {"id": "semana", "estado": "HOME", "tipo": "info", "foco": "semana",
     "texto": "Esta es tu semana. Hoy es domingo y el viernes vence la matrícula.",
     "voz": "Esta es tu semana. Hoy es domingo, y el viernes vence la matrícula."},
    {"id": "banco", "estado": "HOME", "tipo": "info", "foco": "app_banco",
     "texto": "Aquí está tu dinero: tienes $800 para todo el semestre y el viernes debes pagar $500.",
     "voz": "Aquí está tu dinero. Tienes ochocientos para todo el semestre, y el viernes debes pagar quinientos de matrícula."},
    {"id": "abrir_mensajes", "estado": "HOME", "tipo": "click", "foco": "app_mensajes",
     "texto": "Te llegó un mensaje. Toca Mensajes para leerlo.",
     "voz": "Te llegó un mensaje. Toca Mensajes para leerlo."},
    {"id": "recursos", "estado": "MESSAGE_LIST", "tipo": "info", "foco": "hud",
     "texto": "Estas barras son tus recursos: Privacidad, Dinero y Reputación. Si una llega a cero, pierdes el nivel.",
     "voz": "Estas barras son tus recursos: privacidad, dinero y reputación. Si una llega a cero, pierdes el nivel."},
    {"id": "abrir_mama", "estado": "MESSAGE_LIST", "tipo": "click", "foco": "open_0",
     "texto": "Es de tu mamá. Tócalo para abrirlo.",
     "voz": "Es de tu mamá. Tócalo para abrirlo."},
    {"id": "leer", "estado": "CHAT", "tipo": "info", "foco": "mensaje",
     "texto": "Antes de decidir, mira quién escribe y qué te pide.",
     "voz": "Antes de decidir, mira quién escribe y qué te pide."},
    {"id": "remitente", "estado": "CHAT", "tipo": "click", "foco": "tool_remitente",
     "texto": "Investiga primero. Toca Remitente para saber si es de confianza. Cada herramienta que uses suma puntos.",
     "voz": "Investiga primero. Toca Remitente para saber si es de confianza. Cada herramienta que uses suma puntos."},
    {"id": "senales", "estado": "MODAL", "tipo": "click", "foco": "cerrar_modal",
     "texto": "Mamá está en tus contactos y su número coincide: es de confianza. Cierra esta ventana.",
     "voz": "Mamá está en tus contactos y su número coincide: es de confianza. Cierra esta ventana."},
    {"id": "confiar", "estado": "CHAT", "tipo": "click", "foco": "action_confiar",
     "texto": "Es tu mamá y todo coincide. Toca Confiar.",
     "voz": "Es tu mamá y todo coincide. Toca Confiar."},
    {"id": "acierto", "estado": "FEEDBACK", "tipo": "click", "foco": "siguiente",
     "texto": "¡Bien hecho! Acertar suma puntos; equivocarte te cuesta recursos. Sigamos.",
     "voz": "¡Bien hecho! Acertar suma puntos; equivocarte te cuesta recursos. Sigamos."},
    {"id": "abrir_sospechoso", "estado": "MESSAGE_LIST", "tipo": "click", "foco": "open_1",
     "texto": "Ahora uno sospechoso. Es de práctica: aquí equivocarte no cuesta nada. Ábrelo.",
     "voz": "Ahora uno sospechoso. Es de práctica: aquí equivocarte no cuesta nada. Ábrelo."},
    {"id": "senal_estafa", "estado": "CHAT", "tipo": "info", "foco": "mensaje",
     "texto": "Un premio que no pediste, con prisa y con un enlace. Mala señal.",
     "voz": "Un premio que no pediste, con prisa y con un enlace. Mala señal."},
    {"id": "enlace", "estado": "CHAT", "tipo": "click", "foco": "tool_enlace",
     "texto": "Toca Enlace para ver a dónde lleva en realidad.",
     "voz": "Toca Enlace para ver a dónde lleva en realidad."},
    {"id": "dominio", "estado": "MODAL", "tipo": "click", "foco": "cerrar_modal",
     "texto": "El dominio imita a la universidad, pero no es el oficial. Cierra esta ventana.",
     "voz": "El dominio imita a la universidad, pero no es el oficial. Cierra esta ventana."},
    {"id": "acciones", "estado": "CHAT", "tipo": "info", "foco": "action_verificar",
     "texto": "Si dudas, Verificar te deja investigar con una llamada, el canal oficial o una búsqueda, sin riesgo.",
     "voz": "Si dudas, Verificar te deja investigar con una llamada, el canal oficial o una búsqueda, sin riesgo."},
    {"id": "reportar", "estado": "CHAT", "tipo": "click", "foco": "action_reportar",
     "texto": "Esto es una estafa. Toca Reportar para avisar y proteger a otros.",
     "voz": "Esto es una estafa. Toca Reportar para avisar y proteger a otros."},
    {"id": "reportado", "estado": "FEEDBACK", "tipo": "click", "foco": "siguiente",
     "texto": "Muy bien. Ante un fraude, reportar es lo más seguro.",
     "voz": "Muy bien. Ante un fraude, reportar es lo más seguro."},
    {"id": "consejo", "estado": "PANEL", "tipo": "click", "foco": "entendido",
     "texto": "Cada consejo que desbloqueas se guarda en Mis aprendizajes. Toca Entendido para seguir.",
     "voz": "Cada consejo que desbloqueas se guarda en Mis aprendizajes. Toca Entendido para seguir."},
    {"id": "fin", "estado": "RESUMEN", "tipo": "info", "foco": None, "boton": "Empezar",
     "texto": "Eso es todo, Camilo. Mañana empieza la semana de verdad: investiga antes de actuar.",
     "voz": "Eso es todo, Camilo. Mañana empieza la semana de verdad: investiga antes de actuar."},
]


# ============================================================
# ANIMACIÓN EXPLICATIVA (specs/15_animacion.md)
# Estilo anuncio educativo: escenas vectoriales animadas con narración y
# subtítulos. Cada escena dura lo que dura su audio (+ una pausa) o `min_ms`.
#   id        nombre de la escena (clave de la voz: anim_<id>; la dibuja escenas.py)
#   etiqueta  rótulo de color arriba ("" = ninguno)
#   color     azul | verde | rojo | ambar
#   voz       la narración (también son los subtítulos)
# ============================================================
ANIMACION_ESCENAS = [
    {"id": "mensajes", "etiqueta": "TU CELULAR", "color": "azul", "min_ms": 4500,
     "voz": "Cada día recibes decenas de mensajes en tu celular."},
    {"id": "trampa", "etiqueta": "LA TRAMPA", "color": "rojo", "min_ms": 7500,
     "voz": "Pero algunos no son lo que parecen. Son trampas para robar tus datos, "
            "tu dinero o tu reputación."},
    {"id": "habitos", "etiqueta": "", "color": "azul", "min_ms": 3600,
     "voz": "Tres hábitos te protegen."},
    {"id": "investiga", "etiqueta": "1 · INVESTIGA", "color": "azul", "min_ms": 6500,
     "voz": "Uno: investiga antes de actuar. Mira quién escribe y a dónde lleva el enlace."},
    {"id": "verifica", "etiqueta": "2 · VERIFICA", "color": "verde", "min_ms": 7000,
     "voz": "Dos: verifica por un canal oficial. Llama al número que ya conoces, "
            "no al que viene en el mensaje."},
    {"id": "codigos", "etiqueta": "3 · NO COMPARTAS CÓDIGOS", "color": "rojo", "min_ms": 6500,
     "voz": "Tres: nunca compartas tus códigos, ni siquiera con alguien que diga "
            "ser del banco."},
    {"id": "prisa", "etiqueta": "LA PRISA", "color": "ambar", "min_ms": 7000,
     "voz": "Y desconfía de la prisa: los estafadores te apuran para que no pienses. "
            "Detente y verifica."},
    {"id": "mision", "etiqueta": "TU MISIÓN", "color": "verde", "min_ms": 8000,
     "voz": "Tu misión: llegar al viernes, pagar tu matrícula y proteger tu privacidad, "
            "tu dinero y tu reputación."},
    {"id": "cierre", "etiqueta": "", "color": "azul", "min_ms": 4000,
     "voz": "Clic Seguro. Cada clic tiene consecuencias."},
]


# ============================================================
# VOZ: qué se dice en voz alta (specs/13_dia_y_voz.md)
# Textos escritos PARA SER HABLADOS: explican qué hizo mal el jugador, por qué
# y qué señal debió notar. Evitan cifras y monedas ("$40") para que suenen bien.
# ============================================================
VOZ_ERRORES = {
    # ── Nivel 0 y 1 ──
    "n0_01": "Fallaste. Era tu mamá, un contacto guardado en tu celular. Ignorarla o bloquearla sin razón le hace daño a tu reputación.",
    "n0_02": "Fallaste. Era una estafa de práctica: un premio que no pediste, con prisa y desde un enlace que imita a la universidad. Antes de actuar, revisa el dominio.",
    "n1_01": "Fallaste. Era tu mamá preguntando cómo te va. Desconfiar de las personas reales también tiene un costo: pierdes reputación.",
    "n1_02": "Fallaste. Era un aviso legítimo de la universidad, desde su correo y su portal oficiales. Ignorarlo te deja sin información importante.",
    "n1_03": "Fallaste. Era Valentina, una amiga guardada en tus contactos. Ignorarla daña la relación y tu reputación.",
    "n1_04": "Fallaste. Era un sorteo falso: nadie regala un teléfono por reenviar un mensaje. Esas cadenas solo buscan tus contactos y tus datos.",
    "n1_05": "Fallaste. Era un correo falso. El dominio imita al de la universidad cambiando una letra por un número, y el texto tiene errores de ortografía. Esas son señales de estafa.",
    "n1_06": "Fallaste. Una oferta con un precio imposible es una estafa. El enlace no era de una tienda oficial, y el solo hoy busca que no pienses.",
    # ── Nivel 2 ──
    "n2_01": "Fallaste. Era un aviso real de la tesorería, con el dominio oficial de la universidad. Lo correcto era verificarlo en el portal, no ignorarlo.",
    "n2_02": "Fallaste. Era tu compañero Andrés, que está en tus contactos. Ignorarlo sin motivo daña la relación.",
    "n2_03": "Fallaste. Era un aviso real del banco: solo avisaba que tu extracto estaba disponible en la aplicación y no pedía claves. Verifica en la aplicación antes de descartarlo.",
    "n2_04": "Fallaste. Era tu domiciliario de Rappi, y sí habías hecho un pedido. Antes de ignorar, revisa en la aplicación: desconfiar de todo también cuesta.",
    "n2_05": "Fallaste. Entregaste tu código de verificación. Ese código es la llave de tu cuenta: nunca lo compartas, ni con alguien que diga ser de soporte.",
    "n2_06": "Fallaste. El banco jamás te pide tu clave por mensaje. Era un falso banco y ahora tiene tus datos. Cuando dudes, cuelga y llama al número oficial.",
    "n2_07": "Fallaste. Era una multa falsa. La página no tenía el dominio oficial y te apuraba con una amenaza. Pagar desde el enlace de un mensaje es una trampa.",
    "n2_08": "Fallaste. Era el fraude del paquete retenido. Usaba un enlace acortado y un pago urgente. Las empresas de envíos reales no cobran así.",
    # ── Nivel 3 ──
    "n3_01": "Fallaste. Era tu mamá. Ignorar a tu familia sin verificar cuesta reputación.",
    "n3_02": "Fallaste. Era tu profesor, desde su correo institucional guardado en tus contactos. Era un aviso real.",
    "n3_03": "Fallaste. Era Valentina compartiendo un meme. Ignorar a tus amigos te aísla.",
    "n3_04": "Fallaste. Era tu compañero Andrés invitándote a estudiar. Era un mensaje real.",
    "n3_05": "Fallaste. La cuenta de Valentina había sido hackeada y quien escribía era un impostor. Antes de transferir dinero, llama a la persona y confirma por voz.",
    "n3_06": "Fallaste. Callarte ante el acoso lo deja libre para seguir. Reporta y bloquea a quien te insulta.",
    "n3_07": "Fallaste. Esa foto editada es acoso. No reportarla permite que se siga difundiendo. Guarda evidencia y repórtala.",
    "n3_08": "Fallaste. La papelería es un contacto real y el cobro coincidía con lo que pedían. Si no pagas el material, no tendrás con qué estudiar.",
    # ── Nivel 4 ──
    "n4_01": "Fallaste. Era un aviso real de la universidad, con tus resultados en el portal oficial.",
    "n4_02": "Fallaste. Era tu mamá deseándote un buen día.",
    "n4_03": "Fallaste. Era Valentina invitándote a un café.",
    "n4_04": "Fallaste. Era tu compañero Andrés avisando que subió el archivo del proyecto.",
    "n4_05": "Fallaste. Era un aviso real del banco sobre una compra pequeña tuya. Lo correcto era revisarlo en la aplicación.",
    "n4_06": "Fallaste. Otra vez la estafa del código: nadie del soporte te pide el código de seis dígitos, y la presión de una hora es una táctica para asustarte.",
    "n4_07": "Fallaste. Era un sorteo falso, con un dominio extraño y una urgencia de veinticuatro horas. Los premios reales no se reclaman así.",
    "n4_08": "Fallaste. Callarte ante el acoso no lo detiene. Reporta y bloquea al agresor.",
    "n4_09": "Fallaste. El banco nunca te pide tu clave para cancelar una operación. Era un falso banco. Cuelga y llama al número oficial.",
    "n4_10": "Fallaste. Quien escribía no era tu tío: era un suplantador que usaba una emergencia para apurarte. Antes de transferir, verifica por voz con tu familia.",
}

# Se dice ANTES de la explicación cuando el temporizador se agotó.
VOZ_ERROR_TIEMPO = ("Se agotó el tiempo y Camilo confió sin verificar. Los estafadores "
                    "te apuran para que no pienses: ante la urgencia, detente y verifica.")

# No cayó en la estafa (ignoró o bloqueó) pero la mejor respuesta era otra: no pierde
# nada, no suma puntos y se le explica qué era lo ideal. Una por respuesta ideal.
VOZ_PARCIAL = {
    "verificar": "No caíste en la trampa, y eso es lo más importante. Pero aquí lo ideal era verificar antes de actuar: una llamada o el canal oficial te confirman si es real, sin arriesgar nada.",
    "reportar": "No caíste en la trampa. Pero aquí lo ideal era reportarlo, para proteger también a otras personas.",
    "ignorar": "No caíste en la trampa. Pero aquí lo ideal era ignorarlo, sin responder.",
    "bloquear": "No caíste en la trampa. Pero aquí lo ideal era bloquear al remitente.",
}

# Por qué se perdió el nivel (la pantalla de derrota también lo explica).
VOZ_DERROTA = {
    "privacidad": "Perdiste el nivel. Tu privacidad llegó a cero: entregaste demasiados datos o códigos y perdiste el control de tu información.",
    "dinero": "Perdiste el nivel. Te quedaste sin dinero. Las estafas y los pagos agotaron tu saldo, y sin saldo no puedes cubrir los gastos ni la matrícula.",
    "reputacion": "Perdiste el nivel. Tu reputación llegó a cero: tu familia y tus contactos dejaron de confiar en ti.",
    "gasto": "Perdiste la partida. No te alcanzó el dinero para los gastos del día, y sin dinero para lo básico no puedes seguir la semana.",
}


# ============================================================
# VALIDACIÓN
# ============================================================
def _validar():
    ids = set()
    acciones_validas = {"CONFIAR", "VERIFICAR", "IGNORAR", "BLOQUEAR", "REPORTAR"}
    total_fraude = 0
    total_legitimo = 0

    for nivel in NIVELES:
        for inc in nivel["incidentes"]:
            assert inc["id"] not in ids, f"ID duplicado: {inc['id']}"
            ids.add(inc["id"])
            assert inc["nivel"] == nivel["id"], f"{inc['id']}: nivel inconsistente"
            assert inc["respuesta_correcta"] in acciones_validas, \
                f"{inc['id']}: respuesta_correcta inválida"
            assert inc["respuesta_correcta"] in inc["respuestas_aceptables"], \
                f"{inc['id']}: respuesta_correcta no está en aceptables"
            for a in inc["respuestas_aceptables"]:
                assert a in acciones_validas, f"{inc['id']}: acción inválida {a}"
            if inc["consejo"] is not None:
                assert inc["consejo"] in CONSEJOS, \
                    f"{inc['id']}: consejo inexistente '{inc['consejo']}'"
            if inc["categoria"] == "fraude":
                total_fraude += 1
            else:
                total_legitimo += 1

    assert set(VOZ_ERRORES) == ids, \
        f"VOZ_ERRORES no coincide con los incidentes: {set(VOZ_ERRORES) ^ ids}"

    print(f"OK · {len(ids)} incidentes validados")
    print(f"    Fraude: {total_fraude} · Legítimos: {total_legitimo}")
    print(f"    Consejos: {len(CONSEJOS)} · Frases de error con voz: {len(VOZ_ERRORES)}")
    print("    Máximo de puntos: ver Game.puntaje_maximo() (800)")


if __name__ == "__main__":
    _validar()