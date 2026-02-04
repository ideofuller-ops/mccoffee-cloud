import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y BASES DE DATOS ---
st.set_page_config(page_title="CONTROL TOTAL MCCOFFEE", layout="wide")
CLAVE_MAESTRA = "mccoffee2026"

# Rutas de archivos (Agregamos db_mw para la meta semanal guardada)
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
df_v['Fecha_DT'] = pd.to_datetime(df_v['Fecha'], format="%d/%m/%Y %H:%M", errors='coerce')
df_p = pd.read_csv(db_p); df_s = pd.read_csv(db_s); df_a = pd.read_csv(db_a); df_st = pd.read_csv(db_st)

with open(db_m, "r") as f: meta_diaria = float(f.read())
with open(db_mw, "r") as f: meta_semanal = float(f.read())

# --- 🎨 ESTILO FINAL ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; color: white; }}
    .titulo-mccoffee {{ text-align: center; color: #d4af37; font-family: 'Impact'; font-size: 35px; white-space: nowrap; }}
    .total-gigante {{ color: #d4af37; font-size: 60px !important; font-weight: bold; text-align: center; }}
    .stMetricValue {{ color: #d4af37 !important; }}
    .stButton>button {{ border-radius: 0px; border: 1px solid #d4af37; background: #000; color: #d4af37; width: 100%; }}
    .ranking-row {{ background-color: #111; padding: 5px; border-radius: 5px; margin-bottom: 5px; border-left: 3px solid #d4af37; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (REPORTES) ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mccoffee'>CONTROL TOTAL<br> MCCOFFEE 2026</h1>", unsafe_allow_html=True)
    st.markdown("---")
    hoy = datetime.now().date()
    # Filtro para datos de hoy
    df_hoy = df_v[df_v['Fecha_DT'].dt.date == hoy]
    v_hoy = df_hoy['Monto'].sum()
    v_sem = df_v[df_v['Fecha_DT'] >= (datetime.now() - timedelta(days=7))]['Monto'].sum()
    
    st.metric("CORTE DE HOY", f"${v_hoy:,.2f}")
    st.progress(min(v_hoy / meta_diaria, 1.0))
    st.caption(f"Meta Diaria: ${meta_diaria:,.0f}")
    
    # --- RANKING DE VENDEDORES (ACTUALIZADO: TEXTO CON % META TOTAL) ---
    st.markdown("---")
    st.markdown("### 🏆 RANKING DIARIO")
    if not df_st.empty:
        ventas_hoy = df_hoy.groupby('Vend')['Monto'].sum().reset_index()
        # Unimos para que salgan todos los vendedores aunque lleven $0
        ranking = pd.merge(df_st, ventas_hoy, left_on='Nombre', right_on='Vend', how='left').fillna(0)
        ranking = ranking.sort_values(by='Monto', ascending=False)
        
        for _, r in ranking.iterrows():
            # 1. Calculamos el progreso visual de la barra (Meta Individual Simbólica) - ESTO NO SE TOCA
            meta_ind = meta_diaria / len(df_st) if len(df_st) > 0 else 1000
            progreso_barra = min(r['Monto'] / meta_ind, 1.0)
            
            # 2. Calculamos el Porcentaje REAL sobre la META TOTAL para el texto
            porcentaje_real = (r['Monto'] / meta_diaria * 100) if meta_diaria > 0 else 0
            
            # Mostramos: Nombre | Dinero (Porcentaje%)
            st.markdown(f"""<div class='ranking-row'><div style='display:flex; justify-content:space-between;'><b>{r['Nombre']}</b><span style='color:#d4af37'>${r['Monto']:,.0f} ({porcentaje_real:.0f}%)</span></div></div>""", unsafe_allow_html=True)
            st.progress(progreso_barra)
    # --------------------------------------------

    st.markdown("---")
    st.write("📅 PROGRESO SEMANAL")
    st.metric("VENTA SEMANA", f"${v_sem:,.2f}")
    st.markdown(f"""<style>div.stProgress > div > div > div > div {{ background-color: #28a745 !important; }}</style>""", unsafe_allow_html=True)
    st.progress(min(v_sem / meta_semanal, 1.0))
    st.caption(f"Objetivo Semanal: ${meta_semanal:,.0f}")
    
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
    
    # --- PRECIO EDITABLE ---
    c4, c5, c6, c7 = st.columns([2, 1, 1, 1]) 
    v_p = c4.selectbox("Producto", df_p['Cod'].tolist() if not df_p.empty else ["N/A"], key="v_sel_2")
    
    # Obtenemos precio base
    precio_base = 0.0
    if not df_p.empty and v_p in df_p['Cod'].values:
        precio_base = float(df_p[df_p['Cod'] == v_p]['Pre'].values[0])
        
    # Input editable para el precio (Ofertas)
    v_precio_final = c5.number_input("Precio ($)", min_value=0.0, value=precio_base, step=1.0)
    v_ca = c6.number_input("Cant.", min_value=0.1, value=1.0, key="v_num_1")
    
    if c7.button("➕ AÑADIR"):
        if 'car' not in st.session_state: st.session_state.car = []
        pi = df_p[df_p['Cod'] == v_p].iloc[0] if not df_p.empty else None
        nom_prod = pi['Nom'] if pi is not None else "Item"
        # Usamos el precio editado v_precio_final
        st.session_state.car.append({"Cod": v_p, "Nom": nom_prod, "Cant": v_ca, "Sub": v_precio_final*v_ca, "PrecioU": v_precio_final})
    
    if 'car' in st.session_state and st.session_state.car:
        # Mostramos también el precio unitario usado
        st.table(pd.DataFrame(st.session_state.car)[["Cant", "Nom", "PrecioU", "Sub"]])
        tv = sum(i['Sub'] for i in st.session_state.car)
        st.markdown(f"<p class='total-gigante'>${tv:,.2f}</p>", unsafe_allow_html=True)
        if st.button("🚀 REGISTRAR VENTA FINAL"):
            nid = int(df_v['ID'].max() + 1 if not df_v.empty else 1)
            # Guardamos detalle con precio real
            det = ", ".join([f"{i['Cant']} {i['Nom']} (${i['PrecioU']})" for i in st.session_state.car])
            nv = pd.DataFrame([{"ID": nid, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Vend": v_v, "Cli": v_c, "Tel": v_t, "Prod": det, "Monto": tv, "Est": "Pendiente"}])
            for i in st.session_state.car:
                mk = (df_a['Vendedor'] == v_v) & (df_a['Cod'] == i['Cod'])
                if mk.any(): df_a.loc[mk, 'Vendido'] += i['Cant']; df_a.loc[mk, 'Actual'] -= i['Cant']
                # Si no existe registro en auditoría, se crea (aunque sea negativo para alertar)
                else: 
                     new_audit = pd.DataFrame([{"Vendedor": v_v, "Cod": i['Cod'], "Entregado": 0, "Vendido": i['Cant'], "Actual": -i['Cant']}])
                     df_a = pd.concat([df_a, new_audit])

            pd.concat([df_v, nv]).to_csv(db_v, index=False); df_a.to_csv(db_a, index=False); st.session_state.car = []; st.rerun()

with tab_p: # CONTROL DE PEDIDOS
    # Filtramos para mostrar los pendientes primero
    pedidos_ordenados = df_v.sort_values(by=['Est', 'ID'], ascending=[False, False]).head(20)
    
    for idx, row in pedidos_ordenados.iterrows():
        # Lógica visual para distinguir entregados, pendientes y siniestros
        color_ico = "🟢" if "Entregado" in row['Est'] else "🟠"
        if "Siniestro" in row['Est']: color_ico = "🔴"
        
        with st.container():
            st.markdown(f"*{color_ico} #{row['ID']} | {row['Vend']}* | {row['Cli']} | Total: ${row['Monto']:,.2f}")
            st.caption(f"📦 {row['Prod']} ({row['Est']})")
            
            if row['Est'] == "Pendiente":
                c_ok, c_gar, c_monto = st.columns([1, 1, 1])
                
                # Botón Normal
                if c_ok.button("✅ ENTREGAR", key=f"btn_ok_{row['ID']}"):
                    df_v.at[idx, 'Est'] = "Entregado"
                    df_v.to_csv(db_v, index=False); st.rerun()
                
                # --- NUEVA FUNCIÓN: GARANTÍA / SINIESTRO ---
                costo_reenvio = c_monto.number_input(f"Costo Reenvío $", min_value=0.0, value=0.0, step=10.0, key=f"num_gar_{row['ID']}")
                if c_gar.button("🔄 GARANTÍA (CAÍDO)", key=f"btn_gar_{row['ID']}"):
                    # 1. Marcamos el viejo como Siniestro (Dinero se queda, stock ya se descontó)
                    df_v.at[idx, 'Est'] = "Entregado (Siniestro)"
                    # 2. Creamos NUEVO pedido automático por el reenvío
                    nid_new = int(df_v['ID'].max() + 1)
                    # Nota: Este nuevo pedido entra como Pendiente -> Implica que debe salir OTRO producto de la mochila.
                    nv_gar = pd.DataFrame([{
                        "ID": nid_new, 
                        "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                        "Vend": row['Vend'], 
                        "Cli": row['Cli'] + " (REPO)", 
                        "Tel": row['Tel'], 
                        "Prod": f"[GARANTÍA] {row['Prod']}", 
                        "Monto": costo_reenvio, # Solo entra lo del envío
                        "Est": "Pendiente"
                    }])
                    df_v = pd.concat([df_v, nv_gar])
                    df_v.to_csv(db_v, index=False)
                    st.warning(f"Garantía aplicada. Nuevo pedido #{nid_new} generado."); st.rerun()
                # -------------------------------------------
            else:
                # --- BOTÓN DE CORRECCIÓN AÑADIDO (PARA VOLVER A PENDIENTE) ---
                if st.button("↩️ CORREGIR (VOLVER A PENDIENTE)", key=f"btn_fix_{row['ID']}"):
                    df_v.at[idx, 'Est'] = "Pendiente"
                    df_v.to_csv(db_v, index=False); st.rerun()
            
            st.markdown("---")

with tab_j: # PANEL JEFE
    pw = st.text_input("Contraseña", type="password")
    if pw == CLAVE_MAESTRA:
        # --- APARTADO PARA AJUSTAR METAS ---
        with st.expander("🎯 CONFIGURAR METAS DE VENTA"):
            col_m1, col_m2 = st.columns(2)
            nueva_m_diaria = col_m1.number_input("Meta Diaria ($)", min_value=0.0, value=meta_diaria)
            nueva_m_semanal = col_m2.number_input("Meta Semanal ($)", min_value=0.0, value=meta_semanal)
            if st.button("ACTUALIZAR OBJETIVOS"):
                with open(db_m, "w") as f: f.write(str(nueva_m_diaria))
                with open(db_mw, "w") as f: f.write(str(nueva_m_semanal))
                st.success("Metas actualizadas correctamente.")
                st.rerun()

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
            # --- AQUÍ ESTÁ EL CAMBIO SOLICITADO (YA INTEGRADO) ---
            pc, pn, pp, pu = f1.text_input("Clave", key="p_1"), f2.text_input("Nombre", key="p_2"), f3.number_input("$", key="p_3"), f4.text_input("Uni", placeholder="KG, LB, OZ...", key="p_4")
            
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



