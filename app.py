import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash

# --- Configuración Flask ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

# --- Conexión a Postgres por DATABASE_URL ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

def get_conn():
    # Render requiere sslmode=require
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def ensure_table():
    sql = """
    CREATE TABLE IF NOT EXISTS personas (
        id SERIAL PRIMARY KEY,
        dni VARCHAR(20) NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100) NOT NULL,
        direccion TEXT,
        telefono VARCHAR(20)
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

# --- Rutas ---
@app.route("/")
def index():
    return render_template("index.html")

@app.post("/crear")
def crear():
    dni = request.form.get("dni", "").strip()
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    direccion = request.form.get("direccion", "").strip()
    telefono = request.form.get("telefono", "").strip()

    if not dni or not nombre or not apellido:
        flash("DNI, Nombre y Apellido son obligatorios", "error")
        return redirect(url_for("index"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO personas (dni, nombre, apellido, direccion, telefono) VALUES (%s, %s, %s, %s, %s)",
                (dni, nombre, apellido, direccion, telefono),
            )
        conn.commit()

    flash("Registro guardado correctamente", "ok")
    return redirect(url_for("index"))

@app.get("/administrar")
def administrar():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, dni, nombre, apellido, direccion, telefono FROM personas ORDER BY id DESC")
            personas = cur.fetchall()
    return render_template("administrar.html", personas=personas)

@app.post("/eliminar/<int:pid>")
def eliminar(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM personas WHERE id=%s", (pid,))
        conn.commit()
    flash("Registro eliminado", "ok")
    return redirect(url_for("administrar"))

if __name__ == "__main__":
    ensure_table()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
