import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.persistencia import Persistencia
from infrastructure.seguridad import Seguridad
from models.gestion_usuarios import GestionUsuarios
from models.repositorios import RepositorioAmistad, RepositorioFoto, RepositorioComentario
from models.usuario import Usuario
from models.entidades import Amistad, Foto, Comentario
from controllers.perfil_controller import PerfilController
from controllers.eliminar_amigo_controller import EliminarAmigoController
from controllers.moderar_comentario_controller import ModerarComentarioController
from controllers.solicitud_amistad_controller import SolicitudAmistadController
from controllers.sugerencias_amigos_controller import SugerenciasAmigosController
from controllers.visibilidad_album_controller import VisibilidadAlbumController


def setup():
    """Inicializa base de datos en memoria para pruebas."""
    Persistencia().conectar(":memory:")

    seg = Seguridad()
    gestion = GestionUsuarios()
    db = Persistencia().obtener_conexion()

    # Crear usuarios de prueba
    u1 = Usuario(nombre="Juan", apellido="Pérez", email="juan@test.com",
                 contrasena=seg.hashear_contrasena("pass123"))
    u2 = Usuario(nombre="María", apellido="García", email="maria@test.com",
                 contrasena=seg.hashear_contrasena("pass123"))
    u3 = Usuario(nombre="Pedro", apellido="López", email="pedro@test.com",
                 contrasena=seg.hashear_contrasena("pass123"))

    u1 = gestion.guardarUsuario(u1)
    u2 = gestion.guardarUsuario(u2)
    u3 = gestion.guardarUsuario(u3)

    # Crear amistad entre u1 y u2
    repo_amistad = RepositorioAmistad()
    amistad = repo_amistad.guardar(Amistad(usuario_origen=u1.id, usuario_destino=u2.id))

    # Crear álbum, foto y comentario para CU-13
    db.execute("INSERT INTO album (propietario, nombre, fecha_creacion) VALUES (?,?,?)",
               (u1.id, "Mis fotos", "2026-01-01"))
    db.commit()
    album_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    repo_foto = RepositorioFoto()
    foto = repo_foto.guardar(Foto(propietario=u1.id, album_id=album_id, url_imagen="foto1.jpg"))

    repo_com = RepositorioComentario()
    comentario = repo_com.guardar(Comentario(autor_id=u2.id, foto_id=foto.id, contenido="Qué linda foto!"))

    return {
        "u1_id": u1.id, "u2_id": u2.id, "u3_id": u3.id,
        "amistad_id": amistad.id,
        "foto_id": foto.id,
        "comentario_id": comentario.id
    }


def test_cu02_editar_perfil_exitoso(ids):
    ctrl = PerfilController()
    resultado = ctrl.editar_perfil(ids["u1_id"], {
        "nombre": "Juan Actualizado",
        "email": "juan_nuevo@test.com",
        "dias_aviso": 3
    })
    assert resultado["ok"] == True, f"Esperaba ok=True, obtuvo: {resultado}"
    assert resultado["usuario"].nombre == "Juan Actualizado"
    print("  ✓ CU-02 CP-01: Edición exitosa del perfil")


def test_cu02_email_duplicado(ids):
    ctrl = PerfilController()
    resultado = ctrl.editar_perfil(ids["u1_id"], {
        "email": "maria@test.com"  # Email de u2
    })
    assert resultado["ok"] == False
    assert "email" in resultado["mensaje"].lower()
    print("  ✓ CU-02 CP-02: Email duplicado rechazado correctamente")


def test_cu02_nombre_vacio(ids):
    ctrl = PerfilController()
    resultado = ctrl.editar_perfil(ids["u1_id"], {"nombre": ""})
    assert resultado["ok"] == False
    print("  ✓ CU-02 CP-03: Nombre vacío rechazado correctamente")


def test_cu02_foto_formato_invalido(ids):
    ctrl = PerfilController()
    resultado = ctrl.editar_perfil(ids["u1_id"], {"foto_perfil": "foto.pdf"})
    assert resultado["ok"] == False
    assert "jpg" in resultado["mensaje"].lower() or "png" in resultado["mensaje"].lower()
    print("  ✓ CU-02 CP-04: Formato de foto inválido rechazado")


def test_cu02_dias_aviso_fuera_rango(ids):
    ctrl = PerfilController()
    resultado = ctrl.editar_perfil(ids["u1_id"], {"dias_aviso": 0})
    assert resultado["ok"] == False
    print("  ✓ CU-02 CP-05: Días de aviso fuera de rango rechazado")


def test_cu06_eliminar_amigo_exitoso(ids):
    ctrl = EliminarAmigoController()
    resultado = ctrl.eliminar_amigo(ids["u1_id"], ids["u2_id"])
    assert resultado["ok"] == True
    print("  ✓ CU-06 CP-01: Eliminación de amigo exitosa")


def test_cu06_eliminar_sin_amistad(ids):
    ctrl = EliminarAmigoController()
    resultado = ctrl.eliminar_amigo(ids["u1_id"], ids["u3_id"])
    assert resultado["ok"] == False
    print("  ✓ CU-06 CP-02: Eliminación sin vínculo rechazada correctamente")


def test_cu13_eliminar_comentario_propietario(ids):
    ctrl = ModerarComentarioController()
    resultado = ctrl.eliminar_comentario(
        ids["u1_id"], ids["foto_id"], ids["comentario_id"]
    )
    assert resultado["ok"] == True
    print("  ✓ CU-13 CP-01: Eliminación de comentario por propietario exitosa")


