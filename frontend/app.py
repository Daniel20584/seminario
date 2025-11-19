# /frontend/app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Obtén la URL del API Gateway desde las variables de entorno.
# Esta variable debe estar configurada en el docker-compose.yml.
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

@app.route("/")
def index():
    if session.get("username"):
        role = session.get("role")
        if role == "turista":
            return redirect(url_for("experiences"))
        elif role == "guia":
            return redirect(url_for("guide_panel"))
        elif role == "admin":
            return redirect(url_for("admin_panel"))
        else:
            flash("Rol desconocido.", "danger")
            return redirect(url_for("logout"))
    return render_template("start.html")

@app.route("/guide-panel")
def guide_panel():
    guide = session.get("username")
    experiences = []
    if not guide:
        flash("No se pudo identificar al guía logueado.", "danger")
        return render_template("guide_panel.html", title="Panel de Guía", experiences=[])
    consulta_url = f"{API_GATEWAY_URL}/api/v1/experiences/experiences?guide={guide}"
    try:
        resp = requests.get(consulta_url, timeout=5)
        data = resp.json()
        experiences = data.get("experiences") or data
    except Exception:
        print("Error obteniendo experiencias del guía")
        flash("No se pudieron cargar las experiencias del guía.", "danger")
    return render_template("guide_panel.html", title="Panel de Guía", experiences=experiences)

@app.route("/admin-panel")
def admin_panel():
    # Panel de administración
    return render_template("admin_panel.html", title="Panel de Administrador")

@app.route("/new-item", methods=["GET", "POST"])
def new_item():
    """Ruta para crear un nuevo ítem."""
    if request.method == "POST":
        # Recoge los datos del formulario.
        item_data = {
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "price": float(request.form.get("price")),
            "guide": session.get("username")
        }
        # Envía los datos al API Gateway para crear un nuevo recurso.
        try:
            resp = requests.post(f"{API_GATEWAY_URL}/api/v1/experiences/experiences", json=item_data, timeout=5)
            if resp.status_code == 200:
                flash("Experiencia creada con éxito.", "success")
            else:
                flash("No se pudo crear la experiencia.", "danger")
        except requests.exceptions.RequestException as e:
            print(f"Error creando experiencia: {e}")
            flash("Error creando la experiencia.", "danger")
        # Recarga la lista de experiencias del guía
        guide = session.get("username")
        try:
            resp = requests.get(f"{API_GATEWAY_URL}/api/v1/experiences/experiences?guide={guide}", timeout=5)
            data = resp.json()
            exps = data.get("experiences") or data
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo experiencias: {e}")
            exps = []
        return render_template("experiences.html", title="Experiencias", experiences=exps)

    return render_template("form.html", title="Nuevo Ítem")


@app.route("/experiences")
def experiences():
    """Lista de experiencias obtenidas desde el API Gateway."""
    exps = []
    try:
        if session.get("role") == "guia":
            guide = session.get("username")
            if not guide:
                flash("No se pudo identificar al guía logueado.", "danger")
            else:
                resp = requests.get(f"{API_GATEWAY_URL}/api/v1/experiences/experiences?guide={guide}", timeout=5)
                data = resp.json()
                exps = data.get("experiences") or data
        else:
            resp = requests.get(f"{API_GATEWAY_URL}/api/v1/experiences/experiences", timeout=5)
            data = resp.json()
            exps = data.get("experiences") or data
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo experiencias: {e}")
        flash("No se pudieron cargar las experiencias.", "danger")
    return render_template("experiences.html", title="Experiencias", experiences=exps)


@app.route("/experiences/<string:exp_id>/reserve", methods=["GET", "POST"])
def reserve(exp_id):
    if request.method == "POST":
        # Recolectar datos del formulario
        reservation = {
            "experience_id": exp_id,
            "user_id": request.form.get("user_id", "anonymous"),
            "date": request.form.get("date"),
            "notes": request.form.get("notes", "")
        }
        try:
            resp = requests.post(f"{API_GATEWAY_URL}/api/v1/reservations/reservations", json=reservation, timeout=5)
            resp.raise_for_status()
            return render_template("message.html", title="Reserva creada", message="Reserva creada correctamente.")
        except requests.exceptions.RequestException as e:
            return render_template("message.html", title="Error", message=f"Error creando reserva: {e}")

    return render_template("reserve.html", title="Reservar", exp_id=exp_id)


