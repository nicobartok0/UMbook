"""
Controlador de Autenticación — Login
"""
from models.gestion_usuarios import GestionUsuarios
from infrastructure.seguridad import Seguridad
from infrastructure.errores import ErrorAcceso
from infrastructure.logger import Logger


class AuthController:

    def __init__(self):
        self._gestion = GestionUsuarios()
        self._seg = Seguridad()
        self._logger = Logger()

    def login(self, email: str, contrasena: str) -> dict:
        try:
            usuario = self._gestion.obtenerUsuarioPorEmail(email)
            if not usuario:
                return {"ok": False, "mensaje": "Email o contraseña incorrectos."}
            if not self._seg.verificar_contrasena(contrasena, usuario.contrasena):
                return {"ok": False, "mensaje": "Email o contraseña incorrectos."}
            # RE-UE01: el campo activo se verifica en cada intento de login;
            # si es False, el acceso se deniega de inmediato (impedirAcceso()).
            if not usuario.isActivo():
                try:
                    usuario.impedirAcceso()
                except ErrorAcceso as e:
                    self._logger.registrar("LOGIN", "DENEGADO_INACTIVO", usuario.id)
                    return {"ok": False, "mensaje": str(e)}
            self._logger.registrar("LOGIN", "EXITOSO", usuario.id)
            return {"ok": True, "usuario": usuario}
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}
