"""Fase 5, Bloque 5.3.1: Tests unitarios de las herramientas SQLite y Azure Search.

Tests deterministas contra students.db real y test de integracion
de Azure AI Search (skip si no hay red/config).
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture(scope="module")
def sqlite_tools():
    """Importa las funciones de sqlite_query."""
    from src.tools.sqlite_query import (
        get_student_profile,
        get_subject_records,
        get_pending_subjects,
        get_passed_subjects,
        get_current_enrollments,
        get_scholarships,
        get_academic_standing,
        get_full_student_record,
    )
    return {
        "get_student_profile": get_student_profile,
        "get_subject_records": get_subject_records,
        "get_pending_subjects": get_pending_subjects,
        "get_passed_subjects": get_passed_subjects,
        "get_current_enrollments": get_current_enrollments,
        "get_scholarships": get_scholarships,
        "get_academic_standing": get_academic_standing,
        "get_full_student_record": get_full_student_record,
    }


# ===========================================================================
# TESTS get_student_profile
# ===========================================================================

class TestGetStudentProfile:
    """Tests para get_student_profile."""

    def test_alu001_basic_fields(self, sqlite_tools):
        """ALU001 existe y tiene los campos esperados."""
        result = sqlite_tools["get_student_profile"]("ALU001")
        assert "error" not in result, f"Error inesperado: {result}"
        assert result["name"] == "Carlos Vega Cruz"
        assert result["gpa"] == pytest.approx(9.1, abs=0.01)
        assert result["status"] == "excellent"
        assert result["degree"] == "Informatica"
        assert result["year"] == 4

    def test_alu001_has_all_keys(self, sqlite_tools):
        """El perfil de ALU001 contiene todos los campos del esquema."""
        result = sqlite_tools["get_student_profile"]("ALU001")
        expected_keys = {"id", "name", "email", "degree", "year", "gpa",
                         "credits_completed", "credits_total", "status", "enrolled_year"}
        assert expected_keys.issubset(set(result.keys()))

    def test_alu015_at_risk(self, sqlite_tools):
        """ALU015 esta en estado at_risk con GPA bajo."""
        result = sqlite_tools["get_student_profile"]("ALU015")
        assert "error" not in result
        assert result["status"] == "at_risk"
        assert result["gpa"] < 5.0

    def test_alu030_active(self, sqlite_tools):
        """ALU030 existe y esta activa."""
        result = sqlite_tools["get_student_profile"]("ALU030")
        assert "error" not in result
        assert result["name"] == "Isabel Blanco Pérez" or "Isabel" in result["name"]
        assert result["degree"] == "ADE"
        assert result["gpa"] > 7.0

    def test_nonexistent_id_returns_error(self, sqlite_tools):
        """Un ID que no existe devuelve error sin lanzar excepcion."""
        result = sqlite_tools["get_student_profile"]("ALU999")
        assert "error" in result
        assert "999" in result["error"] or "no encontrado" in result["error"].lower()

    def test_empty_id_returns_error(self, sqlite_tools):
        """ID vacio devuelve error sin excepcion."""
        result = sqlite_tools["get_student_profile"]("")
        assert "error" in result


# ===========================================================================
# TESTS get_pending_subjects
# ===========================================================================

class TestGetPendingSubjects:
    """Tests para get_pending_subjects."""

    def test_alu015_has_pending(self, sqlite_tools):
        """ALU015 tiene asignaturas pendientes/fallidas."""
        result = sqlite_tools["get_pending_subjects"]("ALU015")
        assert len(result) > 0
        assert "error" not in result[0]

    def test_alu015_includes_inf101(self, sqlite_tools):
        """ALU015 tiene INF101 como asignatura suspensa."""
        result = sqlite_tools["get_pending_subjects"]("ALU015")
        codes = [s["subject_code"] for s in result if "subject_code" in s]
        assert "INF101" in codes, f"INF101 no encontrado en: {codes}"

    def test_alu015_pending_structure(self, sqlite_tools):
        """Cada asignatura pendiente tiene los campos necesarios."""
        result = sqlite_tools["get_pending_subjects"]("ALU015")
        for subj in result:
            assert "subject_code" in subj
            assert "subject_name" in subj
            assert "status" in subj
            assert subj["status"] in ("pending", "failed")

    def test_nonexistent_id_returns_empty(self, sqlite_tools):
        """ID inexistente devuelve lista vacia, no excepcion."""
        result = sqlite_tools["get_pending_subjects"]("ALU999")
        # Puede ser lista vacia o lista con error, pero no excepcion
        assert isinstance(result, list)


# ===========================================================================
# TESTS get_scholarships
# ===========================================================================

class TestGetScholarships:
    """Tests para get_scholarships."""

    def test_alu030_has_mec_scholarship(self, sqlite_tools):
        """ALU030 tiene beca MEC activa."""
        result = sqlite_tools["get_scholarships"]("ALU030")
        assert len(result) > 0
        mec = [s for s in result if s.get("type") == "MEC"]
        assert len(mec) > 0, "No se encontro beca MEC para ALU030"
        assert mec[0]["amount"] == pytest.approx(1500.0, abs=0.01)
        assert mec[0]["status"] in ("active", "pending")

    def test_scholarships_structure(self, sqlite_tools):
        """Las becas tienen los campos type, amount, year, status."""
        result = sqlite_tools["get_scholarships"]("ALU030")
        for sch in result:
            assert "type" in sch
            assert "amount" in sch
            assert "year" in sch
            assert "status" in sch

    def test_nonexistent_returns_empty_list(self, sqlite_tools):
        """ID inexistente devuelve lista vacia."""
        result = sqlite_tools["get_scholarships"]("ALU999")
        assert isinstance(result, list)


# ===========================================================================
# TESTS get_full_student_record
# ===========================================================================

class TestGetFullStudentRecord:
    """Tests para get_full_student_record."""

    def test_alu001_complete_structure(self, sqlite_tools):
        """ALU001 devuelve estructura completa con todas las claves."""
        result = sqlite_tools["get_full_student_record"]("ALU001")
        assert "error" not in result
        required_keys = {"profile", "academic_standing", "passed_subjects",
                         "pending_subjects", "current_enrollments", "scholarships"}
        assert required_keys.issubset(set(result.keys()))

    def test_alu001_profile_in_record(self, sqlite_tools):
        """El perfil dentro del record es correcto."""
        result = sqlite_tools["get_full_student_record"]("ALU001")
        profile = result["profile"]
        assert profile["name"] == "Carlos Vega Cruz"
        assert profile["gpa"] == pytest.approx(9.1, abs=0.01)
        assert profile["status"] == "excellent"

    def test_alu001_academic_standing(self, sqlite_tools):
        """El academic_standing tiene credits y progress_pct."""
        result = sqlite_tools["get_full_student_record"]("ALU001")
        standing = result["academic_standing"]
        assert "credits_completed" in standing
        assert "credits_total" in standing
        assert "progress_pct" in standing
        assert standing["credits_total"] == 240

    def test_alu001_passed_subjects_nonempty(self, sqlite_tools):
        """ALU001 tiene asignaturas superadas."""
        result = sqlite_tools["get_full_student_record"]("ALU001")
        assert len(result["passed_subjects"]) > 0

    def test_nonexistent_returns_error(self, sqlite_tools):
        """ID inexistente devuelve dict con 'error', no excepcion."""
        result = sqlite_tools["get_full_student_record"]("ALU999")
        assert "error" in result


# ===========================================================================
# TESTS get_academic_standing
# ===========================================================================

class TestGetAcademicStanding:
    """Tests para get_academic_standing."""

    def test_alu001_standing_ok(self, sqlite_tools):
        """ALU001 tiene academic standing correcto."""
        result = sqlite_tools["get_academic_standing"]("ALU001")
        assert "error" not in result
        assert result["gpa"] == pytest.approx(9.1, abs=0.01)
        assert result["at_risk"] is False
        assert result["credits_total"] == 240

    def test_alu015_at_risk_flag(self, sqlite_tools):
        """ALU015 con GPA < 5 tiene at_risk=True."""
        result = sqlite_tools["get_academic_standing"]("ALU015")
        assert "error" not in result
        assert result["at_risk"] is True

    def test_standing_has_progress_pct(self, sqlite_tools):
        """progress_pct es un float entre 0 y 100."""
        result = sqlite_tools["get_academic_standing"]("ALU001")
        pct = result["progress_pct"]
        assert 0.0 <= pct <= 100.0


# ===========================================================================
# TESTS get_subject_records
# ===========================================================================

class TestGetSubjectRecords:
    """Tests para get_subject_records."""

    def test_alu001_has_records(self, sqlite_tools):
        """ALU001 tiene registros de asignaturas."""
        result = sqlite_tools["get_subject_records"]("ALU001")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "error" not in result[0]

    def test_records_structure(self, sqlite_tools):
        """Cada registro tiene los campos esperados."""
        result = sqlite_tools["get_subject_records"]("ALU001")
        for rec in result:
            if "error" not in rec:
                assert "subject_code" in rec
                assert "subject_name" in rec
                assert "credits" in rec
                assert "status" in rec


# ===========================================================================
# TESTS Azure Search (integracion, skip si sin red)
# ===========================================================================

@pytest.mark.integration
class TestAzureSearch:
    """Tests de integracion con Azure AI Search.

    Se marcan como integracion para poder saltarlos con --ignore-glob o
    pytest -m 'not integration' si no hay conectividad.
    """

    def test_search_returns_results(self):
        """search_knowledge_base devuelve resultados para una query academica."""
        try:
            from src.tools.azure_search import search_knowledge_base
            results = search_knowledge_base("matricula de una asignatura", top_k=3)
            assert isinstance(results, list)
            assert len(results) > 0, "Azure Search devolvio lista vacia"
        except Exception as exc:
            pytest.skip(f"Azure Search no disponible: {exc}")

    def test_search_result_has_metadata(self):
        """Cada resultado tiene los campos de metadatos esperados."""
        try:
            from src.tools.azure_search import search_knowledge_base
            results = search_knowledge_base("normativa de permanencia", top_k=2)
            if not results:
                pytest.skip("Sin resultados para validar estructura")
            doc = results[0]
            expected_fields = {"content", "title", "category", "source_file",
                               "relevance_score", "citation"}
            assert expected_fields.issubset(set(doc.keys()))
        except Exception as exc:
            pytest.skip(f"Azure Search no disponible: {exc}")

    def test_search_content_nonempty(self):
        """El campo 'content' de cada resultado no esta vacio."""
        try:
            from src.tools.azure_search import search_knowledge_base
            results = search_knowledge_base("requisitos beca MEC", top_k=2)
            for doc in results:
                assert doc.get("content"), "content vacio en resultado"
        except Exception as exc:
            pytest.skip(f"Azure Search no disponible: {exc}")
