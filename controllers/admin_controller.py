"""
Controlador — CU-18 Deshabilitar usuario / CU-19 Eliminar comentario inapropiado
Clase: DeshabilitarUsuarioCtrl «control»

Nombre de clase y métodos literales del diagrama de clases de diseño
corregido (docx "CasosDeUso-CORREGIDOS"). Comparte panel con CU-19
(moderación de comentarios), que no forma parte de este diagrama pero
usa el mismo control de acceso administrador.
"""

from models.usuario import Usuario
from models.gestion_usuarios import GestionUsuarios
from models.repositorios import RepositorioComentario
from infrastructure.persistencia import Persistencia
from infrastructure.errores import ErrorNegocio, ErrorAcceso
from infrastructure.logger import Logger


class DeshabilitarUsuarioCtrl:
    """
    Controlador para el panel de administración.
    Todas las operaciones validan verificarRolAdmin() antes de ejecutar
    cualquier acción (REDC01).
    """

    def __init__(self, idAdminActual: int = None):
        self._idAdminActual = idAdminActual
        self._gestor = GestionUsuarios()  # rol «GestorUsuario» del diagrama
        self._repo_comentario = RepositorioComentario()
        self._db = Persistencia().obtener_conexion()
        self._logger = Logger()

    def verificarRolAdmin(self) -> bool:
        """
        +verificarRolAdmin(): boolean — REDC01.
        READ01: el rol se verifica a nivel de sistema (consulta a BD),
        no solo por el parámetro de sesión recibido.
        """
        if not self._idAdminActual:
            return False
        row = self._db.execute(
            "SELECT rol FROM usuario WHERE id = ?", (self._idAdminActual,)
        ).fetchone()
        return bool(row) and row["rol"] == Usuario.ROL_ADMIN

    def solicitarBusqueda(self, criterio: str) -> Usuario:
        """
        +solicitarBusqueda(criterio: String): Usuario
        Busca por email exacto si el criterio contiene '@'; si no,
        por coincidencia parcial de nombre/apellido (primer resultado).
        """
        criterio = (criterio or "").strip()
        if not criterio:
            return None
        if "@" in criterio:
            return self._gestor.obtenerUsuarioPorEmail(criterio)
        resultados = self._gestor.buscarPorNombreApellido(criterio)
        return resultados[0] if resultados else None

    def listarUsuarios(self) -> list:
        """Alimenta PanelAdminView.mostrarListadoUsuarios() (listado inicial)."""
        return self._gestor.buscarPorNombreApellido("")

    def deshabilitarUsuario(self, usuario: Usuario) -> bool:
        """
        +deshabilitarUsuario(usuario: Usuario): boolean — flujo principal CU-18.
        REDC02: valida que el usuario exista.
        READ02: un administrador no puede deshabilitar su propia cuenta.
        REDC04: si algo falla, no se aplica ningún cambio parcial (se
        valida todo antes de mutar y persistir).
        """
        if not self.verificarRolAdmin():
            raise ErrorAcceso("Solo un administrador puede deshabilitar cuentas.")
        if not usuario:
            raise ErrorNegocio("El usuario a deshabilitar no existe.")
        if usuario.id == self._idAdminActual:
            raise ErrorAcceso("No podés deshabilitar tu propia cuenta.")
        if not usuario.isActivo():
            raise ErrorNegocio("El usuario ya se encuentra deshabilitado.")

        usuario.setActivo(False)
        self._gestor.actualizarUsuario(usuario)
        self._invalidarSesiones(usuario)
        self._logger.registrar(
            "DESHABILITAR_USUARIO",
            f"Admin {self._idAdminActual} deshabilitó al usuario {usuario.id} "
            f"({usuario.nombre} {usuario.apellido})",
            self._idAdminActual
        )
        return True

    def habilitarUsuario(self, usuario: Usuario) -> bool:
        """
        Reactiva una cuenta (REUE03: un administrador puede volver a
        habilitar una cuenta deshabilitada en cualquier momento).
        No forma parte del diagrama de clases de CU-18 explícitamente,
        pero sí del diagrama de estados (transición "habilita/reactiva").
        """
        if not self.verificarRolAdmin():
            raise ErrorAcceso("Solo un administrador puede habilitar cuentas.")
        if not usuario:
            raise ErrorNegocio("El usuario no existe.")
        if usuario.isActivo():
            raise ErrorNegocio("El usuario ya está activo.")

        usuario.setActivo(True)
        self._gestor.actualizarUsuario(usuario)
        self._logger.registrar(
            "HABILITAR_USUARIO",
            f"Admin {self._idAdminActual} habilitó al usuario {usuario.id}",
            self._idAdminActual
        )
        return True

    def _invalidarSesiones(self, usuario: Usuario):
        """
        -invalidarSesiones(usuario): void — REDC03.
        Incrementa `sesion_version`; cualquier sesión Flask abierta con la
        versión anterior queda invalidada en el próximo request
        (ver hook `before_request` en app.py).
        """
        self._db.execute(
            "UPDATE usuario SET sesion_version = sesion_version + 1 WHERE id = ?",
            (usuario.id,)
        )
        self._db.commit()

    # ══════════════════════════════════════════════
    # CU-19 — Eliminar comentario inapropiado (comparte panel de administración)
    # ══════════════════════════════════════════════

    def listar_comentarios(self) -> dict:
        """Devuelve todos los comentarios del sistema para moderación (CU-19)."""
        try:
            if not self.verificarRolAdmin():
                raise ErrorAcceso("Acceso denegado: se requieren permisos de administrador.")
            rows = self._db.execute(
                """SELECT c.id, c.contenido, c.fecha_creacion,
                          u.nombre || ' ' || u.apellido AS autor,
                          f.id AS foto_id
                   FROM comentario c
                   JOIN usuario u ON u.id = c.autor_id
                   JOIN foto f    ON f.id = c.foto_id
                   ORDER BY c.fecha_creacion DESC"""
            ).fetchall()
            return {"ok": True, "comentarios": [dict(r) for r in rows]}
        except (ErrorAcceso, ErrorNegocio) as e:
            return {"ok": False, "mensaje": str(e)}

    def eliminar_comentario_inapropiado(self, comentario_id: int) -> dict:
        """Flujo principal CU-19: elimina un comentario inapropiado y deja un aviso."""
        try:
            if not self.verificarRolAdmin():
                raise ErrorAcceso("Acceso denegado: se requieren permisos de administrador.")
            row = self._db.execute(
                "SELECT id FROM comentario WHERE id = ?", (comentario_id,)
            ).fetchone()
            if not row:
                raise ErrorNegocio("El comentario no existe.")

            aviso = "[Este comentario fue eliminado por un administrador]"
            self._db.execute(
                "UPDATE comentario SET contenido = ?, eliminado_por_admin = 1 WHERE id = ?",
                (aviso, comentario_id)
            )
            self._db.commit()
            self._logger.registrar(
                "ELIMINAR_COMENTARIO_ADMIN",
                f"Admin {self._idAdminActual} eliminó comentario {comentario_id}",
                self._idAdminActual
            )
            return {"ok": True, "mensaje": "Comentario eliminado correctamente."}
        except (ErrorAcceso, ErrorNegocio) as e:
            return {"ok": False, "mensaje": str(e)}
