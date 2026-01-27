import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y BASES DE DATOS ---
st.set_page_config(page_title="MCCOFFEE", layout="wide")
CLAVE_MAESTRA = "admin123"

# Rutas de archivos
db_v, db_p, db_s, db_a, db_st, db_m = "base_ventas.csv", "base_productos.csv", "base_stock.csv", "base_auditoria.csv", "base_staff.csv", "meta.txt"

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

preparar()

# CARGA DE DATOS
df_v = pd.read_csv(db_v)
df_v['Fecha_DT'] = pd.to_datetime(df_v['Fecha'], format="%d/%m/%Y %H:%M", errors='coerce')
df_p = pd.read_csv(db_p); df_s = pd.read_csv(db_s); df_a = pd.read_csv(db_a); df_st = pd.read_csv(db_st)
with open(db_m, "r") as f: meta_diaria = float(f.read())
meta_semanal = meta_diaria * 6 

# --- 🎨 ESTILO FINAL ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; color: white; }}
    .titulo-mccoffee {{ text-align: center; color: #d4af37; font-family: 'Impact'; font-size: 35px; white-space: nowrap; }}
    .total-gigante {{ color: #d4af37; font-size: 60px !important; font-weight: bold; text-align: center; }}
    .stMetricValue {{ color: #d4af37 !important; }}
    .stButton>button {{ border-radius: 0px; border: 1px solid #d4af37; background: #000; color: #d4af37; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (REPORTES) ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mccoffee'>MCCOFFEE</h1>", unsafe_allow_html=True)
    st.markdown("---")
    hoy = datetime.now().date()
    v_hoy = df_v[df_v['Fecha_DT'].dt.date == hoy]['Monto'].sum()
    v_sem = df_v[df_v['Fecha_DT'] >= (datetime.now() - timedelta(days=7))]['Monto'].sum()
    
    st.metric("CORTE DE HOY", f"${v_hoy:,.2f}")
    st.progress(min(v_hoy / meta_diaria, 1.0))
    
    st.markdown("---")
    st.write("📅 *PROGRESO SEMANAL*")
    st.metric("VENTA SEMANA", f"${v_sem:,.2f}")
    # Barra verde para la semana
    st.markdown(f"""<style>div.stProgress > div > div > div > div {{ background-color: #28a745 !important; }}</style>""", unsafe_allow_html=True)
    st.progress(min(v_sem / meta_semanal, 1.0))
    st.caption(f"Meta Semanal: ${meta_semanal:,.0f}")
    
    st.markdown("---")
    st.subheader("📦 BÓVEDA CENTRAL")
    for _, s in df_s.iterrows():
        p_u = df_p[df_p['Cod'] == s['Cod']]['Uni'].values[0] if not df_p[df_p['Cod'] == s['Cod']].empty else ""
        st.markdown(f"<p style='color: #d4af37; font-weight: bold; margin:0;'>{s['Cod']}: {s['Cant']} {p_u}</p>", unsafe_allow_html=True)

# --- 3. PESTAÑAS ---
tab_v, tab_p, tab_j = st.tabs(["🚀 VENTAS", "📋 PEDIDOS", "🔐 PANEL JEFE"])

with tab_v: # REGISTRO DE VENTAS
    c1, c2, c3 = st.columns(3); l_st = df_st['Nombre'].tolist() if not df_st.empty else ["CONFIGURAR STAFF"]
    v_v = c1.selectbox("Vendedor", l_st, key="v_sel_1")
    v_c = c2.text_input("Cliente").upper(); v_t = c3.text_input("WhatsApp")
    c4, c5, c6 = st.columns([2, 1, 1]); v_p = c4.selectbox("Producto", df_p['Cod'].tolist() if not df_p.empty else ["N/A"], key="v_sel_2"); v_ca = c5.number_input("Cant.", min_value=1, key="v_num_1")
    
    if c6.button("➕ AÑADIR"):
        if 'car' not in st.session_state: st.session_state.car = []
        pi = df_p[df_p['Cod'] == v_p].iloc[0]; st.session_state.car.append({"Cod": v_p, "Nom": pi['Nom'], "Cant": v_ca, "Sub": pi['Pre']*v_ca})
    
    if 'car' in st.session_state and st.session_state.car:
        st.table(pd.DataFrame(st.session_state.car)[["Cant", "Nom", "Sub"]])
        tv = sum(i['Sub'] for i in st.session_state.car)
        st.markdown(f"<p class='total-gigante'>${tv:,.2f}</p>", unsafe_allow_html=True)
        if st.button("🚀 REGISTRAR VENTA FINAL"):
            nid = int(df_v['ID'].max() + 1 if not df_v.empty else 1); det = ", ".join([f"{i['Cant']} {i['Nom']}" for i in st.session_state.car])
            nv = pd.DataFrame([{"ID": nid, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Vend": v_v, "Cli": v_c, "Tel": v_t, "Prod": det, "Monto": tv, "Est": "Pendiente"}])
            for i in st.session_state.car:
                mk = (df_a['Vendedor'] == v_v) & (df_a['Cod'] == i['Cod'])
                if mk.any(): df_a.loc[mk, 'Vendido'] += i['Cant']; df_a.loc[mk, 'Actual'] -= i['Cant']
            pd.concat([df_v, nv]).to_csv(db_v, index=False); df_a.to_csv(db_a, index=False); st.session_state.car = []; st.rerun()

with tab_p: # CONTROL DE PEDIDOS
    for idx, row in df_v.iloc[::-1].head(15).iterrows():
        ca, cb = st.columns([4, 1]); ico = "🟠" if row['Est'] == "Pendiente" else "🟢"
        ca.write(f"{ico} *#{row['ID']}* | *{row['Vend']}* | {row['Cli']}: {row['Prod']}")
        label_btn = "Ok (Entregar)" if row['Est'] == "Pendiente" else "Regresar"
        if cb.button(label_btn, key=f"btn_p_{row['ID']}"):
            df_v.at[idx, 'Est'] = "Entregado" if row['Est'] == "Pendiente" else "Pendiente"; df_v.to_csv(db_v, index=False); st.rerun()

with tab_j: # PANEL JEFE
    pw = st.text_input("Contraseña", type="password")
    if pw == CLAVE_MAESTRA:
        st.subheader("🕵️ MONITOR DE AUDITORÍA (MOCHILAS)")
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        
        col_j1, col_j2 = st.columns(2)
        with col_j1: # ENTRADA A BÓVEDA
            with st.expander("📥 SURTIR BÓVEDA CENTRAL"):
                b_p = st.selectbox("Producto Proveedor", df_p['Cod'].tolist() if not df_p.empty else ["N/A"], key="j_sel_3")
                b_n = st.number_input("Cantidad Entrada", min_value=0.1, key="j_num_2")
                if st.button("SUMAR A BÓVEDA"):
                    df_s.loc[df_s['Cod'] == b_p, 'Cant'] += b_n
                    df_s.to_csv(db_s, index=False); st.success(f"+{b_n} en Bóveda"); st.rerun()
        
        with col_j2: # SALIDA A VENDEDOR
            with st.expander("🚚 RE-SURTIR / CARGA POR CIUDAD"):
                cv = st.selectbox("Elegir Vendedor", l_st, key="j_sel_4"); cp = st.selectbox("Producto a Surtir", df_p['Cod'].tolist() if not df_p.empty else ["N/A"], key="j_sel_5")
                cn = st.number_input("Cantidad a entregar", min_value=0.1, key="j_num_3"); ciu = st.text_input("Ciudad de Entrega", "CDMX")
                if st.button("CONFIRMAR CARGA ACUMULATIVA"):
                    df_s.loc[df_s['Cod'] == cp, 'Cant'] -= cn
                    mk = (df_a['Vendedor'] == cv) & (df_a['Cod'] == cp)
                    if mk.any(): df_a.loc[mk, 'Entregado'] += cn; df_a.loc[mk, 'Actual'] += cn
                    else: df_a = pd.concat([df_a, pd.DataFrame([{"Vendedor": cv, "Cod": cp, "Entregado": cn, "Vendido": 0, "Actual": cn}])])
                    df_s.to_csv(db_s, index=False); df_a.to_csv(db_a, index=False); st.rerun()

        with st.expander("👥 GESTIÓN DE STAFF Y CATÁLOGO"):
            c_s1, c_s2 = st.columns(2); n_v = c_s1.text_input("Nuevo Vendedor", key="j_txt_1")
            if c_s2.button("Registrar Vendedor", key="j_btn_1"):
                pd.concat([df_st, pd.DataFrame([{"Nombre": n_v.upper()}])]).drop_duplicates().to_csv(db_st, index=False); st.rerun()
            st.markdown("---")
            f1, f2, f3, f4 = st.columns(4)
            pc, pn, pp, pu = f1.text_input("Clave", key="p_1"), f2.text_input("Nombre", key="p_2"), f3.number_input("$", key="p_3"), f4.selectbox("Uni", ["KG", "PZA"], key="p_4")
            if st.button("Guardar Producto Nuevo", key="p_btn_1"):
                if pc:
                    pd.concat([df_p, pd.DataFrame([{"Cod": pc.upper(), "Nom": pn, "Pre": pp, "Uni": pu}])]).to_csv(db_p, index=False)
                    pd.concat([df_s, pd.DataFrame([{"Cod": pc.upper(), "Cant": 0}])]).to_csv(db_s, index=False); st.rerun()

        st.info("📊 EXPORTAR REPORTES"); c_ex1, c_ex2, c_ex3 = st.columns(3)
        c_ex1.download_button("📥 Ventas", df_v.to_csv(index=False), "ventas.csv", key="d_1")
        c_ex2.download_button("📥 Mochilas", df_a.to_csv(index=False), "mochilas.csv", key="d_2")
        c_ex3.download_button("📥 Bóveda", df_s.to_csv(index=False), "boveda.csv", key="d_3")
        
        st.error("🚨 REINICIO"); r1, r2 = st.columns(2)
        if r1.button("LIMPIAR VENTAS", key="r_1"): pd.DataFrame(columns=["ID","Fecha","Vend","Cli","Tel","Prod","Monto","Est"]).to_csv(db_v, index=False); st.rerun()
        if r2.button("BORRAR TODO", key="r_2"): [os.remove(f) for f in [db_v, db_p, db_s, db_a, db_st] if os.path.exists(f)]; st.rerun()
