"""
Capa de modelos — Entities: Amistad, Foto, Comentario
"""

from datetime import datetime


class Amistad:
    """
    Representa el vínculo de amistad entre dos usuarios.
    """

    def __init__(self, id: int = None, usuario_origen: int = None,
                 usuario_destino: int = None, fecha_creacion: str = None):
        self._id = id
        self._usuario_origen = usuario_origen
        self._usuario_destino = usuario_destino
        self._fecha_creacion = fecha_creacion or datetime.now().strftime("%Y-%m-%d")

    @property
    def id(self) -> int:
        return self._id

    @property
    def usuario_origen(self) -> int:
        return self._usuario_origen

    @property
    def usuario_destino(self) -> int:
        return self._usuario_destino

    @property
    def fecha_creacion(self) -> str:
        return self._fecha_creacion

    def involucra(self, usuario_id: int) -> bool:
        """Indica si un usuario participa en esta amistad."""
        return self._usuario_origen == usuario_id or self._usuario_destino == usuario_id

    def __repr__(self) -> str:
        return f"Amistad(id={self._id}, origen={self._usuario_origen}, destino={self._usuario_destino})"


class Album:
    """Representa un álbum de fotos con configuración de visibilidad (CU-11)."""
    SOLO_YO = "SOLO_YO"
    AMIGOS = "AMIGOS"
    GRUPO = "GRUPO"
    TODOS = "TODOS"
    VISIBILIDADES = [SOLO_YO, AMIGOS, GRUPO, TODOS]

    def __init__(self, id=None, propietario=None, nombre="",
                 fecha_creacion=None, visibilidad="AMIGOS", grupo_id=None):
        self._id = id
        self._propietario = propietario
        self._nombre = nombre
        self._fecha_creacion = fecha_creacion or datetime.now().strftime("%Y-%m-%d")
        self._visibilidad = visibilidad
        self._grupo_id = grupo_id

    @property
    def id(self): return self._id
    @property
    def propietario(self): return self._propietario
    @property
    def nombre(self): return self._nombre
    @nombre.setter
    def nombre(self, valor): self._nombre = valor.strip() if valor else ""
    @property
    def fecha_creacion(self): return self._fecha_creacion
    @property
    def visibilidad(self): return self._visibilidad
    @visibilidad.setter
    def visibilidad(self, valor):
        if valor not in self.VISIBILIDADES:
            from infrastructure.errores import ErrorValidacion
            raise ErrorValidacion(f"Visibilidad inválida: {valor}. Opciones: {', '.join(self.VISIBILIDADES)}")
        self._visibilidad = valor
    @property
    def grupo_id(self): return self._grupo_id
    @grupo_id.setter
    def grupo_id(self, valor): self._grupo_id = valor

    def es_propietario(self, usuario_id):
        return self._propietario == usuario_id

    def __repr__(self):
        return f"Album(id={self._id}, nombre={self._nombre}, visibilidad={self._visibilidad})"


class Foto:
    """
    Representa una foto subida por un usuario en un álbum.
    """

    def __init__(self, id: int = None, propietario: int = None,
                 album_id: int = None, url_imagen: str = "",
                 fecha_subida: str = None):
        self._id = id
        self._propietario = propietario
        self._album_id = album_id
        self._url_imagen = url_imagen
        self._fecha_subida = fecha_subida or datetime.now().strftime("%Y-%m-%d")

    @property
    def id(self) -> int:
        return self._id

    @property
    def propietario(self) -> int:
        return self._propietario

    @property
    def album_id(self) -> int:
        return self._album_id

    @property
    def url_imagen(self) -> str:
        return self._url_imagen

    @property
    def fecha_subida(self) -> str:
        return self._fecha_subida

    def es_propietario(self, usuario_id: int) -> bool:
        """Verifica si un usuario es dueño de esta foto."""
        return self._propietario == usuario_id

    def tienePermiso(self, idUsuario: int) -> bool:
        """Verifica si el usuario es dueño de la foto. La verificación completa de grupos queda en el controller."""
        return self._propietario == idUsuario

    def __repr__(self) -> str:
        return f"Foto(id={self._id}, propietario={self._propietario})"


class Comentario:
    """
    Representa un comentario publicado en una foto.
    Incluye soporte para moderación por parte del propietario (CU-13)
    y del administrador (CU-19).
    """

    def __init__(self, id: int = None, autor_id: int = None,
                 foto_id: int = None, contenido: str = "",
                 fecha_creacion: str = None,
                 eliminado_por_admin: bool = False,
                 aviso_eliminacion: str = None):
        self._id = id
        self._autor_id = autor_id
        self._foto_id = foto_id
        self._contenido = contenido
        self._fecha_creacion = fecha_creacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # RE-CO03: registra si fue eliminado por administrador (CU-19)
        self._eliminado_por_admin = eliminado_por_admin
        # Aviso visible para todos cuando el admin elimina (CU-19)
        self._aviso_eliminacion = aviso_eliminacion

    @property
    def id(self) -> int:
        return self._id

    @property
    def autor_id(self) -> int:
        return self._autor_id

    @property
    def foto_id(self) -> int:
        return self._foto_id

    @property
    def contenido(self) -> str:
        return self._contenido

    @property
    def fecha_creacion(self) -> str:
        return self._fecha_creacion

    @property
    def eliminado_por_admin(self) -> bool:
        return self._eliminado_por_admin

    @eliminado_por_admin.setter
    def eliminado_por_admin(self, valor: bool):
        self._eliminado_por_admin = valor

    @property
    def aviso_eliminacion(self) -> str:
        return self._aviso_eliminacion

    @aviso_eliminacion.setter
    def aviso_eliminacion(self, valor: str):
        self._aviso_eliminacion = valor

    def editar(self, texto: str):
        """Actualiza el contenido en memoria. El controller persiste con el repo."""
        self._contenido = texto.strip()

    def eliminar(self):
        """Marca la intención de eliminar. El controller ejecuta la eliminación física vía repo."""
        pass

    def texto_visible(self) -> str:
        """Retorna el texto a mostrar: aviso si fue eliminado por admin, contenido si no."""
        if self._eliminado_por_admin and self._aviso_eliminacion:
            return self._aviso_eliminacion
        return self._contenido

    def __repr__(self) -> str:
        return f"Comentario(id={self._id}, autor={self._autor_id}, foto={self._foto_id})"


