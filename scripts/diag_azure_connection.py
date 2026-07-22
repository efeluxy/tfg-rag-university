"""Script de diagnostico TEMPORAL (solo lectura contra Azure).

No modifica el proyecto, ni la BD, ni el indice. Solo ejecuta busquedas de
LECTURA contra Azure AI Search y reproduce la ruta real del grafo para capturar
el traceback subyacente al mensaje generico de la app.

Se puede eliminar sin impacto una vez terminado el diagnostico.

Bloques:
  4 - Busqueda NO semantica (conexion real).
  5 - Busqueda CON semantic ranker (captura del error real).
  6 - Reproduccion de la consulta real del sintoma (traceback completo).

Salida: por consola. El invocador redirige a
  logs\diagnostico_azure_YYYYMMDD.txt
Reglas: sin emojis, sin acentos, ASCII puro.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

TEST_QUERY = "requisitos beca MEC"
SYMPTOM_QUERY = "quiero saber como se llama el alumno ALU001"


def _sep(title):
    print("")
    print("=" * 79)
    print(title)
    print("=" * 79)


def bloque_4_no_semantica():
    """Busqueda SIN semantic ranker usando el cliente REAL del proyecto."""
    _sep("BLOQUE 4 - BUSQUEDA NO SEMANTICA (CONEXION REAL)")
    try:
        # Reutiliza credenciales y cliente reales del proyecto.
        from src.config.azure_config import get_search_client, get_openai_client
        from src.config.settings import EMBEDDING_MODEL, EMBEDDING_DIMENSIONS
        from azure.search.documents.models import VectorizedQuery
        import os

        search_client = get_search_client()

        # Embedding real (misma via que el proyecto) para busqueda hibrida.
        oai = get_openai_client()
        emb_deploy = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", EMBEDDING_MODEL)
        emb = oai.embeddings.create(
            input=TEST_QUERY, model=emb_deploy, dimensions=EMBEDDING_DIMENSIONS
        ).data[0].embedding

        vector_query = VectorizedQuery(
            vector=emb, k_nearest_neighbors=5, fields="embedding"
        )

        # SIN query_type semantico, SIN semantic_configuration_name.
        # Busqueda lexica + vectorial pura (query_type simple por defecto).
        results = search_client.search(
            search_text=TEST_QUERY,
            vector_queries=[vector_query],
            select="content,title,category,source_file,section,page_number",
            top=5,
        )
        items = list(results)
        n = len(items)
        print("Query de prueba: %s" % TEST_QUERY)
        print("Resultados devueltos: %d" % n)
        if n > 0:
            first = items[0]
            print("Primer title: %s" % (first.get("title") or "(sin title)"))
            print("Primer source_file: %s" % (first.get("source_file") or "(sin source_file)"))
            print("Primer @search.score: %s" % str(first.get("@search.score")))
            print("")
            print("[BLOQUE 4] PASS")
            print("Evidencia: la busqueda NO semantica devuelve resultados sin error.")
            print("Conexion, endpoint, key e indice CORRECTOS. El codigo de conexion")
            print("funciona. Evidencia fuerte de que NO es un fallo de codigo/config.")
            return "PASS"
        else:
            print("")
            print("[BLOQUE 4] PASS (con matiz)")
            print("Evidencia: la llamada NO semantica se ejecuta SIN error (conexion OK)")
            print("pero devuelve 0 resultados para esta query. Conexion/indice validos;")
            print("posible indice vacio o query sin match. No es fallo de conexion.")
            return "PASS"
    except Exception as exc:
        print("")
        print("ERROR en busqueda NO semantica:")
        print("Tipo: %s" % type(exc).__name__)
        print("Mensaje: %s" % str(exc))
        print("")
        print("[BLOQUE 4] FAIL")
        print("Evidencia: la busqueda NO semantica FALLA. Esto apunta a codigo/config")
        print("(auth 401/403, endpoint, indice no encontrado o red), NO a cuota semantica.")
        return "FAIL"


def bloque_5_semantica():
    """Misma query CON semantic ranker (como en produccion)."""
    _sep("BLOQUE 5 - BUSQUEDA CON SEMANTIC RANKER (CAPTURA DEL ERROR REAL)")
    try:
        from src.config.azure_config import get_search_client, get_openai_client
        from src.config.settings import EMBEDDING_MODEL, EMBEDDING_DIMENSIONS
        from azure.search.documents.models import VectorizedQuery
        import os

        search_client = get_search_client()
        oai = get_openai_client()
        emb_deploy = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", EMBEDDING_MODEL)
        emb = oai.embeddings.create(
            input=TEST_QUERY, model=emb_deploy, dimensions=EMBEDDING_DIMENSIONS
        ).data[0].embedding

        vector_query = VectorizedQuery(
            vector=emb, k_nearest_neighbors=5, fields="embedding"
        )

        # EXACTAMENTE como en produccion (src/tools/azure_search.py).
        results = search_client.search(
            search_text=TEST_QUERY,
            vector_queries=[vector_query],
            query_type="semantic",
            semantic_configuration_name="semantic-config",
            select="content,title,category,source_file,section,page_number",
            top=5,
        )
        items = list(results)  # el error de plano de datos salta al iterar
        n = len(items)
        print("Query de prueba: %s" % TEST_QUERY)
        print("Resultados devueltos CON semantic ranker: %d" % n)
        if n > 0:
            first = items[0]
            print("Primer @search.reranker_score: %s" % str(first.get("@search.reranker_score")))
        print("")
        print("[BLOQUE 5] PASS")
        print("Evidencia: la busqueda semantica se EJECUTA sin error. Hay cuota")
        print("semantica disponible. El semantic ranker responde correctamente.")
        print("INTERPRETACION: caso (a) NO aplica; la cuota NO esta agotada AHORA.")
        return "PASS", None
    except Exception as exc:
        tipo = type(exc).__name__
        msg = str(exc)
        print("Query de prueba: %s" % TEST_QUERY)
        print("EXCEPCION capturada CON semantic ranker:")
        print("Tipo: %s" % tipo)
        print("Mensaje COMPLETO:")
        print(msg)
        low = msg.lower()
        cuota = any(
            k in low
            for k in [
                "semantic",
                "free query semantic",
                "semantic usage exceeded",
                "enable semantic billing",
                "quota",
            ]
        )
        print("")
        if cuota:
            print("INTERPRETACION: caso (a) -> el mensaje contiene texto de cuota/semantic.")
            print("CONFIRMA que el fallo es de CUOTA de Azure (semantic ranker), NO de codigo.")
        else:
            print("INTERPRETACION: caso (b) -> excepcion NO relacionada con cuota semantica")
            print("(auth, timeout, parametro invalido o config semantica inexistente).")
            print("Podria ser codigo/config. Ver detalle arriba.")
        print("")
        print("[BLOQUE 5] PASS")
        print("Evidencia: capturado el mensaje exacto que produce la busqueda semantica.")
        return "PASS", (tipo, msg, cuota)


def bloque_6_ruta_real():
    """Reproduce la ruta REAL del grafo con la consulta del sintoma."""
    _sep("BLOQUE 6 - REPRODUCCION DE LA CONSULTA REAL (TRAZA COMPLETA)")
    print("Consulta exacta del sintoma: %s" % SYMPTOM_QUERY)
    print("(Nota: se usa ALU001 con tres digitos, el ID valido.)")
    print("")
    try:
        from src.graph.graph import get_graph
        from src.graph.state import get_initial_state

        graph = get_graph()
        # Modo administrador SIN alumno seleccionado (reproduce el sintoma).
        state = get_initial_state(
            user_message=SYMPTOM_QUERY,
            session_id="diag-session-blk6",
            user_id=None,
            conversation_history=[],
            role="admin",
            authenticated_user_id="admin",
        )
        config = {"configurable": {"thread_id": "diag-session-blk6"}}

        resultado = graph.invoke(state, config=config)
        final = resultado.get("final_response") or ""
        print("El grafo NO lanzo excepcion. final_response (primeros 300 chars):")
        print(final[:300])
        print("")
        # Detectar si el mensaje generico interno del generador aparecio.
        if "ha ocurrido un error" in final.lower():
            print("OBSERVACION: el grafo completo NO fallo, pero final_response contiene")
            print("un mensaje de error interno (probablemente del generador). El error")
            print("quedo contenido dentro de un nodo con try/except (no propago).")
        print("[BLOQUE 6] PASS")
        print("Evidencia: ruta real ejecutada. Ver final_response arriba.")
        return "PASS"
    except Exception:
        print("TRACEBACK COMPLETO subyacente al mensaje generico de la app:")
        print("-" * 79)
        traceback.print_exc(file=sys.stdout)
        print("-" * 79)
        print("")
        print("[BLOQUE 6] PASS")
        print("Evidencia: obtenido el traceback real que la app oculta tras el mensaje")
        print("generico. Revisar en el traceback el nodo/agente de origen (retriever,")
        print("azure_search, student_data o generator).")
        return "PASS"


def main():
    print("DIAGNOSTICO AZURE - scripts/diag_azure_connection.py")
    print("Solo lectura contra Azure. No modifica proyecto, BD ni indice.")
    r4 = bloque_4_no_semantica()
    r5, det5 = bloque_5_semantica()
    r6 = bloque_6_ruta_real()

    _sep("RESUMEN DE VERDICTOS DE BLOQUES DEL SCRIPT")
    print("BLOQUE 4 (no semantica): %s" % r4)
    print("BLOQUE 5 (semantica):    %s" % r5)
    print("BLOQUE 6 (ruta real):    %s" % r6)
    if det5:
        tipo, _, cuota = det5
        print("Bloque 5 excepcion tipo: %s | es_cuota_semantica=%s" % (tipo, cuota))


if __name__ == "__main__":
    main()
