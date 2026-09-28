from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class Arista:
    desde: str
    hasta: str
    peso: str = ""
    dirigida: bool = False


class Grafo:
    """Modelo simple de grafo para las vistas de Grafos."""

    def __init__(self, vertices: Iterable[str] | None = None):
        self.vertices: list[str] = []
        self.aristas: list[Arista] = []

        for vertice in vertices or []:
            self.agregar_vertice(vertice)

    def limpiar(self) -> None:
        self.vertices.clear()
        self.aristas.clear()

    def copiar(self) -> "Grafo":
        nuevo = Grafo(self.vertices)
        nuevo.aristas = list(self.aristas)
        return nuevo

    def agregar_vertice(self, nombre: str) -> bool:
        nombre = str(nombre).strip()
        if not nombre or nombre in self.vertices:
            return False
        self.vertices.append(nombre)
        return True

    def eliminar_vertice(self, nombre: str) -> bool:
        if nombre not in self.vertices:
            return False
        self.vertices.remove(nombre)
        self.aristas = [
            e for e in self.aristas
            if e.desde != nombre and e.hasta != nombre
        ]
        return True

    def agregar_arista(
        self,
        desde: str,
        hasta: str,
        peso: str = "",
        dirigida: bool = False,
    ) -> bool:
        desde = str(desde).strip()
        hasta = str(hasta).strip()
        peso = str(peso).strip()

        if not desde or not hasta:
            return False

        self.agregar_vertice(desde)
        self.agregar_vertice(hasta)

        nueva = Arista(desde, hasta, peso, dirigida)
        if self.contiene_arista(nueva):
            return False

        self.aristas.append(nueva)
        return True

    def eliminar_arista(self, desde: str, hasta: str) -> bool:
        for indice, arista in enumerate(self.aristas):
            if self._aristas_equivalentes_extremos(arista, desde, hasta):
                del self.aristas[indice]
                return True
        return False

    def contiene_arista(self, nueva: Arista) -> bool:
        return any(self.aristas_equivalentes(arista, nueva) for arista in self.aristas)

    @staticmethod
    def aristas_equivalentes(a: Arista, b: Arista) -> bool:
        if a.dirigida != b.dirigida:
            return False
        if str(a.peso) != str(b.peso):
            return False

        if a.dirigida:
            return a.desde == b.desde and a.hasta == b.hasta

        return {
            a.desde, a.hasta
        } == {
            b.desde, b.hasta}

    @staticmethod
    def _aristas_equivalentes_extremos(
        arista: Arista,
        desde: str,
        hasta: str,
    ) -> bool:
        if arista.dirigida:
            return arista.desde == desde and arista.hasta == hasta
        return (
            {arista.desde, arista.hasta}
            == {desde, hasta}
        )

    def vecinos(self, vertice: str) -> list[str]:
        vecinos: list[str] = []
        for arista in self.aristas:
            if arista.desde == vertice:
                vecinos.append(arista.hasta)
            elif not arista.dirigida and arista.hasta == vertice:
                vecinos.append(arista.desde)
        return list(dict.fromkeys(vecinos))

    def es_conexo(self) -> bool:
        """Conectividad considerando las aristas sin dirección."""
        if not self.vertices:
            return True

        visitados = {self.vertices[0]}
        pendientes = [self.vertices[0]]

        while pendientes:
            actual = pendientes.pop()
            for vecino in self._vecinos_no_dirigidos(actual):
                if vecino not in visitados:
                    visitados.add(vecino)
                    pendientes.append(vecino)

        return len(visitados) == len(self.vertices)

    def _vecinos_no_dirigidos(self, vertice: str) -> list[str]:
        vecinos: list[str] = []
        for arista in self.aristas:
            if arista.desde == vertice:
                vecinos.append(arista.hasta)
            elif arista.hasta == vertice:
                vecinos.append(arista.desde)
        return list(dict.fromkeys(vecinos))

    def a_dict(self) -> dict:
        return {
            "vertices": list(self.vertices),
            "aristas": [asdict(arista) for arista in self.aristas],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Grafo":
        if not isinstance(data, dict):
            raise ValueError("Datos de grafo inválidos.")

        grafo = cls()
        vertices = data.get("vertices", [])
        aristas = data.get("aristas", [])

        if not isinstance(vertices, list) or not isinstance(aristas, list):
            raise ValueError("La estructura del grafo no es válida.")

        for vertice in vertices:
            if not grafo.agregar_vertice(str(vertice)):
                raise ValueError("Hay vértices repetidos o vacíos.")

        for arista in aristas:
            if not isinstance(arista, dict):
                raise ValueError("Una arista del archivo no es válida.")

            if not grafo.agregar_arista(
                arista.get("desde", ""),
                arista.get("hasta", ""),
                arista.get("peso", ""),
                bool(arista.get("dirigida", False)),
            ):
                raise ValueError("No fue posible cargar una arista.")

        return grafo
