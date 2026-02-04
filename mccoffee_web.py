import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIGURACIÓN Y BASES DE DATOS ---
st.set_page_config(page_title="MCCOFFEE COMMAND CENTER", layout="wide")
CLAVE_MAESTRA = "mccoffee2026"
ZONA_HORARIA = pytz.timezone('America/Mexico_City')

db_v, db_p, db_s, db_a, db_st, db_m, db_mw = "base_ventas.csv", "base_productos.csv", "base_stock.csv", "base_auditoria.csv", "base_staff.csv", "meta.txt", "meta_semanal.txt"

def preparar():
    files = [
        (db_v, ["ID","Fecha","Vend","Cli","Tel","Prod","Monto","Est"]),
        (db_p, ["Cod","Nom","Pre","Uni"]),
        (db_s, ["Cod","Cant"]),
        (db_a, ["Vendedor","Cod","Entregado","Vendido","Actual"]),
        (db_st, ["Nombre"])
    ]
    for f, c in files:
        if not os.path.exists(f): pd.DataFrame(columns=c).to_csv(f, index=False)
    if not os.path.exists(db_m):
        with open(db_m, "w") as f: f.write("5000")
    if not os.path.exists(db_mw):
        with open(db_mw, "w") as f: f.write("30000")

preparar()

# CARGA DE DATOS
df_v = pd.read_csv(db_v)
# Convertimos a datetime naive para evitar errores de comparación
df_v['Fecha_DT'] = pd.to_datetime(df_v['Fecha'], dayfirst=True, errors='coerce').dt.tz_localize(None)
df_p = pd.read_csv(db_p); df_s = pd.read_csv(db_s); df_a = pd.read_csv(db_a); df_st = pd.read_csv(db_st)

with open(db_m, "r") as f: meta_diaria = float(f.read())
with open(db_mw, "r") as f: meta_semanal = float(f.read())

