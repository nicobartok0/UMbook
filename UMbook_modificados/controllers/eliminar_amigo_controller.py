"""
Controlador — CU-06 Eliminar amigo
Responsabilidad: coordinar la eliminación de un vínculo de amistad
y la revocación de permisos asociados.
"""

from models.gestion_usuarios import GestionUsuarios
from models.repositorios import RepositorioAmistad
from infrastructure.errores import ErrorNegocio, ErrorAcceso
from infrastructure.logger import Logger


class EliminarAmigoController:
    """
    Controlador para el caso de uso CU-06 Eliminar amigo.
    Verifica la existencia de ambos usuarios, elimina el vínculo
    de forma atómica y revoca los permisos asociados.
    """

    def __init__(self):
        self._gestion_usuarios = GestionUsuarios()
        self._repo_amistad = RepositorioAmistad()
        self._logger = Logger()

    def eliminar_amigo(self, usuario_id: int, amigo_id: int) -> dict:
        """
        Flujo principal del CU-06.

        Pasos según diagrama de colaboración:
        4. Recibir solicitud de eliminación
        5. Verificar que ambos usuarios existen
        6. Confirmar usuarios
        7. Eliminar vínculo de amistad
        8. Confirmado
        9. Retornar resultado

        Args:
            usuario_id: ID del usuario que realiza la acción
            amigo_id: ID del amigo a eliminar

        Returns:
            dict con ok=True si fue exitoso, ok=False con mensaje de error
        """
        try:
            # Paso 5: Verificar que ambos usuarios existen
            self._gestion_usuarios.obtenerUsuarioPorId(usuario_id)
            self._gestion_usuarios.obtenerUsuarioPorId(amigo_id)

            # Verificar que existe el vínculo de amistad
            amistad = self._repo_amistad.obtener_entre(usuario_id, amigo_id)
            if not amistad:
                raise ErrorNegocio("No existe un vínculo de amistad entre estos usuarios.")

            # Paso 7: Eliminar el vínculo (operación atómica)
            self._repo_amistad.eliminar(amistad.id)

            # Registrar en log
            self._logger.registrar(
                "ELIMINAR_AMIGO",
                f"Usuario {usuario_id} eliminó a {amigo_id}",
                usuario_id
            )

            return {"ok": True, "mensaje": "Amigo eliminado correctamente."}

        except (ErrorNegocio, ErrorAcceso) as e:
            return {"ok": False, "mensaje": str(e)}

    def listar_amigos(self, usuario_id: int) -> dict:
        """
        Obtiene la lista de amigos de un usuario con sus datos.

        Returns:
            dict con ok=True y lista de usuarios amigos
        """
        try:
            amistades = self._repo_amistad.listar_de_usuario(usuario_id)
            amigos = []
            for amistad in amistades:
                otro_id = (amistad.usuario_destino
                           if amistad.usuario_origen == usuario_id
                           else amistad.usuario_origen)
                try:
                    amigo = self._gestion_usuarios.obtenerUsuarioPorId(otro_id)
                    amigos.append({
                        "amistad_id": amistad.id,
                        "usuario": amigo,
                        "desde": amistad.fecha_creacion
                    })
                except ErrorNegocio:
                    continue

            return {"ok": True, "amigos": amigos}

        except Exception as e:
            return {"ok": False, "mensaje": str(e)}
