"""
Capa general de la aplicación — Gestión de Usuarios.
Responsabilidad: operaciones CRUD sobre la entidad Usuario.
"""

from models.usuario import Usuario
from infrastructure.persistencia import Persistencia
from infrastructure.errores import ErrorNegocio, ErrorSistema


class GestionUsuarios:
    """
    Servicio general para gestionar usuarios.
    Es usado por: Registro y Autenticación, Gestión de Amigos,
    Álbumes y Fotos, Administración.

    Realiza el rol de «GestorUsuario» del diagrama de clases de diseño
    de CU-18 (Deshabilitar usuario). Los métodos `obtenerUsuarioPorId`,
    `obtenerUsuarioPorEmail`, `buscarPorNombreApellido`, `guardarUsuario`
    y `actualizarUsuario` son la traducción literal de ese diagrama;
    se implementan como alias de los métodos ya usados por el resto de
    los casos de uso del sistema (`obtener_por_id`, `guardar`, etc.)
    para no romper ninguna otra funcionalidad.
    """

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    def obtener_por_id(self, usuario_id: int) -> Usuario:
        row = self._db.execute(
            "SELECT * FROM usuario WHERE id = ?", (usuario_id,)
        ).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe el usuario con id {usuario_id}.")
        return self._fila_a_usuario(row)

    def obtener_por_email(self, email: str) -> Usuario:
        row = self._db.execute(
            "SELECT * FROM usuario WHERE email = ?", (email.lower(),)
        ).fetchone()
        if not row:
            return None
        return self._fila_a_usuario(row)

    def email_disponible(self, email: str, excluir_id: int = None) -> bool:
        """Verifica que el email no esté registrado por otro usuario."""
        if excluir_id:
            row = self._db.execute(
                "SELECT id FROM usuario WHERE email = ? AND id != ?",
                (email.lower(), excluir_id)
            ).fetchone()
        else:
            row = self._db.execute(
                "SELECT id FROM usuario WHERE email = ?", (email.lower(),)
            ).fetchone()
        return row is None

    def buscarPorNombreApellido(self, termino: str) -> list:
        """
        +buscarPorNombreApellido(criterio): List<Usuario> — CU-18 diseño.
        Busca usuarios activos por nombre o apellido (búsqueda parcial).
        Con `termino` vacío devuelve todos los usuarios activos (se usa
        también para poblar el listado inicial del panel de administración).
        """
        t = f"%{(termino or '').strip()}%"
        rows = self._db.execute(
            """SELECT * FROM usuario
               WHERE (nombre LIKE ? OR apellido LIKE ?)
               AND activo = 1""",
            (t, t)
        ).fetchall()
        return [self._fila_a_usuario(r) for r in rows]

    def nombre_usuario_disponible(self, nombre_usuario: str, excluir_id: int = None) -> bool:
        """Verifica que el nombre de usuario no esté registrado por otro usuario."""
        if excluir_id:
            row = self._db.execute(
                "SELECT id FROM usuario WHERE nombre_usuario = ? AND id != ?",
                (nombre_usuario.strip(), excluir_id)
            ).fetchone()
        else:
            row = self._db.execute(
                "SELECT id FROM usuario WHERE nombre_usuario = ?", (nombre_usuario.strip(),)
            ).fetchone()
        return row is None

    def guardar(self, usuario: Usuario) -> Usuario:
        try:
            cursor = self._db.execute(
                """INSERT INTO usuario (nombre, apellido, email, nombre_usuario,
                   contrasena, foto_perfil, fecha_nac, dias_aviso, activo, rol, fecha_registro)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (usuario.nombre, usuario.apellido, usuario.email,
                 usuario.nombre_usuario, usuario.contrasena,
                 usuario.foto_perfil, usuario.fecha_nac,
                 usuario.dias_aviso, int(usuario.activo), usuario.rol,
                 usuario.fecha_registro)
            )
            self._db.commit()
            return self.obtener_por_id(cursor.lastrowid)
        except Exception as e:
            raise ErrorSistema(f"Error al guardar usuario: {e}")

    def actualizar(self, usuario: Usuario):
        """
        Actualiza los datos editables del perfil (CU-02) *y* el estado
        activo/rol si fueron modificados en el objeto en memoria (p. ej.
        por DeshabilitarUsuarioCtrl.deshabilitarUsuario() vía setActivo()).
        """
        try:
            self._db.execute(
                """UPDATE usuario SET nombre=?, apellido=?, email=?,
                   foto_perfil=?, fecha_nac=?, dias_aviso=?, activo=?
                   WHERE id=?""",
                (usuario.nombre, usuario.apellido, usuario.email,
                 usuario.foto_perfil, usuario.fecha_nac, usuario.dias_aviso,
                 int(usuario.activo), usuario.id)
            )
            self._db.commit()
        except Exception as e:
            raise ErrorSistema(f"Error al actualizar usuario: {e}")

    # ══════════════════════════════════════════════
    # Alias literales — «GestorUsuario» (CU-18 diagrama de clases de diseño)
    # ══════════════════════════════════════════════

    def obtenerUsuarioPorId(self, id: int) -> Usuario:
        return self.obtener_por_id(id)

    def obtenerUsuarioPorEmail(self, email: str) -> Usuario:
        return self.obtener_por_email(email)

    def guardarUsuario(self, u: Usuario) -> Usuario:
        return self.guardar(u)

    def actualizarUsuario(self, u: Usuario):
        return self.actualizar(u)

    def _fila_a_usuario(self, row) -> Usuario:
        return Usuario(
            id=row["id"],
            nombre=row["nombre"],
            apellido=row["apellido"],
            email=row["email"],
            nombre_usuario=row["nombre_usuario"] or "",
            contrasena=row["contrasena"],
            foto_perfil=row["foto_perfil"],
            fecha_nac=row["fecha_nac"],
            dias_aviso=row["dias_aviso"],
            activo=bool(row["activo"]) if "activo" in row.keys() else True,
            rol=row["rol"] if "rol" in row.keys() else Usuario.ROL_USUARIO,
            fecha_registro=row["fecha_registro"] if "fecha_registro" in row.keys() else None
        )
