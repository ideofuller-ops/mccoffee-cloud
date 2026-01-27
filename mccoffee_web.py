import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="MCCOFFEE", layout="wide")

# --- 1. ARCHIVOS Y SEGURIDAD ---
CLAVE_MAESTRA = "admin123" 
db_v, db_p, db_s, db_m = "base_ventas.csv", "base_productos.csv", "base_stock.csv", "meta.txt"

def preparar():
    if not os.path.exists(db_v): pd.DataFrame(columns=["ID","Fecha","Vend","Cli","Tel","Prod","Monto","Est"]).to_csv(db_v, index=False)
    if not os.path.exists(db_p): pd.DataFrame(columns=["Cod","Nom","Pre","Uni"]).to_csv(db_p, index=False)
    if not os.path.exists(db_s): pd.DataFrame(columns=["Cod","Cant"]).to_csv(db_s, index=False)
    if not os.path.exists(db_m):
        with open(db_m, "w") as f: f.write("5000")

preparar()

def cargar():
    v = pd.read_csv(db_v)
    v['Fecha_DT'] = pd.to_datetime(v['Fecha'], format="%d/%m/%Y %H:%M", errors='coerce')
    try:
        with open(db_m, "r") as f: m = float(f.read())
    except: m = 5000.0
    return v, pd.read_csv(db_p), pd.read_csv(db_s), m

df_v, df_p, df_s, meta_diaria = cargar()

