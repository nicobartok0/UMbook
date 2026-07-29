"""
Controlador de Registro — CU-01
Clase: RegistroController «controller»
"""
from datetime import date
from models.usuario import Usuario
from models.gestion_usuarios import GestionUsuarios
from infrastructure.seguridad import Seguridad
from infrastructure.errores import ErrorValidacion, ErrorNegocio
from infrastructure.logger import Logger


class RegistroController:

    def __init__(self):
        self._gestion = GestionUsuarios()
        self._seg = Seguridad()
        self._logger = Logger()

    def registrarUsuario(self, datos: dict) -> dict:
        try:
            self.validarDatos(datos)
            self.verificarEmailUnico(datos["email"])
            self.verificarUsuarioUnico(datos["nombre_usuario"])
            usuario = self.crearCuenta(datos)
            self._logger.registrar("REGISTRO", "EXITOSO", usuario.id)
            return self.retornarResultado(True, usuario=usuario)
        except (ErrorValidacion, ErrorNegocio) as e:
            return self.retornarResultado(False, str(e))

    def validarDatos(self, datos: dict) -> bool:
        if not datos.get("nombre") or not datos.get("apellido"):
            raise ErrorValidacion("Nombre y apellido son obligatorios.")
        if not datos.get("email") or "@" not in datos["email"]:
            raise ErrorValidacion("Email inválido.")
        if not datos.get("nombre_usuario") or not datos["nombre_usuario"].strip():
            raise ErrorValidacion("El nombre de usuario es obligatorio.")
        if not datos.get("contrasena") or len(datos["contrasena"]) < 6:
            raise ErrorValidacion("La contraseña debe tener al menos 6 caracteres.")
        return True

    def verificarEmailUnico(self, email: str) -> bool:
        if not self._gestion.email_disponible(email):
            raise ErrorNegocio("El email ya está registrado.")
        return True

    def verificarUsuarioUnico(self, usr: str) -> bool:
        if not self._gestion.nombre_usuario_disponible(usr):
            raise ErrorNegocio("El nombre de usuario ya está en uso.")
        return True

    def crearCuenta(self, datos: dict) -> Usuario:
        hash_pwd = self._seg.hashear_contrasena(datos["contrasena"])
        usuario = Usuario(
            nombre=datos["nombre"],
            apellido=datos["apellido"],
            email=datos["email"],
            nombre_usuario=datos["nombre_usuario"],
            contrasena=hash_pwd,
            fecha_registro=date.today().isoformat()
        )
        return self._gestion.guardarUsuario(usuario)

    def retornarResultado(self, ok: bool, mensaje: str = "", usuario=None) -> dict:
        resultado = {"ok": ok, "mensaje": mensaje}
        if usuario is not None:
            resultado["usuario"] = usuario
        return resultado
