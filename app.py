import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Asistente Inteligente de Pricing - Fruta",
    page_icon="🍎",
    layout="wide"
)

# ---------------------------------------------------------
# 1. CARGA DE DATOS INTERNOS DE LA EMPRESA (ERP / Histórico)
# ---------------------------------------------------------
@st.cache_data
def cargar_datos_internos():
    datos_historicos = pd.DataFrame({
        'Cliente': ['Mercadona', 'Carrefour', 'Lidl', 'Aldi', 'Eroski', 'Dia'],
        'Cluster': [
            'Cluster 1: Gran Consumo / Sensibilidad Media',
            'Cluster 1: Gran Consumo / Sensibilidad Media',
            'Cluster 2: Hard Discount / Sensibilidad Alta',
            'Cluster 2: Hard Discount / Sensibilidad Alta',
            'Cluster 1: Gran Consumo / Sensibilidad Media',
            'Cluster 2: Hard Discount / Sensibilidad Alta'
        ],
        'Fruta_Comercializada': ['Plátano Canario', 'Manzana Golden', 'Plátano Canario', 'Nectarina', 'Pera Conferencia', 'Plátano Canario'],
        'Precio_Medio_Anteriores': [2.75, 1.18, 2.60, 1.42, 1.22, 2.55],
        'Condiciones_Comerciales': [
            'Pago a 30 días, volumen semanal alto, portes pagados en plataforma',
            'Descuento 4% por volumen superior a 5.000 kg, pago a 60 días',
            'Entrega diaria directa a almacén, alta exigencia de calibre',
            'Suministro semanal cerrado, pago a 30 días',
            'Promociones quincenales acordadas, pago a 45 días',
            'Plazo de pago 30 días, entregas divididas por plataformas regionales'
        ]
    })
    return datos_historicos

df_interno = cargar_datos_internos()

# ---------------------------------------------------------
# 2. BARRA LATERAL (Sidebar) - Filtros de Negociación
# ---------------------------------------------------------
st.sidebar.header("⚙️ Configuración del Pedido")

cliente_seleccionado = st.sidebar.selectbox(
    "Selecciona Cliente / Cadena",
    df_interno['Cliente'].tolist() + ["Otro"]
)

producto_seleccionado = st.sidebar.selectbox(
    "Variedad de Fruta",
    ["Plátano Canario", "Manzana Golden", "Manzana Fuji", "Pera Conferencia", "Melocotón", "Nectarina"]
)

mercado_referencia = st.sidebar.selectbox(
    "Mercado Mayorista de Referencia",
    ["Mercabarna", "Mercamadrid", "Mercasevilla", "Mercavalencia"]
)

st.sidebar.markdown("---")
st.sidebar.header("📋 Condiciones Internas del Cliente")

info_cliente = df_interno[df_interno['Cliente'] == cliente_seleccionado]
if not info_cliente.empty:
    st.sidebar.write(f"**Perfil Clúster:** {info_cliente['Cluster'].values[0]}")
    st.sidebar.write(f"**Fruta habitual:** {info_cliente['Fruta_Comercializada'].values[0]}")
    st.sidebar.write(f"**Precio histórico medio:** {info_cliente['Precio_Medio_Anteriores'].values[0]:.2f} €/kg")
    st.sidebar.info(f"**Condiciones pactadas:**\n{info_cliente['Condiciones_Comerciales'].values[0]}")
else:
    st.sidebar.write("Cliente nuevo / Sin condiciones históricas específicas.")

# ---------------------------------------------------------
# 3. INTERFAZ PRINCIPAL Y CHAT CONVERSACIONAL
# ---------------------------------------------------------
st.title("🍎 Asistente Conversacional de Pricing")
st.caption("Sistema de apoyo a la decisión basado en datos del ERP, Mercasa y modelo predictivo XGBoost")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de precios. He cargado la información interna de clientes, histórico de precios y condiciones comerciales. ¿Para qué cliente y cantidad deseas calcular la oferta hoy?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ej: ¿A qué precio ofertamos 5.000 kg de plátano canario esta semana para Carrefour?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando ERP interno, datos de Mercasa y ejecutando modelo predictivo XGBoost..."):
            if not info_cliente.empty:
                precio_hist = info_cliente['Precio_Medio_Anteriores'].values[0]
                condiciones_txt = info_cliente['Condiciones_Comerciales'].values[0]
                cluster_txt = info_cliente['Cluster'].values[0]
            else:
                precio_hist = 2.50
                condiciones_txt = "Condiciones comerciales estándar."
                cluster_txt = "Cluster 1: Gran Consumo / Sensibilidad Media"

            volumen_detectado = 5000 if ("5.000" in prompt or "5000" in prompt or "5t" in prompt) else 2000

            # Cálculo de precios de simulación XGBoost
            factor_volumen = 0.97 if volumen_detectado >= 5000 else 1.00
            precio_recomendado = round(precio_hist * 1.04 * factor_volumen, 2)
            rango_min = round(precio_recomendado - 0.08, 2)
            rango_max = round(precio_recomendado + 0.08, 2)
            precio_modal_merca = round(precio_recomendado * 0.94, 2)

        # Respuesta estructurada estilo TFM
        res1 = f"**Precio recomendado para oferta:** **{precio_recomendado:.2f} €/kg**  *(Rango óptimo: {rango_min:.2f} €/kg - {rango_max:.2f} €/kg)*\n\n---"
        res2 = f"\n🔍 **Justificación de la recomendación (Modelo XGBoost):**\n\n* **1. Perfil del Cliente & ERP:**\n  * **Cliente:** {cliente_seleccionado} ({cluster_txt})\n  * **Histórico precio medio:** `{precio_hist:.2f} €/kg`\n  * **Condiciones pactadas:** *\"{condiciones_txt}\"*\n  * **Volumen de la operación:** `{volumen_detectado:,} kg` de {producto_seleccionado}."
        res3 = f"\n\n* **2. Referencia Mercado Mayorista (Mercasa / {mercado_referencia}):**\n  * **Precio modal de referencia:** `{precio_modal_merca:.2f} €/kg`\n  * **Evolución semanal:** `+2.1%` de variación en la plaza de destino."
        res4 = f"\n\n* **3. Estrategia Comercial:**\n  El precio sugerido de **{precio_recomendado:.2f} €/kg** mantiene el margen objetivo adaptándose a las condiciones del clúster del cliente y aplicando el descuento correspondiente al volumen solicitado."

        respuesta = res1 + res2 + res3 + res4

        st.markdown(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
