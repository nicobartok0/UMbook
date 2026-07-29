"""
Repositorios para Amistad, Foto y Comentario.
Responsabilidad: acceso a datos para cada entidad.
"""

from models.entidades import Amistad, Foto, Comentario, SolicitudAmistad, Album
from infrastructure.persistencia import Persistencia
from infrastructure.errores import ErrorNegocio, ErrorSistema
from datetime import datetime


class RepositorioAmistad:

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    def obtener(self, id: int) -> Amistad:
        row = self._db.execute(
            "SELECT * FROM amistad WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe la amistad con id {id}.")
        return self._fila_a_amistad(row)

    def obtener_entre(self, usuario_a: int, usuario_b: int) -> Amistad:
        row = self._db.execute(
            """SELECT * FROM amistad
               WHERE (usuario_origen=? AND usuario_destino=?)
               OR    (usuario_origen=? AND usuario_destino=?)""",
            (usuario_a, usuario_b, usuario_b, usuario_a)
        ).fetchone()
        return self._fila_a_amistad(row) if row else None

    def listar_de_usuario(self, usuario_id: int) -> list:
        rows = self._db.execute(
            """SELECT * FROM amistad
               WHERE usuario_origen=? OR usuario_destino=?""",
            (usuario_id, usuario_id)
        ).fetchall()
        return [self._fila_a_amistad(r) for r in rows]

    def guardar(self, amistad: Amistad) -> Amistad:
        try:
            cursor = self._db.execute(
                """INSERT INTO amistad (usuario_origen, usuario_destino, fecha_creacion)
                   VALUES (?,?,?)""",
                (amistad.usuario_origen, amistad.usuario_destino,
                 datetime.now().strftime("%Y-%m-%d"))
            )
            self._db.commit()
            return self.obtener(cursor.lastrowid)
        except Exception as e:
            raise ErrorSistema(f"Error al guardar amistad: {e}")

    def eliminar(self, amistad_id: int):
        try:
            self._db.execute("DELETE FROM amistad WHERE id = ?", (amistad_id,))
            self._db.commit()
        except Exception as e:
            raise ErrorSistema(f"Error al eliminar amistad: {e}")

    def _fila_a_amistad(self, row) -> Amistad:
        return Amistad(
            id=row["id"],
            usuario_origen=row["usuario_origen"],
            usuario_destino=row["usuario_destino"],
            fecha_creacion=row["fecha_creacion"]
        )


class RepositorioFoto:

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    def obtener(self, id: int) -> Foto:
        row = self._db.execute(
            "SELECT * FROM foto WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe la foto con id {id}.")
        return self._fila_a_foto(row)

    def guardar(self, foto: Foto) -> Foto:
        cursor = self._db.execute(
            """INSERT INTO foto (propietario, album_id, url_imagen, fecha_subida)
               VALUES (?,?,?,?)""",
            (foto.propietario, foto.album_id, foto.url_imagen,
             datetime.now().strftime("%Y-%m-%d"))
        )
        self._db.commit()
        return self.obtener(cursor.lastrowid)

    def _fila_a_foto(self, row) -> Foto:
        return Foto(
            id=row["id"],
            propietario=row["propietario"],
            album_id=row["album_id"],
            url_imagen=row["url_imagen"],
            fecha_subida=row["fecha_subida"]
        )


