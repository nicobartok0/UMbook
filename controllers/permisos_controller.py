"""
Controlador — CU-09 Configurar permisos por grupo
Clase: PermisosController «control»

Clase separada de GrupoController (CU-08), tal como indica el diagrama
de clases de diseño corregido. Nombres de método literales del diagrama.
"""

from models.repositorios import RepositorioGrupo
from infrastructure.errores import ErrorNegocio, ErrorAcceso
from infrastructure.logger import Logger


class PermisosController:
    """
    -grupoTarget: Grupo
    -permisosNuevos: GrupoPermiso
    -resultadoOperacion: Boolean
    """

    def __init__(self):
        self._grupoTarget = None
        self._permisosNuevos = None
        self._resultadoOperacion = None
        self._repo_grupo = RepositorioGrupo()
        self._logger = Logger()

    def obtenerGrupos(self, idUsuario: int) -> dict:
        """
        +obtenerGrupos(idUsuario): List<GrupoDTO>
        Flujo alternativo: si el usuario no tiene grupos, se debe
        redirigir a CU-08 (Crear Grupo) — lo señala `sin_grupos`.
        """
        try:
            grupos = self._repo_grupo.listar_de_usuario(idUsuario)
            if not grupos:
                return {"ok": True, "grupos": [], "sin_grupos": True}
            grupos_dto = []
            for grupo in grupos:
                permisos = self._repo_grupo.obtener_permisos(grupo.id)
                grupos_dto.append({"grupo": grupo, "permisos": permisos})
            return {"ok": True, "grupos": grupos_dto, "sin_grupos": False}
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}

    def guardarPermisos(self, idUsuario: int, idGrupo: int,
                         permisosNuevos: dict) -> dict:
        """
        +guardarPermisos(idUsuario, idGrupo, permisosNuevos): boolean
        permisosNuevos: {"verAlbumes": bool, "comentarFotos": bool, "escribirMuro": bool}
        """
        if not self._verificarPropiedad(idUsuario, idGrupo):
            # REPC02: rechazar sin invocar la capa de persistencia (403)
            return self.retornarResultado(False, "No tenés permiso sobre este grupo.",
                                           codigo=403)

        if not self._validarPermisosNoNulos(permisosNuevos):
            return self.retornarResultado(
                False, "Tenés que habilitar al menos un permiso para el grupo.")

        # Transacción atómica (REPC03): se arma la entidad completa en memoria
        # y se persiste en una sola operación; si falla, no queda nada a medias.
        try:
            permisos = self._repo_grupo.obtener_permisos(idGrupo)
            permisos.actualizarPermisos(
                permisosNuevos.get("verAlbumes", False),
                permisosNuevos.get("comentarFotos", False),
                permisosNuevos.get("escribirMuro", False),
            )
            self._permisosNuevos = permisos
            self._repo_grupo.guardar_permisos(permisos)
            self._logger.registrar(
                "CONFIGURAR_PERMISOS",
                f"Usuario {idUsuario} configuró permisos del grupo {idGrupo}",
                idUsuario
            )
            return self.retornarResultado(True, "Permisos guardados correctamente.")
        except Exception as e:
            return self.retornarResultado(False, f"No se pudo guardar: {e}")

    def _verificarPropiedad(self, idUsuario: int, idGrupo: int) -> bool:
        """-verificarPropiedad(idUsuario, idGrupo): boolean"""
        try:
            grupo = self._repo_grupo.obtener(idGrupo)
        except ErrorNegocio:
            return False
        self._grupoTarget = grupo
        return grupo.propietario == idUsuario  # getIdPropietario() implícito vía `propietario`

    def _validarPermisosNoNulos(self, permisos: dict) -> bool:
        """
        -validarPermisosNoNulos(permisos): boolean — REGP02/RE-03/RE-05.
        Delegado en GrupoPermiso.tienePermisosActivos() (la entidad valida
        su propio invariante, no el controlador).
        """
        from models.entidades import GrupoPermiso
        tmp = GrupoPermiso(
            ver_albumes=permisos.get("verAlbumes", False),
            comentar_fotos=permisos.get("comentarFotos", False),
            escribir_muro=permisos.get("escribirMuro", False),
        )
        return tmp.tienePermisosActivos()

    def retornarResultado(self, ok: bool, mensaje: str = "", **extra) -> dict:
        self._resultadoOperacion = ok
        resultado = {"ok": ok, "mensaje": mensaje}
        resultado.update(extra)
        return resultado
