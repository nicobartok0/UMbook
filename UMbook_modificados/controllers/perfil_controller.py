"""
Controlador — CU-02 Editar perfil
Responsabilidad: coordinar la edición del perfil del usuario.
Implementa el flujo del CU-02 según el diagrama de colaboración.
"""

from models.usuario import Usuario
from models.gestion_usuarios import GestionUsuarios
from infrastructure.errores import ErrorValidacion, ErrorNegocio
from infrastructure.logger import Logger


class PerfilController:
    """
    Controlador para el caso de uso CU-02 Editar perfil.
    Recibe datos del formulario, valida, verifica unicidad del email
    y coordina la actualización en el modelo.
    """

    EXTENSIONES_FOTO = (".jpg", ".jpeg", ".png")
    TAMANO_MAX_FOTO_MB = 5

    def __init__(self):
        self._gestion_usuarios = GestionUsuarios()
        self._logger = Logger()

    def editar_perfil(self, usuario_id: int, datos: dict) -> dict:
        """
        Flujo principal del CU-02.

        Pasos según diagrama de colaboración:
        3. Recibir datos del formulario
        4. Validar datos
        5. Actualizar perfil en la entidad
        6. Retornar resultado

        Args:
            usuario_id: ID del usuario autenticado
            datos: dict con nombre, apellido, email, foto_perfil,
                   fecha_nac, dias_aviso

        Returns:
            dict con ok=True y el usuario actualizado, o ok=False y mensaje de error
        """
        try:
            # Paso 4: Validar datos
            self._validar_datos(datos, usuario_id)

            # Obtener el usuario actual
            usuario = self._gestion_usuarios.obtenerUsuarioPorId(usuario_id)

            # Aplicar los cambios al modelo (usando setters con validación)
            if "nombre" in datos:
                usuario.nombre = datos["nombre"]
            if "apellido" in datos:
                usuario.apellido = datos["apellido"]
            if "email" in datos:
                usuario.email = datos["email"]
            if "foto_perfil" in datos:
                usuario.foto_perfil = datos["foto_perfil"]
            if "fecha_nac" in datos:
                usuario.fecha_nac = datos["fecha_nac"]
            if "dias_aviso" in datos:
                usuario.dias_aviso = datos["dias_aviso"]

            # Paso 5: Persistir los cambios
            self._gestion_usuarios.actualizarUsuario(usuario)

            # Registrar en log
            self._logger.registrar("EDITAR_PERFIL", "EXITOSO", usuario_id)

            return {"ok": True, "usuario": usuario, "mensaje": "Perfil actualizado correctamente."}

        except (ErrorValidacion, ErrorNegocio) as e:
            return {"ok": False, "mensaje": str(e)}

    def _validar_datos(self, datos: dict, usuario_id: int):
        """
        Valida formato de campos y unicidad del email.
        """
        if "nombre" in datos and not datos["nombre"].strip():
            raise ErrorValidacion("El nombre es obligatorio.")

        if "apellido" in datos and not datos["apellido"].strip():
            raise ErrorValidacion("El apellido es obligatorio.")

        if "email" in datos:
            email = datos["email"].strip()
            if "@" not in email:
                raise ErrorValidacion("El email debe tener un formato válido.")
            # Verificar unicidad del email (RE-02)
            if not self._gestion_usuarios.email_disponible(email, excluir_id=usuario_id):
                raise ErrorNegocio("El email ya está registrado por otro usuario.")

        if "foto_perfil" in datos and datos["foto_perfil"]:
            tamano = datos.get("foto_perfil_bytes")
            self._validar_foto(datos["foto_perfil"], tamano_bytes=tamano)

        if "dias_aviso" in datos and datos["dias_aviso"] is not None:
            dias = datos["dias_aviso"]
            if not isinstance(dias, int) or dias < 1 or dias > 30:
                raise ErrorValidacion("Los días de aviso deben ser un número entero entre 1 y 30.")

    def _validar_foto(self, nombre_archivo: str, tamano_bytes: int = None):
        """
        Valida formato y tamaño de la foto de perfil.
        RE-03: JPG o PNG, máximo 5MB.
        """
        if not any(nombre_archivo.lower().endswith(ext) for ext in self.EXTENSIONES_FOTO):
            raise ErrorValidacion("La foto debe ser JPG o PNG.")
        if tamano_bytes is not None and tamano_bytes > self.TAMANO_MAX_FOTO_MB * 1024 * 1024:
            raise ErrorValidacion(f"La foto no puede superar los {self.TAMANO_MAX_FOTO_MB}MB.")
