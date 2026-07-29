"""
Capa de modelos — Entity: Usuario
Representa la clase de análisis/diseño Usuario «entity» / «model».
"""

from infrastructure.errores import ErrorValidacion, ErrorAcceso


class Usuario:
    """
    Entidad Usuario del sistema UMBook.
    Encapsula los datos del usuario y las reglas de validación
    de sus atributos.

    `activo` y `rol` son los atributos que exige el diagrama de clases
    de diseño de CU-18 (Deshabilitar usuario); `setActivo`/`isActivo`/
    `impedirAcceso` son los métodos literales de ese mismo diagrama.
    """

    ROL_ADMIN = "ADMIN"
    ROL_USUARIO = "USUARIO"

    def __init__(self, id: int = None, nombre: str = "", apellido: str = "",
                 email: str = "", nombre_usuario: str = "", contrasena: str = "",
                 foto_perfil: str = None, fecha_nac: str = None,
                 dias_aviso: int = 7, activo: bool = True,
                 rol: str = ROL_USUARIO, fecha_registro: str = None):
        self._id = id
        self._nombre = nombre
        self._apellido = apellido
        self._email = email
        self._nombre_usuario = nombre_usuario
        self._contrasena = contrasena
        self._foto_perfil = foto_perfil
        self._fecha_nac = fecha_nac
        self._dias_aviso = dias_aviso
        self._activo = activo if activo is not None else True
        self._rol = rol or self.ROL_USUARIO
        self._fecha_registro = fecha_registro

    # ── Getters ──
    @property
    def id(self) -> int:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def apellido(self) -> str:
        return self._apellido

    @property
    def email(self) -> str:
        return self._email

    @property
    def nombre_usuario(self) -> str:
        return self._nombre_usuario

    @property
    def contrasena(self) -> str:
        return self._contrasena

    @contrasena.setter
    def contrasena(self, valor: str):
        self._contrasena = valor

    @property
    def foto_perfil(self) -> str:
        return self._foto_perfil

    @property
    def fecha_nac(self) -> str:
        return self._fecha_nac

    @property
    def dias_aviso(self) -> int:
        return self._dias_aviso

    @property
    def rol(self) -> str:
        return self._rol

    @property
    def es_admin(self) -> bool:
        """Atajo de lectura: True si rol == ADMIN."""
        return self._rol == self.ROL_ADMIN

    @property
    def activo(self) -> bool:
        """Atajo Pythonic equivalente a isActivo(), para uso interno cómodo."""
        return self._activo

    # ── Setters con validación ──
    @nombre.setter
    def nombre(self, valor: str):
        if not valor or not valor.strip():
            raise ErrorValidacion("El nombre es obligatorio.")
        if len(valor) > 50:
            raise ErrorValidacion("El nombre no puede superar los 50 caracteres.")
        self._nombre = valor.strip()

    @apellido.setter
    def apellido(self, valor: str):
        if not valor or not valor.strip():
            raise ErrorValidacion("El apellido es obligatorio.")
        if len(valor) > 50:
            raise ErrorValidacion("El apellido no puede superar los 50 caracteres.")
        self._apellido = valor.strip()

    @nombre_usuario.setter
    def nombre_usuario(self, valor: str):
        if not valor or not valor.strip():
            raise ErrorValidacion("El nombre de usuario es obligatorio.")
        if len(valor) > 30:
            raise ErrorValidacion("El nombre de usuario no puede superar los 30 caracteres.")
        self._nombre_usuario = valor.strip()

    @email.setter
    def email(self, valor: str):
        if not valor or "@" not in valor:
            raise ErrorValidacion("El email debe tener un formato válido.")
        self._email = valor.strip().lower()

    @foto_perfil.setter
    def foto_perfil(self, valor: str):
        self._foto_perfil = valor

    @fecha_nac.setter
    def fecha_nac(self, valor: str):
        self._fecha_nac = valor

    @dias_aviso.setter
    def dias_aviso(self, valor: int):
        if valor is not None and (valor < 1 or valor > 30):
            raise ErrorValidacion("Los días de aviso deben estar entre 1 y 30.")
        self._dias_aviso = valor

    # ══════════════════════════════════════════════
    # CU-18 — Deshabilitar usuario (métodos literales del diagrama de diseño)
    # ══════════════════════════════════════════════

    def setActivo(self, estado: bool):
        """+setActivo(estado: boolean): void"""
        self._activo = bool(estado)

    def isActivo(self) -> bool:
        """+isActivo(): boolean"""
        return self._activo

    def impedirAcceso(self):
        """
        +impedirAcceso(): void
        RE-UE01: se invoca desde el login cuando isActivo() es False.
        Representa la denegación de acceso; no muta estado.
        """
        raise ErrorAcceso(
            "Tu cuenta está deshabilitada. Contactá a un administrador.")

    @property
    def fecha_registro(self) -> str:
        return self._fecha_registro

    def __repr__(self) -> str:
        return f"Usuario(id={self._id}, nombre={self._nombre}, email={self._email})"