@app.route("/experiences/<string:exp_id>/rate", methods=["GET", "POST"])
def rate(exp_id):
    if request.method == "POST":
        rating = {
            "user_id": request.form.get("user_id", "anonymous"),
            "experience_id": exp_id,
            "comment": request.form.get("comment", ""),
            "rating": int(request.form.get("rating", 5))
        }
        try:
            resp = requests.post(f"{API_GATEWAY_URL}/api/v1/ratings/ratings", json=rating, timeout=5)
            resp.raise_for_status()
            return render_template("message.html", title="Valoración creada", message="Valoración creada correctamente.")
        except requests.exceptions.RequestException as e:
            return render_template("message.html", title="Error", message=f"Error creando valoración: {e}")

    return render_template("rate.html", title="Valorar", exp_id=exp_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            resp = requests.post(f"{API_GATEWAY_URL}/api/v1/auth/login", json={"username": username, "password": password}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                session["username"] = username
                session["role"] = data.get("role", "turista")
                flash("Bienvenido, {}!".format(username), "success")
                return redirect(url_for("index"))
            else:
                flash("Usuario o contraseña incorrectos.", "danger")
        except Exception as e:
            flash(f"Error de conexión: {e}", "danger")
    return render_template("login.html", title="Iniciar sesión")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        try:
            resp = requests.post(
                f"{API_GATEWAY_URL}/api/v1/auth/register",
                json={"username": username, "password": password, "role": role},
                timeout=5
            )
            if resp.status_code in [200, 201]:
                flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
                return redirect(url_for("login"))
            else:
                error_message = resp.json().get("detail", "No se pudo registrar el usuario.")
                flash(error_message, "danger")
        except requests.exceptions.RequestException as e:
            flash(f"Error de conexión: {e}", "danger")
    return render_template("register.html", title="Registro")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("index"))

@app.route('/start')
def start():
    return render_template('start.html')

@app.route("/experiences/new", methods=["GET", "POST"])
def new_experience():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = request.form["price"]
        try:
            guide = session.get("username")
            resp = requests.post(
                f"{API_GATEWAY_URL}/api/v1/experiences/experiences",
                json={"title": title, "description": description, "price": price, "guide": guide},
                timeout=5
            )
            if resp.status_code in [200, 201]:
                flash("Experiencia creada exitosamente.", "success")
                return redirect(url_for("experiences"))
            else:
                error_message = resp.json().get("detail", "No se pudo crear la experiencia.")
                flash(error_message, "danger")
        except requests.exceptions.RequestException as e:
            flash(f"Error de conexión: {e}", "danger")
    return render_template("form.html", title="Nueva Experiencia")

@app.route("/guide-experiences")
def guide_experiences():
    if not session.get("username") or session.get("role") != "guia":
        flash("Acceso denegado.", "danger")
        return redirect(url_for("login"))

    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/experiences?guide={session.get('username')}",
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        experiences = data.get("experiences", [])
    except requests.exceptions.RequestException as e:
        flash(f"Error obteniendo experiencias: {e}", "danger")
        experiences = []

    return render_template("guide_experiences.html", title="Mis Experiencias", experiences=experiences)

@app.route("/experiences/<string:exp_id>/edit", methods=["GET", "POST"])
def edit_experience(exp_id):
    if request.method == "GET":
        try:
            resp = requests.get(f"{API_GATEWAY_URL}/api/v1/experiences/experiences/{exp_id}", timeout=5)
            experience = resp.json().get("experience")
            if not experience:
                flash("Experiencia no encontrada.", "danger")
                # Redirige según el rol del usuario
                if session.get("role") == "admin":
                    return redirect(url_for("admin_experiences"))
                return redirect(url_for("guide_panel"))
            return render_template("form.html", title="Editar Experiencia", experience=experience)
        except Exception:
            flash("Error cargando la experiencia.", "danger")
            if session.get("role") == "admin":
                return redirect(url_for("admin_experiences"))
            return redirect(url_for("guide_panel"))

    if request.method == "POST":
        # Preserve original guide when admin edits
        guide_owner = session.get("username")
        if session.get("role") == "admin":
            try:
                existing = requests.get(f"{API_GATEWAY_URL}/api/v1/experiences/experiences/{exp_id}", timeout=5).json().get("experience")
                if existing and existing.get("guide"):
                    guide_owner = existing.get("guide")
            except Exception:
                # Fall back to current user if we cannot fetch existing
                guide_owner = session.get("username")

        updated_data = {
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "price": float(request.form.get("price")),
            "guide": guide_owner
        }
        try:
            resp = requests.put(f"{API_GATEWAY_URL}/api/v1/experiences/experiences/{exp_id}", json=updated_data, timeout=5)
            if resp.status_code == 200:
                flash("Experiencia actualizada con éxito.", "success")
            else:
                flash("No se pudo actualizar la experiencia.", "danger")
        except Exception:
            flash("Error actualizando la experiencia.", "danger")
        # Redirige según rol
        if session.get("role") == "admin":
            return redirect(url_for("admin_experiences"))
        return redirect(url_for("guide_panel"))


@app.route("/experiences/<exp_id>/delete", methods=["POST"])
def delete_experience(exp_id):
    try:
        resp = requests.delete(f"{API_GATEWAY_URL}/api/v1/experiences/experiences/{exp_id}", timeout=5)
        if resp.status_code == 200:
            flash("Experiencia eliminada con éxito.", "success")
        else:
            flash("No se pudo eliminar la experiencia.", "danger")
    except Exception:
        flash("Error eliminando la experiencia.", "danger")
    # Redirige al panel correspondiente según el rol
    if session.get("role") == "admin":
        return redirect(url_for("admin_experiences"))
    return redirect(url_for("guide_panel"))

@app.route("/admin-experiences")
def admin_experiences():
    if session.get("role") != "admin":
        flash("Acceso denegado.", "danger")
        return redirect(url_for("index"))
    exps = []
    try:
        resp = requests.get(f"{API_GATEWAY_URL}/api/v1/experiences/experiences", timeout=5)
        data = resp.json()
        exps = data.get("experiences") or data
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo experiencias: {e}")
        flash("No se pudieron cargar las experiencias.", "danger")
    return render_template("admin_experiences.html", title="Experiencias (Admin)", experiences=exps)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
