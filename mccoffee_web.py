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
# Formato con segundos para precisión total
df_v['Fecha_DT'] = pd.to_datetime(df_v['Fecha'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
df_p = pd.read_csv(db_p); df_s = pd.read_csv(db_s); df_a = pd.read_csv(db_a); df_st = pd.read_csv(db_st)

with open(db_m, "r") as f: meta_diaria = float(f.read())
with open(db_mw, "r") as f: meta_semanal = float(f.read())

# --- 🎨 ESTILO "DIAMANTE NEGRO & ORO NEÓN" ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    .stApp {{ 
        background: radial-gradient(circle at 10% 10%, #1a1a1a 0%, #050505 100%);
        color: white; 
    }}

    /* Título con Glow Neon */
    .titulo-mccoffee {{ 
        text-align: center; color: #d4af37; font-family: 'Impact'; font-size: 45px;
        text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.6); margin-bottom: 10px;
    }}

    /* Reloj Digital Premium */
    .live-clock {{
        font-family: 'Orbitron', sans-serif; color: #f1c40f; text-align: center;
        font-size: 1.2rem; text-shadow: 0px 0px 10px rgba(241, 196, 15, 0.5);
        background: rgba(0,0,0,0.3); border-radius: 10px; padding: 5px; margin-bottom: 20px;
    }}

    /* Pestañas de Oro Metálico */
    .stTabs [data-baseweb="tab-list"] {{ gap: 12px; }}
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255, 255, 255, 0.03); border-radius: 10px 10px 0 0;
        color: #888; padding: 12px 25px; border: 1px solid rgba(212, 175, 55, 0.1);
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(180deg, #f1c40f, #d4af37) !important;
        color: black !important; font-weight: bold;
        box-shadow: inset 0px 0px 15px rgba(255, 255, 255, 0.6) !important;
    }}

    /* Botones con Glow */
    .stButton>button {{ 
        border: 2px solid #f1c40f; border-radius: 8px; 
        background: linear-gradient(145deg, #1a1a1a, #000); color: #f1c40f;
        font-weight: 800; transition: 0.4s; width: 100%;
    }}
    .stButton>button:hover {{ 
        background: #f1c40f; color: #000; box-shadow: 0px 0px 20px rgba(241, 196, 15, 0.8);
    }}

    /* Tarjetas de Pedido con Badge Temporal */
    .card-pedido {{
        background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 15px; padding: 20px; margin-bottom: 15px; position: relative;
    }}
    .time-badge {{
        position: absolute; top: 10px; right: 10px; background: rgba(212, 175, 55, 0.15);
        color: #f1c40f; padding: 4px 10px; border-radius: 5px; font-size: 12px;
        font-family: 'Orbitron', sans-serif; border: 1px solid #d4af37;
    }}

    /* Pulso Live Feed */
    @keyframes pulse-gold {{
        0% {{ box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(212, 175, 55, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }}
    }}
    .feed-item {{
        padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px;
        margin-bottom: 8px; border-left: 4px solid #f1c40f; animation: pulse-gold 2s infinite;
        font-size: 14px;
    }}

    /* Gráficas Mamalonas */
    .dashboard-card {{
        background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px; padding: 20px; margin-bottom: 20px;
    }}

    .ranking-row {{ 
        background: rgba(212, 175, 55, 0.07); padding: 10px; border-radius: 8px; 
        margin-bottom: 8px; border-left: 4px solid #d4af37; 
    }}
    
    .total-gigante {{ color: #d4af37; font-size: 60px !important; font-weight: bold; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (CONTROL Y RANKING) ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mccoffee'>CONTROL TOTAL<br>MCCOFFEE</h1>", unsafe_allow_html=True)
    
    # Reloj Live CDMX
    hora_actual = datetime.now(ZONA_HORARIA)
    st.markdown(f"<div class='live-clock'>🕒 {hora_actual.strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    hoy = hora_actual.date()
    df_hoy = df_v[df_v['Fecha_DT'].dt.date == hoy]
    v_hoy = df_hoy['Monto'].sum()
    v_sem = df_v[df_v['Fecha_DT'] >= (datetime.now() - timedelta(days=7))]['Monto'].sum()
    
    st.metric("CORTE DE HOY", f"${v_hoy:,.2f}")
    st.progress(min(v_hoy / meta_diaria, 1.0))
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
    st.progress(min(v_sem / meta_semanal, 1.0))
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
            # Registro con segundos para precisión total
            nv = pd.DataFrame([{"ID": nid, "Fecha": datetime.now(ZONA_HORARIA).strftime("%d/%m/%Y %H:%M:%S"), "Vend": v_v, "Cli": v_c, "Tel": v_t, "Prod": det, "Monto": tv, "Est": "Pendiente"}])
            for i in st.session_state.car:
                mk = (df_a['Vendedor'] == v_v) & (df_a['Cod'] == i['Cod'])
                if mk.any(): df_a.loc[mk, 'Vendido'] += i['Cant']; df_a.loc[mk, 'Actual'] -= i['Cant']
                else: df_a = pd.concat([df_a, pd.DataFrame([{"Vendedor": v_v, "Cod": i['Cod'], "Entregado": 0, "Vendido": i['Cant'], "Actual": -i['Cant']}])])
            pd.concat([df_v, nv]).to_csv(db_v, index=False); df_a.to_csv(db_a, index=False); st.session_state.car = []; st.rerun()

with tab_p: # CONTROL DE PEDIDOS CON TIMESTAMP BADGE
    pedidos_ordenados = df_v.sort_values(by=['ID'], ascending=False).head(20)
    for idx, row in pedidos_ordenados.iterrows():
        color_ico = "🟢" if "Entregado" in row['Est'] else "🟠"
        if "Siniestro" in row['Est']: color_ico = "🔴"
        
        st.markdown(f"""
            <div class='card-pedido'>
                <div class='time-badge'>🕒 {row['Fecha'].split(' ')[1]}</div>
                <b>{color_ico} #{row['ID']} | {row['Vend']}</b><br>
                <small>Cliente: {row['Cli']} | WhatsApp: {row['Tel']}</small><br>
                <div style='color: #f1c40f; margin-top:10px;'>Total: <b>${row['Monto']:,.2f}</b></div>
                <caption style='font-size:11px;'>📦 {row['Prod']}</caption>
            </div>
            """, unsafe_allow_html=True)
        
        if row['Est'] == "Pendiente":
            c_ok, c_gar, c_monto = st.columns([1, 1, 1])
            if c_ok.button("✅ ENTREGAR", key=f"btn_ok_{row['ID']}"):
                df_v.at[idx, 'Est'] = "Entregado"; df_v.to_csv(db_v, index=False); st.rerun()
            costo_reenvio = c_monto.number_input(f"Costo Reenvío $", min_value=0.0, value=0.0, step=10.0, key=f"num_gar_{row['ID']}")
            if c_gar.button("🔄 GARANTÍA", key=f"btn_gar_{row['ID']}"):
                df_v.at[idx, 'Est'] = "Entregado (Siniestro)"
                nid_new = int(df_v['ID'].max() + 1)
                nv_gar = pd.DataFrame([{"ID": nid_new, "Fecha": datetime.now(ZONA_HORARIA).strftime("%d/%m/%Y %H:%M:%S"), "Vend": row['Vend'], "Cli": row['Cli'] + " (REPO)", "Tel": row['Tel'], "Prod": f"[GARANTÍA] {row['Prod']}", "Monto": costo_reenvio, "Est": "Pendiente"}])
                df_v = pd.concat([df_v, nv_gar]); df_v.to_csv(db_v, index=False); st.rerun()

with tab_d: # 📊 DASHBOARD MAMA-LÓN
    st.markdown("### 👑 ESTRATEGIA MCCOFFEE")
    
    # 1. Indicadores Rapidos
    c_d1, c_d2, c_d3 = st.columns(3)
    t_avg = df_v['Monto'].mean() if not df_v.empty else 0
    c_d1.metric("TICKET PROMEDIO", f"${t_avg:,.2f}")
    c_d2.metric("TOTAL PEDIDOS", len(df_v))
    c_d3.metric("GARANTÍAS (SINIESTROS)", len(df_v[df_v['Est'].str.contains("Siniestro")]))

    # 2. El Pulso McCoffee (Live Feed)
    st.markdown("#### 🔥 PULSO MCCOFFEE")
    ultimos = df_v.sort_values(by='ID', ascending=False).head(5)
    for _, l in ultimos.iterrows():
        st.markdown(f"<div class='feed-item'><b>{l['Fecha'].split(' ')[1]}</b> | <b>{l['Vend']}</b> cerró venta de ${l['Monto']:,.0f} a {l['Cli']}</div>", unsafe_allow_html=True)

    # 3. Gráficas de Oro Neón
    st.markdown("---")
    col_g1, col_g2 = st.columns([2, 1])

    with col_g1: # Gráfica de Líneas Glow
        st.write("📈 RENDIMIENTO POR HORA")
        if not df_v.empty:
            df_v['Hora'] = df_v['Fecha_DT'].dt.hour
            ventas_hora = df_v.groupby('Hora')['Monto'].sum().reset_index()
            
            # Gráfica Neon
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ventas_hora['Hora'], y=ventas_hora['Monto'], mode='lines+markers',
                                     line=dict(color='#f1c40f', width=4),
                                     marker=dict(size=10, color='#fff', line=dict(color='#f1c40f', width=2))))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
            st.plotly_chart(fig, use_container_width=True)
            
            # Mensaje Opción B (Estratega)
            pico_h = ventas_hora.loc[ventas_hora['Monto'].idxmax(), 'Hora']
            st.warning(f"🎯 VENTANA DE IMPACTO DETECTADA: *{pico_h}:00 HRS*. Los datos confirman máxima efectividad de cierre.")

    with col_g2: # Velocímetro de Metas
        st.write("🏎️ VELOCÍMETRO SEMANAL")
        porcentaje_sem = min(v_sem / meta_semanal * 100, 100)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = porcentaje_sem,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Progreso Meta %", 'font': {'color': "#f1c40f", 'size': 18}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#f1c40f"},
                'bgcolor': "rgba(255,255,255,0.05)",
                'borderwidth': 2,
                'bordercolor': "#d4af37",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(255,0,0,0.1)'},
                    {'range': [50, 90], 'color': 'rgba(241,196,15,0.1)'},
                    {'range': [90, 100], 'color': 'rgba(0,255,0,0.1)'}],
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig_gauge, use_container_width=True)

with tab_j: # PANEL JEFE (AUDITORÍA Y RESET)
    pw = st.text_input("Contraseña Maestro", type="password")
    if pw == CLAVE_MAESTRA:
        with st.expander("🎯 CONFIGURAR METAS"):
            c_m1, c_m2 = st.columns(2)
            nm1 = c_m1.number_input("Meta Diaria ($)", min_value=0.0, value=meta_diaria)
            nm2 = c_m2.number_input("Meta Semanal ($)", min_value=0.0, value=meta_semanal)
            if st.button("ACTUALIZAR OBJETIVOS"):
                with open(db_m, "w") as f: f.write(str(nm1))
                with open(db_mw, "w") as f: f.write(str(nm2)); st.rerun()

        st.subheader("🕵️ MONITOR DE AUDITORÍA")
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        
        # Botones de exportación
        ce1, ce2, ce3 = st.columns(3)
        ce1.download_button("📥 Ventas", df_v.to_csv(index=False), "ventas.csv")
        ce2.download_button("📥 Mochilas", df_a.to_csv(index=False), "mochilas.csv")
        ce3.download_button("📥 Bóveda", df_s.to_csv(index=False), "boveda.csv")

        st.error("🚨 ZONA DE REINICIO"); r1, r2 = st.columns(2)
        if r1.button("LIMPIAR VENTAS"): 
            pd.DataFrame(columns=["ID","Fecha","Vend","Cli","Tel","Prod","Monto","Est"]).to_csv(db_v, index=False); st.rerun()
        if r2.button("BORRAR TODO"): 
            [os.remove(f) for f in [db_v, db_p, db_s, db_a, db_st] if os.path.exists(f)]; st.rerun()
