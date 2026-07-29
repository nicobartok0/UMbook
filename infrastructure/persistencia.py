"""
Persistencia
Patrón: Singleton para la conexión a la base de datos.
Responsabilidad: administrar la conexión con SQLite).
"""

import sqlite3


class Persistencia:
    """
    Clase Singleton que gestiona la conexión a la base de datos.
    """
    _instancia = None
    _conexion = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def conectar(self, ruta_bd: str = "umbook.db"):
        if self._conexion is None:
            self._conexion = sqlite3.connect(ruta_bd, check_same_thread=False)
            self._conexion.row_factory = sqlite3.Row
            self._crear_tablas()
        return self._conexion

    def _crear_tablas(self):
        cursor = self._conexion.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS usuario (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT    NOT NULL,
                apellido    TEXT    NOT NULL,
                email       TEXT    NOT NULL UNIQUE,
                contrasena  TEXT    NOT NULL,
                foto_perfil TEXT,
                fecha_nac   TEXT,
                dias_aviso  INTEGER DEFAULT 7,
                activo      INTEGER NOT NULL DEFAULT 1,
                rol         TEXT    NOT NULL DEFAULT 'USUARIO'
            );

            CREATE TABLE IF NOT EXISTS amistad (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_origen   INTEGER NOT NULL REFERENCES usuario(id),
                usuario_destino  INTEGER NOT NULL REFERENCES usuario(id),
                fecha_creacion   TEXT    NOT NULL,
                UNIQUE(usuario_origen, usuario_destino)
            );

            CREATE TABLE IF NOT EXISTS album (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                propietario  INTEGER NOT NULL REFERENCES usuario(id),
                nombre       TEXT    NOT NULL,
                fecha_creacion TEXT  NOT NULL
            );

            CREATE TABLE IF NOT EXISTS foto (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                propietario  INTEGER NOT NULL REFERENCES usuario(id),
                album_id     INTEGER NOT NULL REFERENCES album(id),
                url_imagen   TEXT    NOT NULL,
                fecha_subida TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comentario (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                autor_id       INTEGER NOT NULL REFERENCES usuario(id),
                foto_id        INTEGER NOT NULL REFERENCES foto(id),
                contenido      TEXT    NOT NULL,
                fecha_creacion TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS log_sistema (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT    NOT NULL,
                usuario_id INTEGER,
                operacion  TEXT    NOT NULL,
                resultado  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS grupo (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                propietario  INTEGER NOT NULL REFERENCES usuario(id),
                nombre       TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS grupo_miembro (
                grupo_id    INTEGER NOT NULL REFERENCES grupo(id),
                usuario_id  INTEGER NOT NULL REFERENCES usuario(id),
                PRIMARY KEY (grupo_id, usuario_id)
            );

            CREATE TABLE IF NOT EXISTS grupo_permiso (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo_id        INTEGER NOT NULL UNIQUE REFERENCES grupo(id),
                ver_albumes     INTEGER NOT NULL DEFAULT 0,
                comentar_fotos  INTEGER NOT NULL DEFAULT 0,
                escribir_muro   INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS solicitud_amistad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emisor_id INTEGER NOT NULL REFERENCES usuario(id),
                receptor_id INTEGER NOT NULL REFERENCES usuario(id),
                estado TEXT NOT NULL DEFAULT 'PENDIENTE',
                fecha_creacion TEXT NOT NULL,
                UNIQUE(emisor_id, receptor_id)
            );
        """)
        self._conexion.commit()
        # Migraciones para columnas que pueden no existir en BDs previas
        for sql in [
            "ALTER TABLE usuario ADD COLUMN activo         INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE usuario ADD COLUMN rol            TEXT    NOT NULL DEFAULT 'USUARIO'",
            "ALTER TABLE usuario ADD COLUMN sesion_version INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE usuario ADD COLUMN nombre_usuario TEXT    NOT NULL DEFAULT ''",
            "ALTER TABLE usuario ADD COLUMN fecha_registro TEXT",
            "ALTER TABLE comentario ADD COLUMN eliminado_por_admin INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE album ADD COLUMN visibilidad TEXT NOT NULL DEFAULT 'AMIGOS'",
            "ALTER TABLE album ADD COLUMN grupo_id INTEGER REFERENCES grupo(id)",
        ]:
            try:
                cursor.execute(sql)
                self._conexion.commit()
            except Exception:
                pass  # La columna ya existe

        self._migrar_activo_rol_usuario(cursor)
        self._migrar_id_grupo_permiso(cursor)

    def _migrar_activo_rol_usuario(self, cursor):
        """
        CU-18 (corrección final): el diagrama de diseño usa `activo: boolean`
        y `rol: String` en Usuario — no un enum `estado`. Si la BD viene de
        una migración intermedia (con columnas `estado` y/o `es_admin`),
        se migran los datos a `activo`/`rol` y se descartan esas columnas.
        """
        columnas = {row["name"] for row in
                    cursor.execute("PRAGMA table_info(usuario)").fetchall()}

        if "estado" in columnas:
            cursor.execute(
                "UPDATE usuario SET activo = 0 WHERE estado = 'DESHABILITADO'"
            )
            self._conexion.commit()

        if "es_admin" in columnas:
            cursor.execute(
                "UPDATE usuario SET rol = 'ADMIN' WHERE es_admin = 1"
            )
            self._conexion.commit()

        for columna in ("estado", "habilitado", "es_admin"):
            if columna in columnas:
                try:
                    cursor.execute(f"ALTER TABLE usuario DROP COLUMN {columna}")
                    self._conexion.commit()
                except Exception:
                    pass  # SQLite < 3.35 no soporta DROP COLUMN; se deja sin usar

    def _migrar_id_grupo_permiso(self, cursor):
        """
        CU-09: agrega `id` propio a grupo_permiso (antes `grupo_id` era la
        clave primaria), para que la entidad coincida con el diagrama de
        clases (Permiso.id). Reconstruye la tabla si todavía no tiene `id`.
        """
        columnas = {row["name"] for row in
                    cursor.execute("PRAGMA table_info(grupo_permiso)").fetchall()}
        if not columnas or "id" in columnas:
            return
        cursor.executescript("""
            ALTER TABLE grupo_permiso RENAME TO grupo_permiso_legado;
            CREATE TABLE grupo_permiso (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo_id        INTEGER NOT NULL UNIQUE REFERENCES grupo(id),
                ver_albumes     INTEGER NOT NULL DEFAULT 0,
                comentar_fotos  INTEGER NOT NULL DEFAULT 0,
                escribir_muro   INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO grupo_permiso (grupo_id, ver_albumes, comentar_fotos, escribir_muro)
                SELECT grupo_id, ver_albumes, comentar_fotos, escribir_muro FROM grupo_permiso_legado;
            DROP TABLE grupo_permiso_legado;
        """)
        self._conexion.commit()

    def obtener_conexion(self) -> sqlite3.Connection:
        if self._conexion is None:
            raise RuntimeError("La base de datos no está conectada.")
        return self._conexion

    def cerrar(self):
        if self._conexion:
            self._conexion.close()
            self._conexion = None