class Grupo:
    """
    Representa un grupo de amigos creado por un usuario (CU-08).
    El propietario puede asignarle miembros y configurar sus permisos (CU-09).
    """

    def __init__(self, id: int = None, propietario: int = None, nombre: str = "",
                 miembros: list = None):
        self._id = id
        self._propietario = propietario
        self._nombre = nombre
        self._miembros = miembros or []   # lista de usuario_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def propietario(self) -> int:
        return self._propietario

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        self._nombre = valor.strip() if valor else valor

    @property
    def miembros(self) -> list:
        return list(self._miembros)

    def agregarMiembro(self, idUsuario: int):
        """+agregarMiembro(idUsuario: Integer): void — CU-08 diseño."""
        if idUsuario not in self._miembros:
            self._miembros.append(idUsuario)

    def quitarMiembro(self, idUsuario: int):
        """+quitarMiembro(idUsuario: Integer): void — CU-08 diseño."""
        self._miembros = [m for m in self._miembros if m != idUsuario]

    def validarNombreNoNulo(self) -> bool:
        """
        +validarNombreNoNulo(): Boolean — CU-08 diseño / REGR01.
        El nombre del grupo no puede ser nulo ni vacío.
        """
        return bool(self._nombre and self._nombre.strip())

    def ejecutarEliminacionEnCascada(self):
        """
        +ejecutarEliminacionEnCascada(): void — CU-08 diseño / REGR02.
        Es responsabilidad de esta entidad disparar la eliminación en
        cascada de sus GrupoPermiso asociados. Como el proyecto no usa
        un ORM con cascade nativo, este método documenta la intención;
        RepositorioGrupo.eliminar() ejecuta el DELETE real inmediatamente
        después de esta llamada.
        """
        pass

    def __repr__(self) -> str:
        return f"Grupo(id={self._id}, nombre={self._nombre}, propietario={self._propietario})"


class GrupoPermiso:
    """
    Representa los permisos configurados para un grupo (CU-09).
    Define qué acciones pueden realizar los miembros del grupo
    en el sitio del propietario.
    """

    def __init__(self, id: int = None, grupo_id: int = None, ver_albumes: bool = False,
                 comentar_fotos: bool = False, escribir_muro: bool = False):
        self._id = id
        self._grupo_id = grupo_id
        self._ver_albumes = ver_albumes
        self._comentar_fotos = comentar_fotos
        self._escribir_muro = escribir_muro

    @property
    def id(self) -> int:
        return self._id

    @property
    def grupo_id(self) -> int:
        return self._grupo_id

    @property
    def ver_albumes(self) -> bool:
        return self._ver_albumes

    @ver_albumes.setter
    def ver_albumes(self, valor: bool):
        self._ver_albumes = valor

    @property
    def comentar_fotos(self) -> bool:
        return self._comentar_fotos

    @comentar_fotos.setter
    def comentar_fotos(self, valor: bool):
        self._comentar_fotos = valor

    @property
    def escribir_muro(self) -> bool:
        return self._escribir_muro

    @escribir_muro.setter
    def escribir_muro(self, valor: bool):
        self._escribir_muro = valor

    def actualizarPermisos(self, ver: bool, comentar: bool, escribir: bool):
        """+actualizarPermisos(ver, comentar, escribir): void — CU-09 diseño."""
        self._ver_albumes = bool(ver)
        self._comentar_fotos = bool(comentar)
        self._escribir_muro = bool(escribir)

    def tienePermisosActivos(self) -> bool:
        """
        +tienePermisosActivos(): Boolean — CU-09 diseño / REGP02, RE-03, RE-05.
        Impide que la configuración se guarde con los 3 permisos en False.
        """
        return self._ver_albumes or self._comentar_fotos or self._escribir_muro

    def __repr__(self) -> str:
        return (f"GrupoPermiso(grupo={self._grupo_id}, "
                f"ver={self._ver_albumes}, comentar={self._comentar_fotos}, "
                f"muro={self._escribir_muro})")


class SolicitudAmistad:
    """Representa una solicitud de amistad entre dos usuarios (CU-05)."""
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"

    def __init__(self, id=None, emisor_id=None, receptor_id=None,
                 estado="PENDIENTE", fecha_creacion=None):
        self._id = id
        self._emisor_id = emisor_id
        self._receptor_id = receptor_id
        self._estado = estado
        self._fecha_creacion = fecha_creacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def id(self): return self._id
    @property
    def emisor_id(self): return self._emisor_id
    @property
    def receptor_id(self): return self._receptor_id
    @property
    def estado(self): return self._estado
    @estado.setter
    def estado(self, valor): self._estado = valor
    @property
    def fecha_creacion(self): return self._fecha_creacion

    def __repr__(self):
        return f"SolicitudAmistad(id={self._id}, emisor={self._emisor_id}, receptor={self._receptor_id}, estado={self._estado})"