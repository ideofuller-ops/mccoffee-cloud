import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA (PARA QUE SE VEA PRO EN CELULAR) ---
st.set_page_config(page_title="MCCOFFEE Control", layout="wide")

# --- 1. LÓGICA DE AUTO-CREACIÓN (EL CEREBRO DEL VOCHO) ---
db_v, db_p, db_s = "base_ventas.csv", "base_productos.csv", "base_stock.csv"

def preparar_todo_web():
    # Si los archivos no existen en la nube/PC, se crean solitos
    for f, c in [(db_v, ["ID","Fecha","Vend","Cli","Tel","Prod","Monto","Est"]),
                 (db_p, ["Cod","Nom","Pre","Uni"]), (db_s, ["Cod","Cant"])]:
        if not os.path.exists(f):
            pd.DataFrame(columns=c).to_csv(f, index=False)

preparar_todo_web()

# Cargar datos para el uso de la app
def cargar_df():
    return pd.read_csv(db_v), pd.read_csv(db_p), pd.read_csv(db_s)

df_v, df_p, df_s = cargar_df()

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: white; }
    [data-testid="stMetricValue"] { color: #d4af37 !important; font-weight: bold; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BARRA LATERAL (ESTADÍSTICAS RÁPIDAS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/924/924514.png", width=100) # Icono de café
    st.title("MCCOFFEE CLOUD")
    
    # Corte del día
    hoy = datetime.now().strftime("%d/%m/%Y")
    ventas_hoy = df_v[df_v['Fecha'].str.contains(hoy, na=False)]
    total_hoy = ventas_hoy['Monto'].sum()
    st.metric("CORTE DE HOY", f"${total_hoy:,.2f}")
    
    st.markdown("---")
    st.subheader("📦 STOCK")
    if not df_s.empty:
        for _, s in df_s.iterrows():
            p_info = df_p[df_p['Cod'] == s['Cod']]
            uni = p_info.iloc[0]['Uni'] if not p_info.empty else ""
            if s['Cant'] < 0:
                st.error(f"{s['Cod']}: DEBES {abs(s['Cant'])} {uni}")
            elif s['Cant'] <= 5:
                st.warning(f"{s['Cod']}: {s['Cant']} {uni}")
            else:
                st.success(f"{s['Cod']}: {s['Cant']} {uni}")
    else:
        st.info("Sin productos registrados")

# --- 3. PESTAÑAS PRINCIPALES ---
tab_v, tab_p, tab_j = st.tabs(["🚀 VENTAS", "📋 PEDIDOS", "⚙️ PANEL JEFE"])

with tab_v:
    c1, c2, c3 = st.columns(3)
    v_vend = c1.text_input("Vendedor").upper()
    v_cli = c2.text_input("Cliente").upper()
    v_tel = c3.text_input("WhatsApp")

    col_prod, col_cant = st.columns([3, 1])
    # Si no hay productos, mostramos aviso
    lista_prods = df_p['Cod'].tolist() if not df_p.empty else ["REGISTRA PRODS PRIMERO"]
    v_prod = col_prod.selectbox("Producto", lista_prods)
    v_cant = col_cant.number_input("Cant.", min_value=1, step=1)

    if st.button("➕ AGREGAR"):
        if 'tkt' not in st.session_state: st.session_state.tkt = []
        if not df_p.empty and v_prod != "REGISTRA PRODS PRIMERO":
            p_data = df_p[df_p['Cod'] == v_prod].iloc[0]
            st.session_state.tkt.append({"Cod": v_prod, "Nom": p_data['Nom'], "Cant": v_cant, "Sub": p_data['Pre']*v_cant})
    
    if 'tkt' in st.session_state and st.session_state.tkt:
        st.table(pd.DataFrame(st.session_state.tkt))
        v_env = st.number_input("Envío $", min_value=0.0)
        total_venta = sum(i['Sub'] for i in st.session_state.tkt) + v_env
        st.subheader(f"TOTAL: ${total_venta:,.2f}")
        
        if st.button("🚀 REGISTRAR VENTA"):
            nid = df_v['ID'].max() + 1 if not df_v.empty else 1
            res_prod = ", ".join([f"{i['Cant']}{i['Cod']}" for i in st.session_state.tkt])
            nueva_f = pd.DataFrame([{"ID": nid, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                                     "Vend": v_vend, "Cli": v_cli, "Tel": v_tel, "Prod": res_prod, "Monto": total_venta, "Est": "Pendiente"}])
            
            # Descontar stock
            for i in st.session_state.tkt:
                df_s.loc[df_s['Cod'] == i['Cod'], 'Cant'] -= i['Cant']
            
            pd.concat([df_v, nueva_f]).to_csv(db_v, index=False)
            df_s.to_csv(db_s, index=False)
            st.session_state.tkt = []
            st.success("Venta Guardada")
            st.rerun()

with tab_p:
    st.subheader("Pedidos del día")
    # Mostrar últimos 10
    for idx, row in df_v.iloc[::-1].head(10).iterrows():
        ca, cb, cc = st.columns([3, 1, 1])
        color = "🟠" if row['Est'] == "Pendiente" else "🟢"
        ca.write(f"{color} *{row['Cli']}*: {row['Prod']} - ${row['Monto']}")
        cb.write(f"{row['Est']}")
        if cc.button("Cambiar", key=f"sw_{row['ID']}"):
            df_v.at[idx, 'Est'] = "Entregado" if row['Est'] == "Pendiente" else "Pendiente"
            df_v.to_csv(db_v, index=False)
            st.rerun()

with tab_j:
    st.subheader("Configuración del Negocio")
    with st.expander("Registrar Nuevo Producto / Stock"):
        f_cod = st.text_input("Clave (Ej: N1)").upper()
        f_nom = st.text_input("Nombre Real")
        f_pre = st.number_input("Precio Unitario", min_value=0.0)
        f_uni = st.text_input("Unidad (Kg, Pza, L)")
        f_stk = st.number_input("Stock inicial", min_value=0)
        
        if st.button("GUARDAR EN EL SISTEMA"):
            if f_cod and f_nom:
                new_p = pd.DataFrame([{"Cod": f_cod, "Nom": f_nom, "Pre": f_pre, "Uni": f_uni}])
                new_s = pd.DataFrame([{"Cod": f_cod, "Cant": f_stk}])
                # Actualizar y quitar duplicados
                pd.concat([df_p, new_p]).drop_duplicates('Cod', keep='last').to_csv(db_p, index=False)
                pd.concat([df_s, new_s]).drop_duplicates('Cod', keep='last').to_csv(db_s, index=False)
                st.success(f"Producto {f_cod} listo.")
                st.rerun()