# --- 🎨 ESTILO FINAL ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; color: white; }}
    .titulo-mccoffee {{
        text-align: center; color: #d4af37; font-family: 'Impact', sans-serif; 
        font-size: 38px !important; white-space: nowrap; letter-spacing: 1px;
    }}
    .total-gigante {{ color: #d4af37; font-size: 70px !important; font-weight: bold; text-align: center; margin: -20px 0; }}
    .stMetricValue {{ color: #d4af37 !important; font-weight: bold !important; }}
    .stButton>button {{ border-radius: 0px; border: 1px solid #d4af37; background: #000; color: #d4af37; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mccoffee'>MCCOFFEE</h1>", unsafe_allow_html=True)
    st.markdown("---")
    hoy = datetime.now().date()
    hace_7 = datetime.now() - timedelta(days=7)
    hace_30 = datetime.now() - timedelta(days=30)
    v_hoy = df_v[df_v['Fecha_DT'].dt.date == hoy]['Monto'].sum()
    v_semana = df_v[df_v['Fecha_DT'] >= hace_7]['Monto'].sum()
    v_mes = df_v[df_v['Fecha_DT'] >= hace_30]['Monto'].sum()
    
    st.metric("CORTE DE HOY", f"${v_hoy:,.2f}")
    st.progress(min(v_hoy / meta_diaria, 1.0))
    st.caption(f"Meta Diaria: ${meta_diaria:,.0f}")
    
    st.markdown("---")
    st.write(f"📅 Esta Semana: *${v_semana:,.2f}*")
    st.write(f"📊 Este Mes: *${v_mes:,.2f}*")
    st.markdown("---")
    st.subheader("📦 STOCK")
    for _, s in df_s.iterrows():
        st.markdown(f"<p style='color: #d4af37; font-weight: bold; margin:0;'>{s['Cod']}: {s['Cant']}</p>", unsafe_allow_html=True)

# --- 3. PESTAÑAS ---
tab_v, tab_p, tab_j = st.tabs(["🚀 VENTAS", "📋 PEDIDOS", "🔐 PANEL JEFE"])

with tab_v:
    c1, c2, c3 = st.columns(3)
    v_vend = c1.text_input("Vendedor").upper()
    v_cli = c2.text_input("Cliente").upper()
    v_tel = c3.text_input("WhatsApp")
    c4, c5, c6 = st.columns([2, 1, 1])
    lista_p = df_p['Cod'].tolist() if not df_p.empty else ["SIN PRODUCTOS"]
    v_prod = c4.selectbox("Producto", lista_p)
    v_cant = c5.number_input("Cant.", min_value=1)
    if c6.button("➕ AÑADIR"):
        if 'c' not in st.session_state: st.session_state.c = []
        if v_prod != "SIN PRODUCTOS":
            p = df_p[df_p['Cod'] == v_prod].iloc[0]
            st.session_state.c.append({"Cod": v_prod, "Nom": p['Nom'], "Cant": v_cant, "Sub": p['Pre']*v_cant})

    if 'c' in st.session_state and st.session_state.c:
        st.table(pd.DataFrame(st.session_state.c)[["Cant", "Nom", "Sub"]])
        v_env = st.number_input("Envío $", min_value=0.0)
        t_v = sum(i['Sub'] for i in st.session_state.c) + v_env
        st.markdown(f"<p class='total-gigante'>${t_v:,.2f}</p>", unsafe_allow_html=True)
        if st.button("🚀 REGISTRAR VENTA FINAL"):
            nid = int(df_v['ID'].max() + 1 if not df_v.empty else 1)
            det = ", ".join([f"{i['Cant']} {i['Nom']}" for i in st.session_state.c])
            nueva = pd.DataFrame([{"ID": nid, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Vend": v_vend, "Cli": v_cli, "Tel": v_tel, "Prod": det, "Monto": t_v, "Est": "Pendiente"}])
            for i in st.session_state.c: df_s.loc[df_s['Cod'] == i['Cod'], 'Cant'] -= i['Cant']
            pd.concat([df_v, nueva]).to_csv(db_v, index=False)
            df_s.to_csv(db_s, index=False)
            st.session_state.c = []
            st.rerun()

with tab_p:
    for idx, row in df_v.iloc[::-1].head(20).iterrows():
        ca, cb = st.columns([4, 1])
        icono = "🟠" if row['Est'] == "Pendiente" else "🟢"
        ca.write(f"{icono} *#{row['ID']}* | *{row['Vend']}* | {row['Cli']}: {row['Prod']} (${row['Monto']})")
        if cb.button("Cambiar", key=f"s_{row['ID']}"):
            df_v.at[idx, 'Est'] = "Entregado" if row['Est'] == "Pendiente" else "Pendiente"
            df_v.to_csv(db_v, index=False)
            st.rerun()

with tab_j:
    st.subheader("🔐 Panel Administrativo")
    pw = st.text_input("Contraseña", type="password")
    if pw == CLAVE_MAESTRA:
        # BOTONES DE DESCARGA (AQUÍ ESTÁN)
        st.info("📊 REPORTES Y AUDITORÍA")
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.download_button("📥 Descargar Ventas (Excel)", df_v.to_csv(index=False), "ventas_mccoffee.csv", "text/csv")
        with col_ex2:
            st.download_button("📥 Descargar Stock (Excel)", df_s.to_csv(index=False), "stock_mccoffee.csv", "text/csv")
        
        st.markdown("---")
        with st.expander("📦 GESTIÓN DE INVENTARIO"):
            f1, f2, f3 = st.columns(3)
            fc, fn, fp = f1.text_input("Clave").upper(), f2.text_input("Nombre"), f3.number_input("Precio", min_value=0.0)
            fu, fs = st.text_input("Unidad"), st.number_input("Stock Inicial", min_value=0)
            if st.button("💾 GUARDAR"):
                np = pd.DataFrame([{"Cod": fc, "Nom": fn, "Pre": fp, "Uni": fu}])
                ns = pd.DataFrame([{"Cod": fc, "Cant": fs}])
                pd.concat([df_p, np]).drop_duplicates('Cod', keep='last').to_csv(db_p, index=False)
                pd.concat([df_s, ns]).drop_duplicates('Cod', keep='last').to_csv(db_s, index=False)
                st.rerun()

        st.markdown("---")
        st.error("🚨 REINICIO")
        col_r1, col_r2 = st.columns(2)
        if col_r1.button("🗑️ LIMPIAR VENTAS"):
            pd.DataFrame(columns=["ID","Fecha","Vend","Cli","Tel","Prod","Monto","Est"]).to_csv(db_v, index=False)
            st.rerun()
        if col_r2.button("🔥 REINICIO TOTAL"):
            for f in [db_v, db_p, db_s]:
                if os.path.exists(f): os.remove(f)
            st.rerun()
