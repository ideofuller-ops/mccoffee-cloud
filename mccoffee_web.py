import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y BASES DE DATOS ---
st.set_page_config(page_title="MCCOFFEE", layout="wide")
CLAVE_MAESTRA = "admin123"

# Archivos necesarios
db_v = "base_ventas.csv"     # Ventas totales
db_p = "base_productos.csv"  # Catálogo (L1, Americano, etc.)
db_s = "base_stock.csv"      # Bóveda Central
db_a = "base_auditoria.csv"  # Inventario por Vendedor
db_st = "base_staff.csv"     # Lista de Vendedores
db_m = "meta.txt"            # Meta diaria

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

# --- CARGA DE DATOS ---
df_v = pd.read_csv(db_v)
df_v['Fecha_DT'] = pd.to_datetime(df_v['Fecha'], format="%d/%m/%Y %H:%M", errors='coerce')
df_p = pd.read_csv(db_p)
df_s = pd.read_csv(db_s)
df_a = pd.read_csv(db_a)
df_st = pd.read_csv(db_st)
with open(db_m, "r") as f: meta_diaria = float(f.read())

# --- 🎨 ESTILO MCCOFFEE (NOMBRE CORRIDO) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; color: white; }}
    .titulo-mccoffee {{
        text-align: center; color: #d4af37; font-family: 'Impact', sans-serif; 
        font-size: 38px !important; white-space: nowrap; letter-spacing: 1px;
    }}
    .total-gigante {{ color: #d4af37; font-size: 70px !important; font-weight: bold; text-align: center; }}
    .stMetricValue {{ color: #d4af37 !important; font-weight: bold !important; }}
    .stButton>button {{ border-radius: 0px; border: 1px solid #d4af37; background: #000; color: #d4af37; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. BARRA LATERAL (REPORTES) ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mccoffee'>MCCOFFEE</h1>", unsafe_allow_html=True)
    st.markdown("---")
    hoy = datetime.now().date()
    hace_7 = datetime.now() - timedelta(days=7)
    hace_30 = datetime.now() - timedelta(days=30)
    
    v_hoy = df_v[df_v['Fecha_DT'].dt.date == hoy]['Monto'].sum()
    v_sem = df_v[df_v['Fecha_DT'] >= hace_7]['Monto'].sum()
    v_mes = df_v[df_v['Fecha_DT'] >= hace_30]['Monto'].sum()
    
    st.metric("CORTE DE HOY", f"${v_hoy:,.2f}")
    st.progress(min(v_hoy / meta_diaria, 1.0))
    st.write(f"📅 Semana: *${v_sem:,.2f}*")
    st.write(f"📊 Mes: *${v_mes:,.2f}*")
    
    st.markdown("---")
    st.subheader("📦 BÓVEDA CENTRAL")
    for _, s in df_s.iterrows():
        st.markdown(f"<p style='color: #d4af37; font-weight: bold; margin:0;'>{s['Cod']}: {s['Cant']}</p>", unsafe_allow_html=True)

# --- 3. PESTAÑAS ---
tab_v, tab_p, tab_j = st.tabs(["🚀 VENTAS", "📋 PEDIDOS", "🔐 PANEL JEFE"])

with tab_v:
    c1, c2, c3 = st.columns(3)
    lista_vendedores = df_st['Nombre'].tolist() if not df_st.empty else ["CONFIGURAR STAFF"]
    v_vend = c1.selectbox("Vendedor", lista_vendedores)
    v_cli = c2.text_input("Cliente").upper()
    v_tel = c3.text_input("WhatsApp")
    
    c4, c5, c6 = st.columns([2, 1, 1])
    v_prod = c4.selectbox("Producto (Clave)", df_p['Cod'].tolist() if not df_p.empty else ["N/A"])
    v_cant = c5.number_input("Cant.", min_value=1)
    
    if c6.button("➕ AÑADIR"):
        if 'car' not in st.session_state: st.session_state.car = []
        p_info = df_p[df_p['Cod'] == v_prod].iloc[0]
        st.session_state.car.append({"Cod": v_prod, "Nom": p_info['Nom'], "Cant": v_cant, "Sub": p_info['Pre']*v_cant})

    if 'car' in st.session_state and st.session_state.car:
        st.table(pd.DataFrame(st.session_state.car)[["Cant", "Nom", "Sub"]])
        if st.button("🚀 REGISTRAR VENTA FINAL"):
            nid = int(df_v['ID'].max() + 1 if not df_v.empty else 1)
            det = ", ".join([f"{i['Cant']} {i['Nom']}" for i in st.session_state.car])
            total = sum(i['Sub'] for i in st.session_state.car)
            
            nueva = pd.DataFrame([{"ID": nid, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Vend": v_vend, "Cli": v_cli, "Tel": v_tel, "Prod": det, "Monto": total, "Est": "Pendiente"}])
            
            # Descontar de la Mochila del Vendedor
            for i in st.session_state.car:
                mask = (df_a['Vendedor'] == v_vend) & (df_a['Cod'] == i['Cod'])
                if mask.any():
                    df_a.loc[mask, 'Vendido'] += i['Cant']
                    df_a.loc[mask, 'Actual'] -= i['Cant']
            
            pd.concat([df_v, nueva]).to_csv(db_v, index=False)
            df_a.to_csv(db_a, index=False)
            st.session_state.car = []
            st.rerun()

with tab_p:
    st.subheader("📋 Control de Pedidos y Deudas")
    for idx, row in df_v.iloc[::-1].head(10).iterrows():
        ca, cb = st.columns([4, 1])
        ico = "🟠" if row['Est'] == "Pendiente" else "🟢"
        ca.write(f"{ico} *#{row['ID']}* | *{row['Vend']}* | {row['Cli']}: {row['Prod']}")
        if cb.button("Ok", key=f"btn_{row['ID']}"):
            df_v.at[idx, 'Est'] = "Entregado"
            df_v.to_csv(db_v, index=False)
            st.rerun()

with tab_j:
    pw = st.text_input("Contraseña", type="password")
    if pw == CLAVE_MAESTRA:
        st.subheader("🕵️ MONITOR DE AUDITORÍA (LO QUE DEBEN)")
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        
        with st.expander("🚚 RE-SURTIR / CARGA POR CIUDAD"):
            c_v = st.selectbox("Vendedor a Surtir", lista_vendedores)
            c_p = st.selectbox("Producto", df_p['Cod'].tolist())
            c_n = st.number_input("Cantidad nueva entregada", min_value=0.1)
            c_ciu = st.text_input("Ciudad de Entrega (Opcional)", "CDMX")
            
            if st.button("CONFIRMAR CARGA ACUMULATIVA"):
                # 1. Restar de Bóveda
                df_s.loc[df_s['Cod'] == c_p, 'Cant'] -= c_n
                # 2. Sumar a Vendedor
                mask = (df_a['Vendedor'] == c_v) & (df_a['Cod'] == c_p)
                if mask.any():
                    df_a.loc[mask, 'Entregado'] += c_n
                    df_a.loc[mask, 'Actual'] += c_n
                else:
                    df_a = pd.concat([df_a, pd.DataFrame([{"Vendedor": c_v, "Cod": c_p, "Entregado": c_n, "Vendido": 0, "Actual": c_n}])])
                
                df_s.to_csv(db_s, index=False)
                df_a.to_csv(db_a, index=False)
                st.success(f"Cargado {c_n} a {c_v} en {c_ciu}")
                st.rerun()

        with st.expander("👥 GESTIÓN DE STAFF Y PRODUCTOS"):
            n_v = st.text_input("Nuevo Vendedor").upper()
            if st.button("Registrar Vendedor"):
                pd.concat([df_st, pd.DataFrame([{"Nombre": n_v}])]).drop_duplicates().to_csv(db_st, index=False)
                st.rerun()
            st.markdown("---")
            f1, f2, f3 = st.columns(3)
            pc, pn, pp = f1.text_input("Cód"), f2.text_input("Nom"), f3.number_input("$", min_value=0.0)
            if st.button("Guardar Producto"):
                pd.concat([df_p, pd.DataFrame([{"Cod": pc, "Nom": pn, "Pre": pp, "Uni": "Uni"}])]).to_csv(db_p, index=False)
                pd.concat([df_s, pd.DataFrame([{"Cod": pc, "Cant": 0}])]).to_csv(db_s, index=False)
                st.rerun()

        st.info("📊 AUDITORÍA")
        st.download_button("📥 Excel Ventas", df_v.to_csv(index=False), "ventas.csv")
        st.download_button("📥 Excel Auditoría Mochila", df_a.to_csv(index=False), "auditoria.csv")
