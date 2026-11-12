import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# Configuración de la página (adaptable a móvil y escritorio)
st.set_page_config(page_title="Control de Presupuesto", page_icon="💰", layout="centered")

ARCHIVO_DATOS = "datos_presupuesto.json"

# --- FUNCIONES DE DATOS ---

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    return {"saldo_total": 0.0, "historial_gastos": []}

def guardar_datos(saldo, historial):
    datos = {"saldo_total": saldo, "historial_gastos": historial}
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

datos = cargar_datos()
saldo_total = datos["saldo_total"]
historial_gastos = datos["historial_gastos"]

# Calculamos el total de gastos e ingresos históricos
total_gastos = sum(g["monto"] for g in historial_gastos)
total_ingresos = saldo_total + total_gastos

# --- INTERFAZ PRINCIPAL ---

st.title("💰 Control de Presupuesto")
st.caption("Gestiona tus finanzas desde tu computadora o celular")

# 1. Tarjetas de Métricas (3 columnas)
col1, col2, col3 = st.columns(3)
col1.metric("💵 Saldo Disponible", f"${saldo_total:,.0f}")
col2.metric("📈 Ingresos Totales", f"${total_ingresos:,.0f}")
col3.metric("📉 Gastos Totales", f"${total_gastos:,.0f}")

st.divider()

# 2. Pestañas para organizar la pantalla (ideal para celulares)
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
        desc_g = st.text_input("Descripción (ej. Almuerzo, DiDi, Cine)")
        
        enviado_g = st.form_submit_button("Registrar Gasto", type="primary", use_container_width=True)
        
        if enviado_g:
            if monto_g <= 0:
                st.error("❌ El monto debe ser mayor a cero.")
            elif monto_g > saldo_total:
                st.warning("⚠️ Fondos insuficientes para registrar este gasto.")
            else:
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
                nuevo_gasto = {
                    "fecha": fecha_actual,
                    "categoria": categoria_g,
                    "descripcion": desc_g.strip() or "Sin descripción",
                    "monto": monto_g
                }
                saldo_total -= monto_g
                historial_gastos.append(nuevo_gasto)
                guardar_datos(saldo_total, historial_gastos)
                st.success(f"✅ Gasto de ${monto_g:,.2f} guardado correctamente.")
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
                saldo_total += monto_i
                guardar_datos(saldo_total, historial_gastos)
                st.success(f"✅ Se sumaron ${monto_i:,.2f} a tu saldo.")
                st.rerun()

# --- PESTAÑA 3: HISTORIAL, GRÁFICOS Y EXPORTACIÓN ---
with tab_analisis:
    if not historial_gastos:
        st.info("Aún no tienes gastos registrados. ¡Empieza añadiendo uno en la primera pestaña!")
    else:
        # Convertimos el historial a una tabla inteligente (DataFrame)
        df = pd.DataFrame(historial_gastos)
        if "fecha" not in df.columns:
            df["fecha"] = "Sin fecha"
        df["fecha"] = df["fecha"].fillna("Sin fecha")
        
        # Reordenamos las columnas
        df_mostrar = df[["fecha", "categoria", "descripcion", "monto"]].copy()
        df_mostrar.columns = ["Fecha", "Categoría", "Descripción", "Monto ($)"]

        st.subheader("📊 Gastos por Categoría")
        resumen_cat = df.groupby("categoria")["monto"].sum()
        st.bar_chart(resumen_cat)

        st.subheader("📋 Detalle de Movimientos")
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

       # Botón para descargar en Excel / CSV (separado por punto y coma y con tildes corregidas)
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
            for i, g in enumerate(historial_gastos)
        ]
        seleccion = st.selectbox("Selecciona el registro a eliminar:", opciones_borrar)
        
        if st.button("Eliminar Registro Seleccionado"):
            indice = opciones_borrar.index(seleccion)
            eliminado = historial_gastos.pop(indice)
            saldo_total += eliminado["monto"]
            guardar_datos(saldo_total, historial_gastos)
            st.success(f"✅ Gasto eliminado. Se devolvieron ${eliminado['monto']:,.2f} a tu saldo.")
            st.rerun()
