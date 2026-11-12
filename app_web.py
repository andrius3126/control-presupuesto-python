import streamlit as st
from datetime import datetime
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Control de Presupuesto", page_icon="💰", layout="centered")

# --- INICIALIZACIÓN DE MEMORIA PRIVADA POR SESIÓN ---
if "saldo_total" not in st.session_state:
    st.session_state.saldo_total = 0.0

if "historial_gastos" not in st.session_state:
    st.session_state.historial_gastos = []

# Calculamos totales en tiempo real desde la sesión del usuario
saldo_total = st.session_state.saldo_total
historial_gastos = st.session_state.historial_gastos
total_gastos = sum(g["monto"] for g in historial_gastos)
total_ingresos = saldo_total + total_gastos

# --- INTERFAZ PRINCIPAL ---
st.title("💰 Control de Presupuesto")
st.caption("Gestiona tus finanzas de forma privada en tu sesión actual")

# 1. Tarjetas de Métricas
col1, col2, col3 = st.columns(3)
col1.metric("💵 Saldo Disponible", f"${saldo_total:,.0f}")
col2.metric("📈 Ingresos Totales", f"${total_ingresos:,.0f}")
col3.metric("📉 Gastos Totales", f"${total_gastos:,.0f}")

st.divider()

# 2. Pestañas de navegación
tab_gasto, tab_ingreso, tab_analisis = st.tabs(["📉 Registrar Gasto", "➕ Sumar Ingreso", "📊 Historial y Gráficos"])

# --- PESTAÑA 1: REGISTRAR GASTO ---
with tab_gasto:
    st.subheader("Nuevo Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        monto_g = st.number_input("Monto del gasto ($)", min_value=0.0, step=1000.0, format="%.2f")
        categoria_g = st.selectbox(
            "Categoría",
            ["Comida", "Transporte", "Entretenimiento", "Servicios", "Suscripciones", "Otros"]
        )
        desc_g = st.text_input("Descripción (ej. Almuerzo, Transporte, Cine)")
        
        enviado_g = st.form_submit_button("Registrar Gasto", type="primary", use_container_width=True)
        
        if enviado_g:
            if monto_g <= 0:
                st.error("❌ El monto debe ser mayor a cero.")
            elif monto_g > st.session_state.saldo_total:
                st.warning("⚠️ Fondos insuficientes para registrar este gasto.")
            else:
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
                nuevo_gasto = {
                    "fecha": fecha_actual,
                    "categoria": categoria_g,
                    "descripcion": desc_g.strip() or "Sin descripción",
                    "monto": monto_g
                }
                st.session_state.saldo_total -= monto_g
                st.session_state.historial_gastos.append(nuevo_gasto)
                st.success(f"✅ Gasto de ${monto_g:,.2f} registrado correctamente.")
                st.rerun()

# --- PESTAÑA 2: SUMAR INGRESO ---
with tab_ingreso:
    st.subheader("Nuevo Ingreso")
    with st.form("form_ingreso", clear_on_submit=True):
        monto_i = st.number_input("Monto del ingreso ($)", min_value=0.0, step=5000.0, format="%.2f")
        enviado_i = st.form_submit_button("Sumar al Saldo", type="primary", use_container_width=True)
        
        if enviado_i:
            if monto_i <= 0:
                st.error("❌ El monto debe ser mayor a cero.")
            else:
                st.session_state.saldo_total += monto_i
                st.success(f"✅ Se sumaron ${monto_i:,.2f} a tu saldo.")
                st.rerun()

# --- PESTAÑA 3: HISTORIAL, GRÁFICOS Y EXPORTACIÓN ---
with tab_analisis:
    if not st.session_state.historial_gastos:
        st.info("Aún no tienes gastos registrados en esta sesión. ¡Empieza añadiendo un ingreso y un gasto!")
    else:
        df = pd.DataFrame(st.session_state.historial_gastos)
        df_mostrar = df[["fecha", "categoria", "descripcion", "monto"]].copy()
        df_mostrar.columns = ["Fecha", "Categoría", "Descripción", "Monto ($)"]

        st.subheader("📊 Gastos por Categoría")
        resumen_cat = df.groupby("categoria")["monto"].sum()
        st.bar_chart(resumen_cat)

        st.subheader("📋 Detalle de Movimientos")
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        # Exportación limpia para Excel en español
        csv = df_mostrar.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Descargar Reporte en Excel (CSV)",
            data=csv,
            file_name="reporte_presupuesto.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.divider()
        st.subheader("🗑️ Eliminar un gasto")
        opciones_borrar = [
            f"{i+1}. [{g['categoria']}] {g['descripcion']} - ${g['monto']:,.2f}"
            for i, g in enumerate(st.session_state.historial_gastos)
        ]
        seleccion = st.selectbox("Selecciona el registro a eliminar:", opciones_borrar)
        
        if st.button("Eliminar Registro Seleccionado"):
            indice = opciones_borrar.index(seleccion)
            eliminado = st.session_state.historial_gastos.pop(indice)
            st.session_state.saldo_total += eliminado["monto"]
            st.success(f"✅ Gasto eliminado. Se devolvieron ${eliminado['monto']:,.2f} a tu saldo.")
            st.rerun()
