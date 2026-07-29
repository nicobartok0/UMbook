"""
Controlador — CU-08 Gestionar grupos de amigos
Clase: GrupoController «controller»

Nombres de método literales del diagrama de clases de diseño corregido
de CU-08 (docx "CasosDeUso-CORREGIDOS"), siguiendo la convención de
camelCase para métodos que se corresponden 1:1 con el diagrama, ya
usada por el resto de los controladores del proyecto.
"""

from models.gestion_usuarios import GestionUsuarios
from models.repositorios import RepositorioAmistad, RepositorioGrupo
from infrastructure.errores import ErrorNegocio, ErrorAcceso
from infrastructure.logger import Logger


class GrupoController:
    """
    -usuarioActualId: Integer
    -resultadoOperacion: Boolean

    El controlador se instancia por request con el id del usuario logueado
    (usuarioActualId); las operaciones de escritura (crear/editar/eliminar)
    no reciben idUsuario como parámetro porque usan ese valor interno,
    tal como muestra el diagrama de clases.
    """

    def __init__(self, usuarioActualId: int = None):
        self._usuarioActualId = usuarioActualId
        self._resultadoOperacion = None
        self._gestion = GestionUsuarios()
        self._repo_grupo = RepositorioGrupo()
        self._repo_amistad = RepositorioAmistad()
        self._logger = Logger()

    def obtenerGrupos(self, idUsuario: int) -> dict:
        """+obtenerGrupos(idUsuario: Integer): List<Grupo>"""
        try:
            grupos = self._repo_grupo.listar_de_usuario(idUsuario)
            grupos_enriquecidos = []
            for grupo in grupos:
                miembros_data = []
                for uid in grupo.miembros:
                    try:
                        miembros_data.append(self._gestion.obtenerUsuarioPorId(uid))
                    except ErrorNegocio:
                        continue
                permisos = self._repo_grupo.obtener_permisos(grupo.id)
                grupos_enriquecidos.append({
                    "grupo": grupo,
                    "miembros": miembros_data,
                    "permisos": permisos,
                })
            return {"ok": True, "grupos": grupos_enriquecidos}
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}

    def obtenerAmigosDisponibles(self, idUsuario: int) -> dict:
        """+obtenerAmigosDisponibles(idUsuario: Integer): List<Usuario>"""
        try:
            amistades = self._repo_amistad.listar_de_usuario(idUsuario)
            amigos = []
            for a in amistades:
                otro_id = (a.usuario_destino
                           if a.usuario_origen == idUsuario
                           else a.usuario_origen)
                try:
                    amigos.append(self._gestion.obtenerUsuarioPorId(otro_id))
                except ErrorNegocio:
                    continue
            return {"ok": True, "amigos": amigos}
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}

    def crearGrupo(self, nombre: str, miembros: list) -> dict:
        """
        +crearGrupo(nombre: String, miembros: List<Integer>): Boolean
        Usa self.usuarioActualId como propietario (no viene por parámetro).
        """
        try:
            idUsuario = self._usuarioActualId
            self.validarNombre(nombre)
            self.validarUnicidadNombre(nombre, idUsuario)
            miembros_validos = self._filtrarSoloAmigos(idUsuario, miembros or [])
            grupo = self._repo_grupo.crear(idUsuario, nombre)
            if miembros_validos:
                self._repo_grupo.actualizar_miembros(grupo.id, idUsuario, miembros_validos)
            self._logger.registrar(
                "CREAR_GRUPO", f"Usuario {idUsuario} creó el grupo '{nombre}'", idUsuario)
            return self.retornarResultado(True, f"Grupo '{nombre}' creado correctamente.")
        except (ErrorNegocio, ErrorAcceso) as e:
            return self.retornarResultado(False, str(e))

    def editarGrupo(self, idGrupo: int, nombre: str, miembros: list) -> dict:
        """+editarGrupo(idGrupo: Integer, nombre: String, miembros: List<Integer>): Boolean"""
        try:
            idUsuario = self._usuarioActualId
            if not self.verificarPropiedadGrupo(idGrupo, idUsuario):
                raise ErrorAcceso("No tenés permiso para editar este grupo.")
            self.validarNombre(nombre)
            self.validarUnicidadNombre(nombre, idUsuario, idGrupoExcluir=idGrupo)
            miembros_validos = self._filtrarSoloAmigos(idUsuario, miembros or [])
            self._repo_grupo.renombrar(idGrupo, idUsuario, nombre)
            self._repo_grupo.actualizar_miembros(idGrupo, idUsuario, miembros_validos)
            self._logger.registrar(
                "EDITAR_GRUPO", f"Usuario {idUsuario} editó el grupo {idGrupo}", idUsuario)
            return self.retornarResultado(True, "Grupo actualizado correctamente.")
        except (ErrorNegocio, ErrorAcceso) as e:
            return self.retornarResultado(False, str(e))

    def eliminarGrupo(self, idGrupo: int) -> dict:
        """+eliminarGrupo(idGrupo: Integer): Boolean"""
        try:
            idUsuario = self._usuarioActualId
            grupo = self._repo_grupo.obtener(idGrupo)
            nombre = grupo.nombre
            if not self.verificarPropiedadGrupo(idGrupo, idUsuario):
                raise ErrorAcceso("No tenés permiso para eliminar este grupo.")
            self._repo_grupo.eliminar(idGrupo, idUsuario)  # dispara Grupo.ejecutarEliminacionEnCascada()
            self._logger.registrar(
                "ELIMINAR_GRUPO", f"Usuario {idUsuario} eliminó grupo '{nombre}'", idUsuario)
            return self.retornarResultado(
                True, f"Grupo '{nombre}' eliminado. Sus permisos fueron removidos.")
        except (ErrorNegocio, ErrorAcceso) as e:
            return self.retornarResultado(False, str(e))

    def verificarPropiedadGrupo(self, idGrupo: int, idUsuario: int) -> bool:
        """+verificarPropiedadGrupo(idGrupo: Integer, idUsuario: Integer): Boolean"""
        grupo = self._repo_grupo.obtener(idGrupo)
        return grupo.propietario == idUsuario

    def validarNombre(self, nombre: str) -> bool:
        """Flujo alternativo: nombre de grupo vacío -> mostrar error (REV03/RE-02/REGR01)."""
        if not nombre or not nombre.strip():
            raise ErrorNegocio("El nombre del grupo es obligatorio.")
        return True

    def validarUnicidadNombre(self, nombre: str, idUsuario: int, idGrupoExcluir: int = None) -> bool:
        """
        +validarUnicidadNombre() — CU-08 análisis (REGC03/RE-06).
        No puede haber dos grupos con el mismo nombre para el mismo usuario.
        """
        if self._repo_grupo.existe_nombre(idUsuario, nombre, excluir_id=idGrupoExcluir):
            raise ErrorNegocio(f"Ya tenés un grupo llamado '{nombre}'.")
        return True

    def _filtrarSoloAmigos(self, idUsuario: int, miembros: list) -> list:
        """REGR03: los miembros del grupo deben ser únicamente amigos del propietario."""
        validos = []
        for uid in miembros:
            if uid == idUsuario:
                continue
            if self._repo_amistad.obtener_entre(idUsuario, uid) is not None:
                validos.append(uid)
        return validos

    def retornarResultado(self, ok: bool, mensaje: str = "", **extra) -> dict:
        self._resultadoOperacion = ok
        resultado = {"ok": ok, "mensaje": mensaje}
        resultado.update(extra)
        return resultado