def test_cu13_eliminar_no_propietario(ids):
    # Recrear comentario porque el anterior fue eliminado
    repo_com = RepositorioComentario()
    nuevo_comentario = repo_com.guardar(
        Comentario(autor_id=ids["u2_id"], foto_id=ids["foto_id"], contenido="Otro comentario")
    )
    ctrl = ModerarComentarioController()
    resultado = ctrl.eliminar_comentario(
        ids["u2_id"],  # u2 NO es propietario de la foto
        ids["foto_id"],
        nuevo_comentario.id
    )
    assert resultado["ok"] == False
    assert resultado.get("acceso_denegado") == True
    print("  ✓ CU-13 CP-02: Acceso denegado a no propietario correctamente")


def test_cu13_obtener_comentarios(ids):
    ctrl = ModerarComentarioController()
    resultado = ctrl.obtener_comentarios(ids["u1_id"], ids["foto_id"])
    assert resultado["ok"] == True
    assert resultado["es_propietario"] == True
    print("  ✓ CU-13 CP-03: Obtención de comentarios con flag propietario correcto")


def test_cu05_enviar_y_aceptar_solicitud(ids):
    ctrl = SolicitudAmistadController()
    # u2 envía a u3
    res1 = ctrl.enviar_solicitud(ids["u2_id"], ids["u3_id"])
    assert res1["ok"] == True
    # u3 acepta
    pendientes = ctrl.listar_recibidas(ids["u3_id"])
    sol_id = pendientes["solicitudes"][0]["solicitud"].id
    res2 = ctrl.aceptar_solicitud(ids["u3_id"], sol_id)
    assert res2["ok"] == True
    print("  ✓ CU-05: Enviar y aceptar solicitud de amistad")

def test_cu07_sugerencias_amigos():
    # Setup específico para >2 amigos en común
    gestion = GestionUsuarios()
    u_a = gestion.guardarUsuario(Usuario(nombre="A", apellido="A", email="a@a.com", contrasena="1"))
    u_b = gestion.guardarUsuario(Usuario(nombre="B", apellido="B", email="b@b.com", contrasena="1"))
    u_c = gestion.guardarUsuario(Usuario(nombre="C", apellido="C", email="c@c.com", contrasena="1"))
    u_d = gestion.guardarUsuario(Usuario(nombre="D", apellido="D", email="d@d.com", contrasena="1"))
    u_e = gestion.guardarUsuario(Usuario(nombre="E", apellido="E", email="e@e.com", contrasena="1"))
    
    repo_am = RepositorioAmistad()
    # a es amigo de c, d, e
    repo_am.guardar(Amistad(usuario_origen=u_a.id, usuario_destino=u_c.id))
    repo_am.guardar(Amistad(usuario_origen=u_a.id, usuario_destino=u_d.id))
    repo_am.guardar(Amistad(usuario_origen=u_a.id, usuario_destino=u_e.id))
    # b es amigo de c, d, e (3 amigos en común con A)
    repo_am.guardar(Amistad(usuario_origen=u_b.id, usuario_destino=u_c.id))
    repo_am.guardar(Amistad(usuario_origen=u_b.id, usuario_destino=u_d.id))
    repo_am.guardar(Amistad(usuario_origen=u_b.id, usuario_destino=u_e.id))
    
    ctrl = SugerenciasAmigosController()
    res = ctrl.obtener_sugerencias(u_a.id)
    assert res["ok"] == True
    # Debería sugerir a B porque tienen 3 en común
    assert len(res["sugerencias"]) == 1
    assert res["sugerencias"][0]["usuario"].id == u_b.id
    assert res["sugerencias"][0]["amigos_en_comun"] == 3
    print("  ✓ CU-07: Sugerir amigos con >2 en común")

def test_cu11_configurar_visibilidad(ids):
    ctrl = VisibilidadAlbumController()
    res1 = ctrl.crear_album(ids["u1_id"], "Nuevo Album", "SOLO_YO")
    assert res1["ok"] == True
    album_id = res1["album"].id
    
    res2 = ctrl.configurar_visibilidad(ids["u1_id"], album_id, "TODOS")
    assert res2["ok"] == True
    
    res3 = ctrl.configurar_visibilidad(ids["u1_id"], album_id, "INVÁLIDO")
    assert res3["ok"] == False
    print("  ✓ CU-11: Crear álbum y cambiar visibilidad")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PRUEBAS AUTOMATIZADAS — UMBook")
    print("="*60)

    ids = setup()

    print("\n  CU-02 Editar perfil:")
    test_cu02_editar_perfil_exitoso(ids)
    test_cu02_email_duplicado(ids)
    test_cu02_nombre_vacio(ids)
    test_cu02_foto_formato_invalido(ids)
    test_cu02_dias_aviso_fuera_rango(ids)

    print("\n  CU-06 Eliminar amigo:")
    test_cu06_eliminar_amigo_exitoso(ids)
    test_cu06_eliminar_sin_amistad(ids)

    print("\n  CU-13 Moderar comentarios:")
    test_cu13_eliminar_comentario_propietario(ids)
    test_cu13_eliminar_no_propietario(ids)
    test_cu13_obtener_comentarios(ids)
    
    print("\n  Nuevos Casos de Uso (CU-05, CU-07, CU-11):")
    test_cu05_enviar_y_aceptar_solicitud(ids)
    test_cu07_sugerencias_amigos()
    test_cu11_configurar_visibilidad(ids)

    print("\n" + "="*60)
    print("  TODAS LAS PRUEBAS PASARON ✓")
    print("="*60 + "\n")
