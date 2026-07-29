"""
UMBook — Aplicación Flask
Implementación completa de CU-02, CU-06 y CU-13
con interfaz web respetando el diseño de pantallas.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, session, flash

from infrastructure.persistencia import Persistencia
from infrastructure.seguridad import Seguridad
from models.gestion_usuarios import GestionUsuarios
from models.repositorios import (RepositorioAmistad, RepositorioFoto,
                                  RepositorioComentario, RepositorioGrupo)
from models.usuario import Usuario
from models.entidades import Amistad, Foto, Comentario
from controllers.auth_controller import AuthController
from controllers.registro_controller import RegistroController
from controllers.perfil_controller import PerfilController
from controllers.eliminar_amigo_controller import EliminarAmigoController
from controllers.moderar_comentario_controller import ModerarComentarioController
from controllers.grupos_controller import GrupoController
from controllers.permisos_controller import PermisosController
from controllers.admin_controller import DeshabilitarUsuarioCtrl
from controllers.busqueda_controller import BusquedaController
from controllers.comentario_controller import ComentarioController
from controllers.solicitud_amistad_controller import SolicitudAmistadController
from controllers.sugerencias_amigos_controller import SugerenciasAmigosController
from controllers.visibilidad_album_controller import VisibilidadAlbumController

# ── Inicialización ──
app = Flask(__name__)
app.secret_key = "umbook-secret-2026"
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'fotos')
os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'fotos'), exist_ok=True)

Persistencia().conectar(os.path.join(os.path.dirname(__file__), "umbook.db"))
_inicializado = False


def inicializar_datos_demo():
    """Crea datos de demo si la BD está vacía."""
    db = Persistencia().obtener_conexion()
    if db.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] > 0:
        return
    seg = Seguridad()
    gestion = GestionUsuarios()
    repo_amistad = RepositorioAmistad()
    repo_foto = RepositorioFoto()
    repo_com = RepositorioComentario()

    # ── Usuarios ──
    u1 = gestion.guardar(Usuario(nombre="Valentina", apellido="Rodriguez",
        email="vrodr@um.edu.ar", contrasena=seg.hashear_contrasena("1234"),
        dias_aviso=7, fecha_nac="2001-03-15"))
    u2 = gestion.guardar(Usuario(nombre="Martín", apellido="Díaz",
        email="mdiaz@um.edu.ar", contrasena=seg.hashear_contrasena("1234"),
        fecha_nac="2000-11-20"))
    u3 = gestion.guardar(Usuario(nombre="Lucía", apellido="Fernández",
        email="lfern@um.edu.ar", contrasena=seg.hashear_contrasena("1234"),
        fecha_nac="2001-07-08"))
    u4 = gestion.guardar(Usuario(nombre="Santiago", apellido="Molina",
        email="smoli@um.edu.ar", contrasena=seg.hashear_contrasena("1234"),
        fecha_nac="2000-05-22"))
    u5 = gestion.guardar(Usuario(nombre="Camila", apellido="Torres",
        email="ctorr@um.edu.ar", contrasena=seg.hashear_contrasena("1234"),
        fecha_nac="2001-12-01"))

    # ── Usuario administrador ──
    u_admin = gestion.guardar(Usuario(nombre="Admin", apellido="UMBook",
        email="admin@um.edu.ar", contrasena=seg.hashear_contrasena("admin123"),
        fecha_nac="1990-01-01"))
    db.execute("UPDATE usuario SET rol = ? WHERE id = ?", (Usuario.ROL_ADMIN, u_admin.id))
    db.commit()

    # ── Amistades de Valentina (u1) ──
    # Valentina tiene 4 amigos → CU-06 muestra lista con varios para eliminar
    repo_amistad.guardar(Amistad(usuario_origen=u1.id, usuario_destino=u2.id))
    repo_amistad.guardar(Amistad(usuario_origen=u1.id, usuario_destino=u3.id))
    repo_amistad.guardar(Amistad(usuario_origen=u1.id, usuario_destino=u4.id))
    repo_amistad.guardar(Amistad(usuario_origen=u1.id, usuario_destino=u5.id))

    # ── Amistades de Martín (u2) ──
    repo_amistad.guardar(Amistad(usuario_origen=u2.id, usuario_destino=u3.id))
    repo_amistad.guardar(Amistad(usuario_origen=u2.id, usuario_destino=u4.id))

    def crear_album(propietario_id, nombre, fecha):
        db.execute("INSERT INTO album (propietario, nombre, fecha_creacion) VALUES (?,?,?)",
                   (propietario_id, nombre, fecha))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # ── Álbumes y fotos de Valentina ──
    # Álbum 1: varios comentarios de distintos amigos → ideal para CU-13
    alb1 = crear_album(u1.id, "Egresados 2025", "2025-12-10")
    foto1 = repo_foto.guardar(Foto(propietario=u1.id, album_id=alb1,
                                   url_imagen="egresados_fiesta.jpg"))
    repo_com.guardar(Comentario(autor_id=u2.id, foto_id=foto1.id,
                                contenido="¡Qué noche tan épica! Los voy a extrañar 🎓"))
    repo_com.guardar(Comentario(autor_id=u3.id, foto_id=foto1.id,
                                contenido="No puedo creer que ya terminamos. Fue todo un viaje 🥹"))
    repo_com.guardar(Comentario(autor_id=u4.id, foto_id=foto1.id,
                                contenido="Me encanta esta foto, salimos todos perfectos 😄"))
    repo_com.guardar(Comentario(autor_id=u5.id, foto_id=foto1.id,
                                contenido="Inolvidable. ¡Repetimos pronto! 🙌"))

    foto2 = repo_foto.guardar(Foto(propietario=u1.id, album_id=alb1,
                                   url_imagen="egresados_salon.jpg"))
    repo_com.guardar(Comentario(autor_id=u2.id, foto_id=foto2.id,
                                contenido="El salón quedó hermoso esa noche ✨"))
    repo_com.guardar(Comentario(autor_id=u3.id, foto_id=foto2.id,
                                contenido="Qué recuerdos! Ya quiero que sea el de cuarto año 🎉"))

    # Álbum 2: fotos del campus → más comentarios para moderar
    alb2 = crear_album(u1.id, "Campus UM 2026", "2026-03-05")
    foto3 = repo_foto.guardar(Foto(propietario=u1.id, album_id=alb2,
                                   url_imagen="campus_primavera.jpg"))
    repo_com.guardar(Comentario(autor_id=u3.id, foto_id=foto3.id,
                                contenido="El campus en primavera es lo más 🌸"))
    repo_com.guardar(Comentario(autor_id=u4.id, foto_id=foto3.id,
                                contenido="Qué buena foto! Me la mandás?"))
    repo_com.guardar(Comentario(autor_id=u2.id, foto_id=foto3.id,
                                contenido="Yo quiero ir ahí el finde, me avisan!"))

    foto4 = repo_foto.guardar(Foto(propietario=u1.id, album_id=alb2,
                                   url_imagen="biblioteca_um.jpg"))
    repo_com.guardar(Comentario(autor_id=u5.id, foto_id=foto4.id,
                                contenido="Ahí pasé todas mis noches de parciales 📚"))
    repo_com.guardar(Comentario(autor_id=u3.id, foto_id=foto4.id,
                                contenido="La biblioteca nueva está increíble"))

    # ── Álbum de Martín (u2) con comentarios de Valentina ──
    alb3 = crear_album(u2.id, "Proyecto Final", "2026-05-20")
    foto5 = repo_foto.guardar(Foto(propietario=u2.id, album_id=alb3,
                                   url_imagen="proyecto_presentacion.jpg"))
    repo_com.guardar(Comentario(autor_id=u1.id, foto_id=foto5.id,
                                contenido="¡Felicitaciones Martín! Se los merecen 🏆"))
    repo_com.guardar(Comentario(autor_id=u3.id, foto_id=foto5.id,
                                contenido="Qué orgullo! Lo hicieron genial 👏"))

    # ── Grupos demo de Valentina (u1) — CU-08 / CU-09 ──
    repo_grupo = RepositorioGrupo()

    g1 = repo_grupo.crear(u1.id, "Familia")
    repo_grupo.actualizar_miembros(g1.id, u1.id, [u2.id, u3.id])
    from models.entidades import GrupoPermiso
    repo_grupo.guardar_permisos(GrupoPermiso(grupo_id=g1.id,
                                             ver_albumes=True,
                                             comentar_fotos=True,
                                             escribir_muro=True))

    g2 = repo_grupo.crear(u1.id, "Compañeros")
    repo_grupo.actualizar_miembros(g2.id, u1.id, [u4.id, u5.id])
    repo_grupo.guardar_permisos(GrupoPermiso(grupo_id=g2.id,
                                             ver_albumes=True,
                                             comentar_fotos=False,
                                             escribir_muro=False))



def login_requerido(f):
    from functools import wraps
    @wraps(f)
    def decorador(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        # REDC03: si un admin deshabilitó esta cuenta, sesion_version en BD
        # avanzó y ya no coincide con la que quedó guardada en la cookie.
        db = Persistencia().obtener_conexion()
        row = db.execute(
            "SELECT activo, sesion_version FROM usuario WHERE id = ?",
            (session["usuario_id"],)
        ).fetchone()
        if not row or not row["activo"] or row["sesion_version"] != session.get("sesion_version"):
            session.clear()
            return redirect(url_for(
                "login", error="Tu sesión fue cerrada por un administrador."))
        return f(*args, **kwargs)
    return decorador


@app.context_processor
def inject_solicitudes_count():
    if "usuario_id" in session:
        try:
            from controllers.solicitud_amistad_controller import SolicitudAmistadController
            ctrl = SolicitudAmistadController()
            return dict(solicitudes_count=ctrl.contar_pendientes(session["usuario_id"]))
        except Exception:
            pass
    return dict(solicitudes_count=0)


# ══════════════════════════════════════════════
# RUTAS DE AUTENTICACIÓN
# ══════════════════════════════════════════════

@app.route("/")
def index():
    if "usuario_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    global _inicializado
    if not _inicializado:
        inicializar_datos_demo()
        _inicializado = True

    if request.method == "POST":
        ctrl = AuthController()
        resultado = ctrl.login(request.form["email"], request.form["contrasena"])
        if resultado["ok"]:
            u = resultado["usuario"]
            db = Persistencia().obtener_conexion()
            row = db.execute(
                "SELECT rol, sesion_version FROM usuario WHERE id = ?", (u.id,)
            ).fetchone()
            session["usuario_id"] = u.id
            session["nombre"] = u.nombre
            session["apellido"] = u.apellido
            session["es_admin"] = bool(row and row["rol"] == Usuario.ROL_ADMIN)
            session["sesion_version"] = row["sesion_version"] if row else 0
            return redirect(url_for("home"))
        return render_template("login.html", error=resultado["mensaje"])

    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("login.html", exito=exito, error=error)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    form = {"nombre": "", "apellido": "", "email": "", "nombre_usuario": ""}
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ["nombre", "apellido", "email", "nombre_usuario"]}
        if request.form.get("contrasena") != request.form.get("contrasena2"):
            return render_template("registro.html",
                                   error="Las contraseñas no coinciden.", form=form)
        ctrl = RegistroController()
        resultado = ctrl.registrarUsuario({
            "nombre": form["nombre"], "apellido": form["apellido"],
            "email": form["email"], "nombre_usuario": form["nombre_usuario"],
            "contrasena": request.form.get("contrasena")
        })
        if resultado["ok"]:
            return redirect(url_for("login", exito="Cuenta creada. Podés iniciar sesión."))
        return render_template("registro.html", error=resultado["mensaje"], form=form)
    return render_template("registro.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ══════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════

@app.route("/home")
@login_requerido
def home():
    return render_template("home.html")

# ══════════════════════════════════════════════
# CU-03 — BUSCAR USUARIOS
# ══════════════════════════════════════════════

@app.route("/buscar")
@login_requerido
def buscar_usuarios():
    termino = request.args.get("termino", "")
    exito = request.args.get("exito")
    if not termino:
        return render_template("buscar.html", resultados=None, termino="", exito=exito)
    ctrl = BusquedaController(session["usuario_id"])
    resultado = ctrl.buscarUsuarios(termino)
    return render_template("buscar.html",
                           resultados=resultado.get("resultados", []),
                           termino=resultado.get("termino", termino),
                           error=resultado.get("mensaje") if not resultado["ok"] else None,
                           exito=exito)


@app.route("/amigos/agregar", methods=["POST"])
@login_requerido
def agregar_amigo():
    amigo_id = request.form.get("amigo_id")
    termino = request.form.get("termino", "")
    if not amigo_id or not amigo_id.isdigit():
        return redirect(url_for("buscar_usuarios", termino=termino))
    ctrl = BusquedaController(session["usuario_id"])
    resultado = ctrl.agregar_amigo(int(amigo_id))
    if resultado["ok"]:
        return redirect(url_for("buscar_usuarios", termino=termino, exito=resultado["mensaje"]))
    return redirect(url_for("buscar_usuarios", termino=termino, error=resultado["mensaje"]))


# ══════════════════════════════════════════════
# CU-05 — SOLICITUDES DE AMISTAD
# ══════════════════════════════════════════════

@app.route("/solicitudes")
@login_requerido
def solicitudes():
    ctrl = SolicitudAmistadController()
    resultado = ctrl.listar_recibidas(session["usuario_id"])
    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("solicitudes.html",
                           solicitudes=resultado.get("solicitudes", []),
                           exito=exito, error=error)

@app.route("/solicitudes/aceptar", methods=["POST"])
@login_requerido
def aceptar_solicitud():
    solicitud_id = request.form.get("solicitud_id")
    if not solicitud_id:
        return redirect(url_for("solicitudes"))
    ctrl = SolicitudAmistadController()
    resultado = ctrl.aceptar_solicitud(session["usuario_id"], int(solicitud_id))
    if resultado["ok"]:
        return redirect(url_for("solicitudes", exito=resultado["mensaje"]))
    return redirect(url_for("solicitudes", error=resultado["mensaje"]))

@app.route("/solicitudes/rechazar", methods=["POST"])
@login_requerido
def rechazar_solicitud():
    solicitud_id = request.form.get("solicitud_id")
    if not solicitud_id:
        return redirect(url_for("solicitudes"))
    ctrl = SolicitudAmistadController()
    resultado = ctrl.rechazar_solicitud(session["usuario_id"], int(solicitud_id))
    if resultado["ok"]:
        return redirect(url_for("solicitudes", exito=resultado["mensaje"]))
    return redirect(url_for("solicitudes", error=resultado["mensaje"]))


# ══════════════════════════════════════════════
# CU-07 — SUGERENCIAS DE AMIGOS
# ══════════════════════════════════════════════

@app.route("/sugerencias")
@login_requerido
def sugerencias():
    ctrl = SugerenciasAmigosController()
    resultado = ctrl.obtener_sugerencias(session["usuario_id"])
    exito = request.args.get("exito")
    return render_template("sugerencias.html",
                           sugerencias=resultado.get("sugerencias", []),
                           exito=exito)


# ── PERFIL ──
@app.route("/perfil")
@login_requerido
def perfil():
    gestion = GestionUsuarios()
    usuario = gestion.obtener_por_id(session["usuario_id"])
    return render_template("perfil.html", usuario=usuario)


# ══════════════════════════════════════════════
# CU-02 — EDITAR PERFIL
# ══════════════════════════════════════════════

@app.route("/perfil/editar", methods=["GET", "POST"])
@login_requerido
def editar_perfil():
    gestion = GestionUsuarios()
    usuario = gestion.obtener_por_id(session["usuario_id"])

    if request.method == "POST":
        datos = {}

        if request.form.get("nombre"):
            datos["nombre"] = request.form["nombre"]
        if request.form.get("apellido"):
            datos["apellido"] = request.form["apellido"]
        if request.form.get("email"):
            datos["email"] = request.form["email"]
        if request.form.get("fecha_nac"):
            datos["fecha_nac"] = request.form["fecha_nac"]
        if request.form.get("dias_aviso"):
            try:
                datos["dias_aviso"] = int(request.form["dias_aviso"])
            except ValueError:
                pass

        # Foto de perfil — la validación de formato y tamaño la hace el controller
        archivo = request.files.get("foto_perfil")
        if archivo and archivo.filename:
            contenido = archivo.read()
            nombre_archivo = archivo.filename.lower()
            # Pasar nombre y tamaño al controller para que valide
            datos["foto_perfil"] = nombre_archivo
            datos["foto_perfil_bytes"] = len(contenido)

            ctrl = PerfilController()
            resultado = ctrl.editar_perfil(session["usuario_id"], datos)

            if not resultado["ok"]:
                return render_template("editar_perfil.html", usuario=usuario,
                                       error=resultado["mensaje"])

            # Solo guardar el archivo en disco si el controller aprobó
            ext = os.path.splitext(nombre_archivo)[1]
            nombre_guardado = f"user_{session['usuario_id']}{ext}"
            ruta = os.path.join(os.path.dirname(__file__), "static", "fotos", nombre_guardado)
            with open(ruta, "wb") as f:
                f.write(contenido)
            # Actualizar la referencia correcta en el modelo
            datos["foto_perfil"] = nombre_guardado
            datos.pop("foto_perfil_bytes", None)
            resultado = ctrl.editar_perfil(session["usuario_id"], datos)
        else:
            ctrl = PerfilController()
            resultado = ctrl.editar_perfil(session["usuario_id"], datos)

        if resultado["ok"]:
            session["nombre"] = resultado["usuario"].nombre
            session["apellido"] = resultado["usuario"].apellido
            usuario = resultado["usuario"]
            return render_template("editar_perfil.html", usuario=usuario,
                                   exito="Perfil actualizado correctamente.")
        return render_template("editar_perfil.html", usuario=usuario,
                               error=resultado["mensaje"])

    return render_template("editar_perfil.html", usuario=usuario)


# ══════════════════════════════════════════════
# CU-06 — ELIMINAR AMIGO
# ══════════════════════════════════════════════

@app.route("/amigos")
@login_requerido
def amigos():
    ctrl = EliminarAmigoController()
    resultado = ctrl.listar_amigos(session["usuario_id"])
    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("amigos.html",
                           amigos=resultado.get("amigos", []),
                           exito=exito, error=error)


@app.route("/amigos/eliminar", methods=["POST"])
@login_requerido
def eliminar_amigo():
    amigo_id = request.form.get("amigo_id")
    if not amigo_id:
        return redirect(url_for("amigos", error="ID de amigo inválido."))
    ctrl = EliminarAmigoController()
    resultado = ctrl.eliminar_amigo(session["usuario_id"], int(amigo_id))
    if resultado["ok"]:
        return redirect(url_for("amigos", exito=resultado["mensaje"]))
    return redirect(url_for("amigos", error=resultado["mensaje"]))


# ══════════════════════════════════════════════
# CU-11 — ÁLBUMES Y VISIBILIDAD
# ══════════════════════════════════════════════

@app.route("/albumes")
@login_requerido
def albumes():
    ctrl = VisibilidadAlbumController()
    resultado = ctrl.listar_albumes(session["usuario_id"])
    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("albumes.html",
                           albumes=resultado.get("albumes", []),
                           grupos=resultado.get("grupos", []),
                           exito=exito, error=error)

@app.route("/albumes/crear", methods=["POST"])
@login_requerido
def crear_album():
    nombre = request.form.get("nombre")
    visibilidad = request.form.get("visibilidad", "AMIGOS")
    grupo_id = request.form.get("grupo_id")
    if grupo_id:
        grupo_id = int(grupo_id)
        
    ctrl = VisibilidadAlbumController()
    resultado = ctrl.crear_album(session["usuario_id"], nombre, visibilidad, grupo_id)
    if resultado["ok"]:
        return redirect(url_for("albumes", exito=resultado["mensaje"]))
    return redirect(url_for("albumes", error=resultado["mensaje"]))

@app.route("/albumes/<int:album_id>/visibilidad", methods=["POST"])
@login_requerido
def configurar_visibilidad(album_id):
    visibilidad = request.form.get("visibilidad")
    grupo_id = request.form.get("grupo_id")
    if grupo_id:
        grupo_id = int(grupo_id)
        
    ctrl = VisibilidadAlbumController()
    resultado = ctrl.configurar_visibilidad(session["usuario_id"], album_id, visibilidad, grupo_id)
    if resultado["ok"]:
        return redirect(url_for("albumes", exito=resultado["mensaje"]))
    return redirect(url_for("albumes", error=resultado["mensaje"]))

@app.route("/albumes/<int:album_id>")
@login_requerido
def ver_album(album_id):
    repo = RepositorioFoto()
    db = Persistencia().obtener_conexion()
    rows = db.execute("SELECT * FROM foto WHERE album_id = ?",
                      (album_id,)).fetchall()
    from models.entidades import Foto
    fotos = [Foto(id=r["id"], propietario=r["propietario"],
                  album_id=r["album_id"], url_imagen=r["url_imagen"],
                  fecha_subida=r["fecha_subida"]) for r in rows]
    return render_template("mis_fotos.html", fotos=fotos)


# ══════════════════════════════════════════════
# CU-13 — MODERAR COMENTARIOS
# ══════════════════════════════════════════════

@app.route("/fotos/<int:foto_id>")
@login_requerido
def detalle_foto(foto_id):
    ctrl_mod = ModerarComentarioController()
    resultado = ctrl_mod.obtener_comentarios(session["usuario_id"], foto_id)
    if not resultado["ok"]:
        return redirect(url_for("albumes"))

    ctrl_com = ComentarioController(session["usuario_id"])
    puede_comentar = ctrl_com.verificarPermiso(session["usuario_id"], foto_id)

    # Cargar nombres de autores para mostrar en template
    gestion = GestionUsuarios()
    autores = {}
    for c in resultado["comentarios"]:
        if c.autor_id not in autores:
            try:
                u = gestion.obtener_por_id(c.autor_id)
                autores[c.autor_id] = f"{u.nombre} {u.apellido}"
            except Exception:
                autores[c.autor_id] = f"Usuario #{c.autor_id}"

    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("detalle_foto.html",
                           foto=resultado["foto"],
                           comentarios=resultado["comentarios"],
                           es_propietario=resultado["es_propietario"],
                           puede_comentar=puede_comentar,
                           autores=autores,
                           exito=exito, error=error)


@app.route("/comentarios/eliminar", methods=["POST"])
@login_requerido
def eliminar_comentario():
    comentario_id = request.form.get("comentario_id")
    foto_id = request.form.get("foto_id")
    if not comentario_id or not foto_id:
        return redirect(url_for("albumes"))
    ctrl = ModerarComentarioController()
    resultado = ctrl.eliminar_comentario(
        session["usuario_id"], int(foto_id), int(comentario_id)
    )
    if resultado["ok"]:
        return redirect(url_for("detalle_foto", foto_id=foto_id,
                                exito=resultado["mensaje"]))
    return redirect(url_for("detalle_foto", foto_id=foto_id,
                            error=resultado["mensaje"]))


@app.route("/comentarios/publicar", methods=["POST"])
@login_requerido
def publicar_comentario():
    foto_id = request.form.get("foto_id")
    contenido = request.form.get("contenido", "")
    if not foto_id:
        return redirect(url_for("albumes"))
    ctrl = ComentarioController(session["usuario_id"])
    resultado = ctrl.publicarComentario(int(foto_id), contenido)
    if resultado["ok"]:
        return redirect(url_for("detalle_foto", foto_id=foto_id,
                                exito=resultado["mensaje"]))
    return redirect(url_for("detalle_foto", foto_id=foto_id,
                            error=resultado["mensaje"]))


@app.route("/comentarios/editar", methods=["POST"])
@login_requerido
def editar_comentario():
    comentario_id = request.form.get("comentario_id")
    foto_id = request.form.get("foto_id")
    nuevo_contenido = request.form.get("contenido", "")
    if not comentario_id or not foto_id:
        return redirect(url_for("albumes"))
    ctrl = ComentarioController(session["usuario_id"])
    resultado = ctrl.editarComentario(int(comentario_id), nuevo_contenido)
    if resultado["ok"]:
        return redirect(url_for("detalle_foto", foto_id=foto_id,
                                exito=resultado["mensaje"]))
    return redirect(url_for("detalle_foto", foto_id=foto_id,
                            error=resultado["mensaje"]))


@app.route("/comentarios/eliminar_autor", methods=["POST"])
@login_requerido
def eliminar_comentario_autor():
    comentario_id = request.form.get("comentario_id")
    foto_id = request.form.get("foto_id")
    if not comentario_id or not foto_id:
        return redirect(url_for("albumes"))
    ctrl = ComentarioController(session["usuario_id"])
    resultado = ctrl.eliminarComentario(int(comentario_id))
    if resultado["ok"]:
        return redirect(url_for("detalle_foto", foto_id=foto_id,
                                exito=resultado["mensaje"]))
    return redirect(url_for("detalle_foto", foto_id=foto_id,
                            error=resultado["mensaje"]))


@app.route("/fotos/demo")
@login_requerido
def agregar_foto_demo():
    """Agrega una foto de demo para el usuario actual."""
    db = Persistencia().obtener_conexion()
    db.execute("INSERT OR IGNORE INTO album (propietario, nombre, fecha_creacion) VALUES (?,?,?)",
               (session["usuario_id"], "Mi álbum", "2026-01-01"))
    db.commit()
    album_id = db.execute("SELECT id FROM album WHERE propietario=? LIMIT 1",
                          (session["usuario_id"],)).fetchone()[0]
    repo_foto = RepositorioFoto()
    foto = repo_foto.guardar(Foto(propietario=session["usuario_id"],
                                  album_id=album_id, url_imagen="mi_foto.jpg"))
    repo_com = RepositorioComentario()
    repo_com.guardar(Comentario(autor_id=session["usuario_id"],
                                foto_id=foto.id, contenido="Mi comentario de demo"))
    return redirect(url_for("albumes"))


# ══════════════════════════════════════════════
# CU-08 — GRUPOS / CU-09 — PERMISOS POR GRUPO
# ══════════════════════════════════════════════

@app.route("/grupos")
@login_requerido
def grupos():
    ctrl = GrupoController(session["usuario_id"])
    resultado = ctrl.obtenerGrupos(session["usuario_id"])
    res_amigos = ctrl.obtenerAmigosDisponibles(session["usuario_id"])
    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("grupos.html",
                           grupos=resultado.get("grupos", []),
                           amigos=res_amigos.get("amigos", []),
                           exito=exito, error=error)

@app.route("/grupos/crear", methods=["POST"])
@login_requerido
def crear_grupo():
    ids_raw = request.form.getlist("miembro_ids")
    miembros = [int(i) for i in ids_raw if i.isdigit()]
    ctrl = GrupoController(session["usuario_id"])
    resultado = ctrl.crearGrupo(request.form.get("nombre", ""), miembros)
    if resultado["ok"]:
        return redirect(url_for("grupos", exito=resultado["mensaje"]))
    return redirect(url_for("grupos", error=resultado["mensaje"]))

@app.route("/grupos/<int:grupo_id>/editar", methods=["POST"])
@login_requerido
def editar_grupo(grupo_id):
    ids_raw = request.form.getlist("miembro_ids")
    miembros = [int(i) for i in ids_raw if i.isdigit()]
    ctrl = GrupoController(session["usuario_id"])
    resultado = ctrl.editarGrupo(grupo_id, request.form.get("nombre", ""), miembros)
    if resultado["ok"]:
        return redirect(url_for("grupos", exito=resultado["mensaje"]))
    return redirect(url_for("grupos", error=resultado["mensaje"]))

@app.route("/grupos/<int:grupo_id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_grupo(grupo_id):
    ctrl = GrupoController(session["usuario_id"])
    resultado = ctrl.eliminarGrupo(grupo_id)
    if resultado["ok"]:
        return redirect(url_for("grupos", exito=resultado["mensaje"]))
    return redirect(url_for("grupos", error=resultado["mensaje"]))

@app.route("/grupos/<int:grupo_id>/permisos", methods=["POST"])
@login_requerido
def configurar_permisos(grupo_id):
    permisos_nuevos = {
        "verAlbumes": "ver_albumes" in request.form,
        "comentarFotos": "comentar_fotos" in request.form,
        "escribirMuro": "escribir_muro" in request.form,
    }
    ctrl = PermisosController()
    resultado = ctrl.guardarPermisos(session["usuario_id"], grupo_id, permisos_nuevos)
    if resultado["ok"]:
        return redirect(url_for("grupos", exito=resultado["mensaje"]))
    return redirect(url_for("grupos", error=resultado["mensaje"]))


# ══════════════════════════════════════════════
# CU-18 — DESHABILITAR USUARIO / CU-19 — MODERAR COMENTARIOS
# ══════════════════════════════════════════════

def admin_requerido(f):
    from functools import wraps
    @wraps(f)
    def decorador(*args, **kwargs):
        if not session.get("es_admin"):
            flash("Acceso denegado.", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorador

@app.route("/admin")
@login_requerido
@admin_requerido
def admin():
    ctrl = DeshabilitarUsuarioCtrl(session["usuario_id"])
    termino = request.args.get("q", "")
    usuarios = ctrl.listarUsuarios() if not termino else _buscar_para_panel(ctrl, termino)
    res_comentarios = ctrl.listar_comentarios()
    exito = request.args.get("exito")
    error = request.args.get("error")
    return render_template("admin.html",
                           usuarios=usuarios,
                           termino=termino,
                           comentarios=res_comentarios.get("comentarios", []),
                           exito=exito, error=error)

def _buscar_para_panel(ctrl, termino):
    """Usa solicitarBusqueda() (retorna un único Usuario) para el buscador del panel."""
    encontrado = ctrl.solicitarBusqueda(termino)
    return [encontrado] if encontrado else []

@app.route("/admin/deshabilitar", methods=["POST"])
@login_requerido
@admin_requerido
def deshabilitar_usuario():
    usuario_id = request.form.get("usuario_id")
    if not usuario_id or not usuario_id.isdigit():
        return redirect(url_for("admin", error="ID inválido."))
    ctrl = DeshabilitarUsuarioCtrl(session["usuario_id"])
    try:
        usuario = GestionUsuarios().obtenerUsuarioPorId(int(usuario_id))
        ctrl.deshabilitarUsuario(usuario)
        return redirect(url_for(
            "admin", exito=f"Usuario {usuario.nombre} {usuario.apellido} deshabilitado."))
    except Exception as e:
        return redirect(url_for("admin", error=str(e)))

@app.route("/admin/habilitar", methods=["POST"])
@login_requerido
@admin_requerido
def habilitar_usuario():
    usuario_id = request.form.get("usuario_id")
    if not usuario_id or not usuario_id.isdigit():
        return redirect(url_for("admin", error="ID inválido."))
    ctrl = DeshabilitarUsuarioCtrl(session["usuario_id"])
    try:
        usuario = GestionUsuarios().obtenerUsuarioPorId(int(usuario_id))
        ctrl.habilitarUsuario(usuario)
        return redirect(url_for(
            "admin", exito=f"Usuario {usuario.nombre} {usuario.apellido} habilitado."))
    except Exception as e:
        return redirect(url_for("admin", error=str(e)))

@app.route("/admin/comentario/eliminar", methods=["POST"])
@login_requerido
@admin_requerido
def admin_eliminar_comentario():
    comentario_id = request.form.get("comentario_id")
    if not comentario_id or not comentario_id.isdigit():
        return redirect(url_for("admin", error="ID de comentario inválido."))
    ctrl = DeshabilitarUsuarioCtrl(session["usuario_id"])
    resultado = ctrl.eliminar_comentario_inapropiado(int(comentario_id))
    if resultado["ok"]:
        return redirect(url_for("admin", exito=resultado["mensaje"]))
    return redirect(url_for("admin", error=resultado["mensaje"]))


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  UMBook — Servidor iniciado")
    print("  Abrí http://127.0.0.1:5000 en tu navegador")
    print("  Usuarios demo:")
    print("    vrodr@um.edu.ar  / 1234  (Valentina)")
    print("    mdiaz@um.edu.ar  / 1234  (Martín)")
    print("    lfern@um.edu.ar  / 1234  (Lucía)")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)