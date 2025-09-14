import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash

# Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")  # necesario para flash()

# Postgres (Render -> External Database URL)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

def get_conn():
    # En Render se requiere SSL
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def ensure_table():
    sql = """
    CREATE TABLE IF NOT EXISTS personas (
        id SERIAL PRIMARY KEY,
        dni VARCHAR(20) NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100) NOT NULL,
        direccion TEXT,
        telefono VARCHAR(20),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()

# --- Rutas ---
@app.get("/")
def index():
    # Página de registro
    return render_template("index.html")

@app.post("/crear")
def crear():
    # Recoge datos del formulario
    dni       = request.form.get("dni", "").strip()
    nombre    = request.form.get("nombre", "").strip()
    apellido  = request.form.get("apellido", "").strip()
    direccion = request.form.get("direccion", "").strip()
    telefono  = request.form.get("telefono", "").strip()

    # Validación sencilla
    if not dni or not nombre or not apellido:
        flash("DNI, Nombre y Apellido son obligatorios", "error")
        return redirect(url_for("index"))

    # Inserta
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO personas (dni, nombre, apellido, direccion, telefono)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (dni, nombre, apellido, direccion, telefono),
        )
        conn.commit()

    flash("Persona registrada", "success")
    return redirect(url_for("index"))

@app.get("/admin")
def administrar():
    # Lista todo
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM personas ORDER BY id DESC")
        personas = cur.fetchall()
    return render_template("administrar.html", personas=personas)

@app.post("/eliminar/<int:pid>")
def eliminar(pid):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM personas WHERE id = %s", (pid,))
        conn.commit()
    flash("Registro eliminado", "success")
    return redirect(url_for("administrar"))

# Crear tabla al iniciar
ensure_table()

if __name__ == "__main__":
    # Para local
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