# --- 🎨 ESTILO "DIAMANTE NEGRO" PREMIUM (BADGES AMPLIADOS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    
    .block-container {{ padding-top: 3.5rem !important; }}

    .stApp {{ 
        background: radial-gradient(circle at top left, #1a1a1a 0%, #050505 100%);
        color: white; 
    }}

    .titulo-mccoffee {{ 
        text-align: center; color: #d4af37; font-family: 'Impact'; font-size: 42px; line-height: 1.1;
        text-shadow: 0px 4px 15px rgba(212, 175, 55, 0.4); margin-bottom: 25px;
    }}

    /* Reloj Digital con Fecha en Sidebar */
    .live-clock {{
        font-family: 'Orbitron', sans-serif; color: #f1c40f; text-align: center;
        text-shadow: 0px 0px 10px rgba(241, 196, 15, 0.5);
        background: rgba(255,255,255,0.03); border-radius: 8px; padding: 10px; margin-bottom: 15px;
    }}
    .clock-date {{ font-size: 0.8rem; color: #d4af37; opacity: 0.8; margin-bottom: 2px; }}
    .clock-time {{ font-size: 1.2rem; font-weight: bold; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: transparent; }}
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255, 255, 255, 0.05); border-radius: 12px 12px 0 0;
        color: #888; padding: 10px 20px; border: 1px solid rgba(212, 175, 55, 0.1);
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(180deg, #f1c40f, #d4af37) !important;
        color: black !important; font-weight: bold;
        box-shadow: 0px 0px 15px rgba(241, 196, 15, 0.5) !important;
    }}

    /* Badge de Tiempo y Fecha en Pedidos */
    .card-pedido {{
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 12px; padding: 15px; margin-bottom: 15px;
    }}
    .time-badge-fixed {{
        background: rgba(212, 175, 55, 0.15); color: #f1c40f; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-family: 'Orbitron', sans-serif;
        border: 1px solid rgba(241, 196, 15, 0.4); white-space: nowrap; text-align: center;
    }}

    .feed-item {{
        padding: 8px; background: rgba(212, 175, 55, 0.05); border-left: 4px solid #f1c40f;
        margin-bottom: 5px; border-radius: 4px; font-size: 13px;
    }}

    .ranking-row {{ 
        background: rgba(255, 255, 255, 0.03); padding: 8px 12px; border-radius: 6px; 
        margin-bottom: 5px; border-left: 3px solid #d4af37; font-size: 14px;
    }}

    .total-gigante {{ color: #d4af37; font-size: 55px !important; font-weight: bold; text-align: center; }}
    hr {{ border: 0; height: 1px; background: linear-gradient(90deg, transparent, #d4af37, transparent); }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (RELOJ + RANKING) ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mccoffee'>CONTROL TOTAL<br>MCCOFFEE</h1>", unsafe_allow_html=True)
    
    ahora_mx = datetime.now(ZONA_HORARIA)
    # Reloj con Fecha y Hora
    st.markdown(f"""
        <div class='live-clock'>
            <div class='clock-date'>📅 {ahora_mx.strftime('%d/%b/%Y')}</div>
            <div class='clock-time'>🕒 {ahora_mx.strftime('%H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    ahora_naive = ahora_mx.replace(tzinfo=None)
    hoy = ahora_naive.date()
    
    st.markdown("---")
    df_hoy = df_v[df_v['Fecha_DT'].dt.date == hoy]
    v_hoy = df_hoy['Monto'].sum()
    v_sem = df_v[df_v['Fecha_DT'] >= (ahora_naive - timedelta(days=7))]['Monto'].sum()
    
    st.metric("CORTE DE HOY", f"${v_hoy:,.2f}")
    st.progress(min(v_hoy / meta_diaria, 1.0) if meta_diaria > 0 else 0)
    st.caption(f"Meta Diaria: ${meta_diaria:,.0f}")
    
    st.markdown("---")
    st.markdown("### 🏆 RANKING DIARIO")
    if not df_st.empty:
        ventas_hoy = df_hoy.groupby('Vend')['Monto'].sum().reset_index()
        ranking = pd.merge(df_st, ventas_hoy, left_on='Nombre', right_on='Vend', how='left').fillna(0)
        ranking = ranking.sort_values(by='Monto', ascending=False)
        for _, r in ranking.iterrows():
            meta_ind = meta_diaria / len(df_st) if len(df_st) > 0 else 1000
            progreso_barra = min(r['Monto'] / meta_ind, 1.0)
            porcentaje_real = (r['Monto'] / meta_diaria * 100) if meta_diaria > 0 else 0
            st.markdown(f"<div class='ranking-row'><div style='display:flex; justify-content:space-between;'><b>{r['Nombre']}</b><span>${r['Monto']:,.0f} ({porcentaje_real:.0f}%)</span></div></div>", unsafe_allow_html=True)
            st.progress(progreso_barra)

    st.markdown("---")
    st.write("📅 PROGRESO SEMANAL")
    st.metric("VENTA SEMANA", f"${v_sem:,.2f}")
    st.progress(min(v_sem / meta_semanal, 1.0) if meta_semanal > 0 else 0)
    st.caption(f"Objetivo Semanal: ${meta_semanal:,.0f}")

# --- 3. PESTAÑAS ---
tab_v, tab_p, tab_d, tab_j = st.tabs(["🚀 VENTAS", "📋 PEDIDOS", "📊 DASHBOARD", "🔐 PANEL JEFE"])

with tab_v: # REGISTRO DE VENTAS
    c1, c2, c3 = st.columns(3); l_st = df_st['Nombre'].tolist() if not df_st.empty else ["CONFIGURAR STAFF"]
    v_v = c1.selectbox("Vendedor", l_st, key="v_sel_1")
    v_c = c2.text_input("Cliente").upper(); v_t = c3.text_input("WhatsApp")
    
    c4, c5, c6, c7 = st.columns([2, 1, 1, 1]) 
    v_p = c4.selectbox("Producto", df_p['Cod'].tolist() if not df_p.empty else ["N/A"], key="v_sel_2")
    precio_base = float(df_p[df_p['Cod'] == v_p]['Pre'].values[0]) if not df_p.empty and v_p in df_p['Cod'].values else 0.0
    v_precio_final = c5.number_input("Precio ($)", min_value=0.0, value=precio_base, step=1.0)
    v_ca = c6.number_input("Cant.", min_value=0.1, value=1.0, key="v_num_1")
    
    if c7.button("➕ AÑADIR"):
        if 'car' not in st.session_state: st.session_state.car = []
        pi = df_p[df_p['Cod'] == v_p].iloc[0] if not df_p.empty else None
        nom_prod = pi['Nom'] if pi is not None else "Item"
        st.session_state.car.append({"Cod": v_p, "Nom": nom_prod, "Cant": v_ca, "Sub": v_precio_final*v_ca, "PrecioU": v_precio_final})
    
    if 'car' in st.session_state and st.session_state.car:
        st.table(pd.DataFrame(st.session_state.car)[["Cant", "Nom", "PrecioU", "Sub"]])
        tv = sum(i['Sub'] for i in st.session_state.car)
        st.markdown(f"<p class='total-gigante'>${tv:,.2f}</p>", unsafe_allow_html=True)
        if st.button("🚀 REGISTRAR VENTA FINAL"):
            nid = int(df_v['ID'].max() + 1 if not df_v.empty else 1)
            det = ", ".join([f"{i['Cant']} {i['Nom']} (${i['PrecioU']})" for i in st.session_state.car])
            nv = pd.DataFrame([{"ID": nid, "Fecha": datetime.now(ZONA_HORARIA).strftime("%d/%m/%Y %H:%M:%S"), "Vend": v_v, "Cli": v_c, "Tel": v_t, "Prod": det, "Monto": tv, "Est": "Pendiente"}])
            pd.concat([df_v, nv]).to_csv(db_v, index=False); st.session_state.car = []; st.rerun()

with tab_p: # CONTROL DE PEDIDOS (FECHA + HORA)
    pedidos_ordenados = df_v.sort_values(by=['ID'], ascending=False).head(20)
    for idx, row in pedidos_ordenados.iterrows():
        color_ico = "🟢" if "Entregado" in row['Est'] else "🟠"
        if "Siniestro" in row['Est']: color_ico = "🔴"
        
        # Formateo de Fecha y Hora para el Badge
        try:
            dt_obj = pd.to_datetime(row['Fecha'], dayfirst=True)
            f_format = dt_obj.strftime('%d/%b | %H:%M')
        except:
            f_format = row['Fecha']

        st.markdown(f"""
            <div class='card-pedido'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                    <div style='flex-grow: 1; margin-right: 15px;'>
                        <b>{color_ico} #{row['ID']} | {row['Vend']}</b> | {row['Cli']}
                    </div>
                    <div class='time-badge-fixed'>🕒 {f_format}</div>
                </div>
                <div style='font-size: 15px;'>Total: <span style='color:#f1c40f; font-weight:bold;'>${row['Monto']:,.2f}</span></div>
                <div style='margin-top:5px; color:#888; font-size:12px;'>📦 {row['Prod']} ({row['Est']})</div>
            </div>
        """, unsafe_allow_html=True)
        
        if row['Est'] == "Pendiente":
            c_ok, c_gar, c_monto = st.columns([1, 1, 1])
            if c_ok.button("✅ ENTREGAR", key=f"btn_ok_{row['ID']}"):
                df_v.at[idx, 'Est'] = "Entregado"; df_v.to_csv(db_v, index=False); st.rerun()

with tab_d: # 📊 DASHBOARD
    st.markdown("### 👑 ESTRATEGIA MCCOFFEE")
    # Pulso Live con Fecha
    for _, l in df_v.sort_values(by='ID', ascending=False).head(5).iterrows():
        try:
            h_f = pd.to_datetime(l['Fecha'], dayfirst=True).strftime('%d/%b %H:%M')
        except:
            h_f = l['Fecha']
        st.markdown(f"<div class='feed-item'><b>{h_f}</b> | <b>{l['Vend']}</b> vendió ${l['Monto']:,.0f}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    cg1, cg2 = st.columns([2, 1])
    with cg1:
        st.write("📈 RENDIMIENTO POR HORA")
        if not df_v.empty:
            df_v['H'] = df_v['Fecha_DT'].dt.hour
            v_h = df_v.groupby('H')['Monto'].sum().reset_index()
            fig = go.Figure(go.Scatter(x=v_h['H'], y=v_h['Monto'], mode='lines+markers', line=dict(color='#f1c40f', width=4), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.1)'))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig, use_container_width=True)

with tab_j: # PANEL JEFE
    pw = st.text_input("Contraseña", type="password")
    if pw == CLAVE_MAESTRA:
        st.subheader("🕵️ MONITOR DE AUDITORÍA")
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        # (Lógica de inventario, boveda, resurtir... se mantiene igual abajo)
