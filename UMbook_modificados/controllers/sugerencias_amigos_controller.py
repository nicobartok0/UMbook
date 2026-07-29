"""
CU-07 — Ver sugerencias de amigos
Sugiere amigos basándose en amigos en común.
Solo muestra usuarios con más de 2 amigos en común (estrictamente mayor).
"""

from models.gestion_usuarios import GestionUsuarios
from models.repositorios import RepositorioAmistad
from infrastructure.errores import ErrorNegocio


class SugerenciasAmigosController:

    def __init__(self):
        self._gestion = GestionUsuarios()
        self._repo_amistad = RepositorioAmistad()

    def obtener_sugerencias(self, usuario_id: int) -> dict:
        """Obtiene sugerencias de amigos con más de 2 amigos en común."""
        try:
            # Obtener IDs de amigos del usuario
            amistades = self._repo_amistad.listar_de_usuario(usuario_id)
            amigos_ids = set()
            for a in amistades:
                otro = a.usuario_destino if a.usuario_origen == usuario_id else a.usuario_origen
                amigos_ids.add(otro)

            if not amigos_ids:
                return {"ok": True, "sugerencias": []}

            # Para cada amigo, obtener sus amigos (amigos de amigos)
            candidatos = {}  # {usuario_id: set(amigos_en_comun)}
            for amigo_id in amigos_ids:
                amistades_amigo = self._repo_amistad.listar_de_usuario(amigo_id)
                for a in amistades_amigo:
                    otro = a.usuario_destino if a.usuario_origen == amigo_id else a.usuario_origen
                    # Excluir al propio usuario y a los que ya son amigos
                    if otro == usuario_id or otro in amigos_ids:
                        continue
                    if otro not in candidatos:
                        candidatos[otro] = set()
                    candidatos[otro].add(amigo_id)

            # Filtrar: solo los que tienen más de 2 amigos en común (>2, es decir 3+)
            sugerencias = []
            for candidato_id, amigos_comunes in candidatos.items():
                if len(amigos_comunes) > 2:
                    try:
                        usuario = self._gestion.obtenerUsuarioPorId(candidato_id)
                        sugerencias.append({
                            "usuario": usuario,
                            "amigos_en_comun": len(amigos_comunes)
                        })
                    except Exception:
                        continue

            # Ordenar por cantidad de amigos en común (descendente)
            sugerencias.sort(key=lambda x: x["amigos_en_comun"], reverse=True)
            return {"ok": True, "sugerencias": sugerencias}

        except Exception as e:
            return {"ok": False, "mensaje": f"Error al obtener sugerencias: {e}", "sugerencias": []}
