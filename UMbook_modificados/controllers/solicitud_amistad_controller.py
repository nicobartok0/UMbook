"""
CU-05 — Responder solicitud de amistad
Permite enviar, aceptar y rechazar solicitudes de amistad.
"""

from models.gestion_usuarios import GestionUsuarios
from models.repositorios import RepositorioAmistad, RepositorioSolicitudAmistad
from models.entidades import Amistad, SolicitudAmistad
from infrastructure.errores import ErrorValidacion, ErrorNegocio, ErrorAcceso
from infrastructure.logger import Logger


class SolicitudAmistadController:

    def __init__(self):
        self._gestion = GestionUsuarios()
        self._repo_solicitud = RepositorioSolicitudAmistad()
        self._repo_amistad = RepositorioAmistad()
        self._logger = Logger()

    def enviar_solicitud(self, emisor_id: int, receptor_id: int) -> dict:
        try:
            if emisor_id == receptor_id:
                return {"ok": False, "mensaje": "No podés enviarte una solicitud a vos mismo."}

            # Verificar que ambos usuarios existen
            self._gestion.obtenerUsuarioPorId(emisor_id)
            self._gestion.obtenerUsuarioPorId(receptor_id)

            # Verificar que no son ya amigos
            amistad = self._repo_amistad.obtener_entre(emisor_id, receptor_id)
            if amistad:
                return {"ok": False, "mensaje": "Ya son amigos."}

            # Verificar que no existe solicitud pendiente en ninguna dirección
            pendiente = self._repo_solicitud.obtener_pendiente_entre(emisor_id, receptor_id)
            if pendiente:
                return {"ok": False, "mensaje": "Ya existe una solicitud pendiente."}

            solicitud = SolicitudAmistad(emisor_id=emisor_id, receptor_id=receptor_id)
            self._repo_solicitud.guardar(solicitud)
            self._logger.registrar("ENVIAR_SOLICITUD", "OK", emisor_id)
            return {"ok": True, "mensaje": "Solicitud de amistad enviada."}

        except (ErrorValidacion, ErrorNegocio) as e:
            return {"ok": False, "mensaje": str(e)}
        except Exception as e:
            return {"ok": False, "mensaje": f"Error al enviar solicitud: {e}"}

    def aceptar_solicitud(self, receptor_id: int, solicitud_id: int) -> dict:
        try:
            solicitud = self._repo_solicitud.obtener(solicitud_id)

            if solicitud.receptor_id != receptor_id:
                return {"ok": False, "mensaje": "No tenés permiso para responder esta solicitud."}

            if solicitud.estado != SolicitudAmistad.PENDIENTE:
                return {"ok": False, "mensaje": "Esta solicitud ya fue respondida."}

            # Crear amistad bidireccional
            self._repo_amistad.guardar(
                Amistad(usuario_origen=solicitud.emisor_id, usuario_destino=solicitud.receptor_id)
            )

            # Actualizar estado
            self._repo_solicitud.actualizar_estado(solicitud_id, SolicitudAmistad.ACEPTADA)
            self._logger.registrar("ACEPTAR_SOLICITUD", "OK", receptor_id)
            return {"ok": True, "mensaje": "Solicitud aceptada. ¡Ahora son amigos!"}

        except (ErrorValidacion, ErrorNegocio) as e:
            return {"ok": False, "mensaje": str(e)}
        except Exception as e:
            return {"ok": False, "mensaje": f"Error al aceptar solicitud: {e}"}

    def rechazar_solicitud(self, receptor_id: int, solicitud_id: int) -> dict:
        try:
            solicitud = self._repo_solicitud.obtener(solicitud_id)

            if solicitud.receptor_id != receptor_id:
                return {"ok": False, "mensaje": "No tenés permiso para responder esta solicitud."}

            if solicitud.estado != SolicitudAmistad.PENDIENTE:
                return {"ok": False, "mensaje": "Esta solicitud ya fue respondida."}

            self._repo_solicitud.actualizar_estado(solicitud_id, SolicitudAmistad.RECHAZADA)
            self._logger.registrar("RECHAZAR_SOLICITUD", "OK", receptor_id)
            return {"ok": True, "mensaje": "Solicitud rechazada."}

        except (ErrorValidacion, ErrorNegocio) as e:
            return {"ok": False, "mensaje": str(e)}
        except Exception as e:
            return {"ok": False, "mensaje": f"Error al rechazar solicitud: {e}"}

    def listar_recibidas(self, usuario_id: int) -> dict:
        try:
            solicitudes = self._repo_solicitud.listar_recibidas(usuario_id)
            resultado = []
            for s in solicitudes:
                emisor = self._gestion.obtenerUsuarioPorId(s.emisor_id)
                resultado.append({"solicitud": s, "emisor": emisor})
            return {"ok": True, "solicitudes": resultado}
        except Exception as e:
            return {"ok": False, "mensaje": str(e), "solicitudes": []}

    def contar_pendientes(self, usuario_id: int) -> int:
        try:
            return self._repo_solicitud.contar_recibidas(usuario_id)
        except Exception:
            return 0