class RepositorioComentario:

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    def obtener(self, id: int) -> Comentario:
        row = self._db.execute(
            "SELECT * FROM comentario WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe el comentario con id {id}.")
        return self._fila_a_comentario(row)

    def listar_de_foto(self, foto_id: int) -> list:
        rows = self._db.execute(
            "SELECT * FROM comentario WHERE foto_id = ? ORDER BY fecha_creacion",
            (foto_id,)
        ).fetchall()
        return [self._fila_a_comentario(r) for r in rows]

    def guardar(self, comentario: Comentario) -> Comentario:
        cursor = self._db.execute(
            """INSERT INTO comentario (autor_id, foto_id, contenido, fecha_creacion)
               VALUES (?,?,?,?)""",
            (comentario.autor_id, comentario.foto_id, comentario.contenido,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self._db.commit()
        return self.obtener(cursor.lastrowid)

    def actualizar(self, comentario_id: int, nuevo_contenido: str):
        self._db.execute(
            "UPDATE comentario SET contenido = ? WHERE id = ?",
            (nuevo_contenido, comentario_id)
        )
        self._db.commit()

    def eliminar(self, comentario_id: int):
        self._db.execute("DELETE FROM comentario WHERE id = ?", (comentario_id,))
        self._db.commit()

    def _fila_a_comentario(self, row) -> Comentario:
        return Comentario(
            id=row["id"],
            autor_id=row["autor_id"],
            foto_id=row["foto_id"],
            contenido=row["contenido"],
            fecha_creacion=row["fecha_creacion"]
        )


class RepositorioAlbum:
    """Repositorio para álbumes (CU-10, CU-11)."""

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    def obtener(self, album_id):
        from models.entidades import Album
        row = self._db.execute("SELECT * FROM album WHERE id = ?", (album_id,)).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe el álbum con id {album_id}.")
        return self._fila_a_album(row)

    def listar_de_usuario(self, propietario_id):
        rows = self._db.execute(
            "SELECT * FROM album WHERE propietario = ? ORDER BY fecha_creacion DESC",
            (propietario_id,)
        ).fetchall()
        return [self._fila_a_album(r) for r in rows]

    def crear(self, propietario_id, nombre, visibilidad="AMIGOS", grupo_id=None):
        from models.entidades import Album
        if not nombre or not nombre.strip():
            raise ErrorNegocio("El nombre del álbum es obligatorio.")
        cursor = self._db.execute(
            "INSERT INTO album (propietario, nombre, fecha_creacion, visibilidad, grupo_id) VALUES (?,?,?,?,?)",
            (propietario_id, nombre.strip(), datetime.now().strftime("%Y-%m-%d"),
             visibilidad, grupo_id)
        )
        self._db.commit()
        return self.obtener(cursor.lastrowid)

    def actualizar_visibilidad(self, album_id, propietario_id, visibilidad, grupo_id=None):
        from models.entidades import Album
        album = self.obtener(album_id)
        if album.propietario != propietario_id:
            raise ErrorNegocio("No tenés permiso para modificar este álbum.")
        if visibilidad not in Album.VISIBILIDADES:
            raise ErrorNegocio(f"Visibilidad inválida: {visibilidad}.")
        if visibilidad == Album.GRUPO and not grupo_id:
            raise ErrorNegocio("Debés seleccionar un grupo para esta visibilidad.")
        self._db.execute(
            "UPDATE album SET visibilidad = ?, grupo_id = ? WHERE id = ?",
            (visibilidad, grupo_id if visibilidad == Album.GRUPO else None, album_id)
        )
        self._db.commit()

    def eliminar(self, album_id, propietario_id):
        album = self.obtener(album_id)
        if album.propietario != propietario_id:
            raise ErrorNegocio("No tenés permiso para eliminar este álbum.")
        self._db.execute("DELETE FROM foto WHERE album_id = ?", (album_id,))
        self._db.execute("DELETE FROM album WHERE id = ?", (album_id,))
        self._db.commit()

    def contar_fotos(self, album_id):
        row = self._db.execute("SELECT COUNT(*) FROM foto WHERE album_id = ?", (album_id,)).fetchone()
        return row[0]

    def _fila_a_album(self, row):
        from models.entidades import Album
        return Album(
            id=row["id"],
            propietario=row["propietario"],
            nombre=row["nombre"],
            fecha_creacion=row["fecha_creacion"],
            visibilidad=row["visibilidad"] if "visibilidad" in row.keys() else "AMIGOS",
            grupo_id=row["grupo_id"] if "grupo_id" in row.keys() else None
        )


class RepositorioGrupo:
    """
    Repositorio para Grupo y GrupoPermiso.
    Responsabilidad: acceso a datos de grupos, miembros y permisos.
    Utilizado por CU-08 (gestionar grupos) y CU-09 (configurar permisos).
    """

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    # ── Grupos ──

    def obtener(self, grupo_id: int):
        from models.entidades import Grupo
        row = self._db.execute(
            "SELECT * FROM grupo WHERE id = ?", (grupo_id,)
        ).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe el grupo con id {grupo_id}.")
        return self._fila_a_grupo(row)

    def listar_de_usuario(self, propietario_id: int) -> list:
        rows = self._db.execute(
            "SELECT * FROM grupo WHERE propietario = ? ORDER BY nombre",
            (propietario_id,)
        ).fetchall()
        return [self._fila_a_grupo(r) for r in rows]

    def crear(self, propietario_id: int, nombre: str):
        from models.entidades import Grupo
        grupo_tmp = Grupo(propietario=propietario_id, nombre=(nombre or "").strip())
        if not grupo_tmp.validarNombreNoNulo():
            raise ErrorNegocio("El nombre del grupo es obligatorio.")
        cursor = self._db.execute(
            "INSERT INTO grupo (propietario, nombre) VALUES (?, ?)",
            (propietario_id, grupo_tmp.nombre)
        )
        self._db.commit()
        # Crear fila de permisos vacía asociada al grupo
        self._db.execute(
            "INSERT INTO grupo_permiso (grupo_id) VALUES (?)",
            (cursor.lastrowid,)
        )
        self._db.commit()
        return self.obtener(cursor.lastrowid)

    def existe_nombre(self, propietario_id: int, nombre: str, excluir_id: int = None) -> bool:
        """REGC03/RE-06: existe otro grupo con el mismo nombre para este usuario."""
        query = "SELECT COUNT(*) AS c FROM grupo WHERE propietario = ? AND nombre = ?"
        params = [propietario_id, (nombre or "").strip()]
        if excluir_id is not None:
            query += " AND id != ?"
            params.append(excluir_id)
        row = self._db.execute(query, params).fetchone()
        return row["c"] > 0

    def renombrar(self, grupo_id: int, propietario_id: int, nuevo_nombre: str):
        grupo = self.obtener(grupo_id)
        if grupo.propietario != propietario_id:
            raise ErrorNegocio("No tenés permiso para editar este grupo.")
        grupo.nombre = (nuevo_nombre or "").strip()
        if not grupo.validarNombreNoNulo():
            raise ErrorNegocio("El nombre del grupo es obligatorio.")
        self._db.execute(
            "UPDATE grupo SET nombre = ? WHERE id = ?",
            (grupo.nombre, grupo_id)
        )
        self._db.commit()

    def eliminar(self, grupo_id: int, propietario_id: int):
        grupo = self.obtener(grupo_id)
        if grupo.propietario != propietario_id:
            raise ErrorNegocio("No tenés permiso para eliminar este grupo.")
        grupo.ejecutarEliminacionEnCascada()  # REGR02: responsabilidad de la entidad
        # Sin ORM con cascade nativo: el DELETE real lo hace el repositorio,
        # inmediatamente después de que la entidad "dispara" la cascada.
        self._db.execute("DELETE FROM grupo_permiso WHERE grupo_id = ?", (grupo_id,))
        self._db.execute("DELETE FROM grupo_miembro WHERE grupo_id = ?", (grupo_id,))
        self._db.execute("DELETE FROM grupo WHERE id = ?", (grupo_id,))
        self._db.commit()

    # ── Miembros ──

    def obtener_miembros_ids(self, grupo_id: int) -> list:
        rows = self._db.execute(
            "SELECT usuario_id FROM grupo_miembro WHERE grupo_id = ?", (grupo_id,)
        ).fetchall()
        return [r["usuario_id"] for r in rows]

    def actualizar_miembros(self, grupo_id: int, propietario_id: int,
                            nuevos_ids: list):
        """Reemplaza la lista de miembros del grupo con los IDs recibidos."""
        grupo = self.obtener(grupo_id)
        if grupo.propietario != propietario_id:
            raise ErrorNegocio("No tenés permiso para modificar este grupo.")
        actuales = set(grupo.miembros)
        nuevos = set(nuevos_ids or [])
        for uid in nuevos - actuales:
            grupo.agregarMiembro(uid)
        for uid in actuales - nuevos:
            grupo.quitarMiembro(uid)
        self._db.execute(
            "DELETE FROM grupo_miembro WHERE grupo_id = ?", (grupo_id,)
        )
        for uid in grupo.miembros:
            self._db.execute(
                "INSERT OR IGNORE INTO grupo_miembro (grupo_id, usuario_id) VALUES (?,?)",
                (grupo_id, uid)
            )
        self._db.commit()

    # ── Permisos ──

    def obtener_permisos(self, grupo_id: int):
        from models.entidades import GrupoPermiso
        row = self._db.execute(
            "SELECT * FROM grupo_permiso WHERE grupo_id = ?", (grupo_id,)
        ).fetchone()
        if not row:
            return GrupoPermiso(grupo_id=grupo_id)
        return GrupoPermiso(
            id=row["id"],
            grupo_id=row["grupo_id"],
            ver_albumes=bool(row["ver_albumes"]),
            comentar_fotos=bool(row["comentar_fotos"]),
            escribir_muro=bool(row["escribir_muro"])
        )

    def guardar_permisos(self, permisos):
        self._db.execute(
            """INSERT INTO grupo_permiso (grupo_id, ver_albumes, comentar_fotos, escribir_muro)
               VALUES (?,?,?,?)
               ON CONFLICT(grupo_id) DO UPDATE SET
                 ver_albumes    = excluded.ver_albumes,
                 comentar_fotos = excluded.comentar_fotos,
                 escribir_muro  = excluded.escribir_muro""",
            (permisos.grupo_id, int(permisos.ver_albumes),
             int(permisos.comentar_fotos), int(permisos.escribir_muro))
        )
        self._db.commit()
        return self.obtener_permisos(permisos.grupo_id)

    # ── Helpers ──

    def _fila_a_grupo(self, row):
        from models.entidades import Grupo
        miembros = self.obtener_miembros_ids(row["id"])
        return Grupo(
            id=row["id"],
            propietario=row["propietario"],
            nombre=row["nombre"],
            miembros=miembros
        )


class RepositorioSolicitudAmistad:
    """Repositorio para solicitudes de amistad (CU-05)."""

    def __init__(self):
        self._db = Persistencia().obtener_conexion()

    def obtener(self, id):
        row = self._db.execute("SELECT * FROM solicitud_amistad WHERE id = ?", (id,)).fetchone()
        if not row:
            raise ErrorNegocio(f"No existe la solicitud con id {id}.")
        return self._fila_a_solicitud(row)

    def obtener_entre(self, emisor_id, receptor_id):
        row = self._db.execute(
            "SELECT * FROM solicitud_amistad WHERE emisor_id = ? AND receptor_id = ? AND estado = 'PENDIENTE'",
            (emisor_id, receptor_id)
        ).fetchone()
        return self._fila_a_solicitud(row) if row else None

    def obtener_pendiente_entre(self, usuario_a, usuario_b):
        """Busca solicitud pendiente en cualquier dirección."""
        row = self._db.execute(
            """SELECT * FROM solicitud_amistad
               WHERE ((emisor_id=? AND receptor_id=?) OR (emisor_id=? AND receptor_id=?))
               AND estado = 'PENDIENTE'""",
            (usuario_a, usuario_b, usuario_b, usuario_a)
        ).fetchone()
        return self._fila_a_solicitud(row) if row else None

    def listar_recibidas(self, receptor_id):
        rows = self._db.execute(
            "SELECT * FROM solicitud_amistad WHERE receptor_id = ? AND estado = 'PENDIENTE' ORDER BY fecha_creacion DESC",
            (receptor_id,)
        ).fetchall()
        return [self._fila_a_solicitud(r) for r in rows]

    def listar_enviadas(self, emisor_id):
        rows = self._db.execute(
            "SELECT * FROM solicitud_amistad WHERE emisor_id = ? AND estado = 'PENDIENTE' ORDER BY fecha_creacion DESC",
            (emisor_id,)
        ).fetchall()
        return [self._fila_a_solicitud(r) for r in rows]

    def contar_recibidas(self, receptor_id):
        row = self._db.execute(
            "SELECT COUNT(*) FROM solicitud_amistad WHERE receptor_id = ? AND estado = 'PENDIENTE'",
            (receptor_id,)
        ).fetchone()
        return row[0]

    def guardar(self, solicitud):
        cursor = self._db.execute(
            """INSERT INTO solicitud_amistad (emisor_id, receptor_id, estado, fecha_creacion)
               VALUES (?,?,?,?)
               ON CONFLICT(emisor_id, receptor_id) DO UPDATE SET
                   estado=excluded.estado,
                   fecha_creacion=excluded.fecha_creacion
               RETURNING id""",
            (solicitud.emisor_id, solicitud.receptor_id, solicitud.estado,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        row = cursor.fetchone()
        self._db.commit()
        return self.obtener(row["id"]) if row else None

    def actualizar_estado(self, solicitud_id, nuevo_estado):
        self._db.execute(
            "UPDATE solicitud_amistad SET estado = ? WHERE id = ?",
            (nuevo_estado, solicitud_id)
        )
        self._db.commit()

    def _fila_a_solicitud(self, row):
        return SolicitudAmistad(
            id=row["id"], emisor_id=row["emisor_id"],
            receptor_id=row["receptor_id"], estado=row["estado"],
            fecha_creacion=row["fecha_creacion"]
        )