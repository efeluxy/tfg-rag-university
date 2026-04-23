# Guía Docente — Bases de Datos I
**Universidad Demo | Documento oficial | Actualización: 2025-01-15**
**Categoría: guia_docente**

---

## Identificación

| Campo | Valor |
|-------|-------|
| Código | INF202 |
| Nombre | Bases de Datos I |
| Créditos ECTS | 6 |
| Curso | 2o |
| Semestre | 3o |
| Carácter | Obligatoria |
| Prerrequisitos | INF106 (Programación II) |
| Grado | Ingeniería Informática |

---

## Objetivos de aprendizaje

1. Comprender los fundamentos del modelo relacional y su base matemática (álgebra relacional).
2. Diseñar esquemas de bases de datos mediante el modelo entidad-relación (ER) y su traducción al modelo relacional.
3. Escribir consultas SQL de complejidad media-alta (joins, subconsultas, agregaciones).
4. Aplicar los conceptos de normalización hasta la tercera forma normal (3FN).
5. Comprender los mecanismos de control de concurrencia y recuperación ante fallos.
6. Utilizar un SGBD real (PostgreSQL) para diseñar, poblar y consultar bases de datos.

---

## Temario

### Tema 1: Introducción a las bases de datos
- 1.1 Concepto de base de datos y SGBD: ventajas sobre ficheros planos
- 1.2 Arquitectura ANSI/SPARC: niveles externo, conceptual e interno
- 1.3 Modelos de datos: jerárquico, en red, relacional y orientado a objetos
- 1.4 Historia y evolución de los SGBD

### Tema 2: Modelo Entidad-Relación
- 2.1 Entidades, atributos y relaciones
- 2.2 Cardinalidad y participación (1:1, 1:N, M:N)
- 2.3 Entidades débiles y relaciones identificadoras
- 2.4 Diagrama ER extendido: especialización y generalización

### Tema 3: Modelo relacional y álgebra relacional
- 3.1 Relación, tupla, atributo y dominio
- 3.2 Claves: primaria, candidata, ajena
- 3.3 Álgebra relacional: selección, proyección, unión, diferencia, producto cartesiano
- 3.4 Operaciones derivadas: join natural, join theta, división

### Tema 4: SQL — Lenguaje de consulta estructurado
- 4.1 DDL: CREATE, ALTER, DROP (tablas, índices, restricciones)
- 4.2 DML: SELECT, INSERT, UPDATE, DELETE
- 4.3 Consultas avanzadas: JOIN, subconsultas correlacionadas, GROUP BY, HAVING
- 4.4 Funciones de ventana (OVER, PARTITION BY) y CTEs (WITH)

### Tema 5: Normalización
- 5.1 Dependencias funcionales y axiomas de Armstrong
- 5.2 Primera forma normal (1FN): eliminar grupos repetitivos
- 5.3 Segunda forma normal (2FN): eliminar dependencias parciales
- 5.4 Tercera forma normal (3FN) y forma normal de Boyce-Codd (BCFN)

### Tema 6: Transacciones y control de concurrencia
- 6.1 Concepto de transacción: propiedades ACID
- 6.2 Anomalías de concurrencia: lectura sucia, lectura no repetible, lectura fantasma
- 6.3 Niveles de aislamiento en SQL
- 6.4 Recuperación ante fallos: log de transacciones y puntos de control

---

## Metodología

| Actividad | Horas presenciales | Horas autónomo |
|-----------|-------------------|----------------|
| Clases teóricas | 30 h | 30 h |
| Prácticas de laboratorio | 20 h | 45 h |
| Tutorías y actividades | 5 h | 20 h |
| **Total** | **55 h** | **95 h (= 150 h total)** |

---

## Evaluación

| Componente | Peso | Descripción |
|------------|------|-------------|
| Examen final escrito | 60% | Diseño de esquemas ER + SQL + normalización. Nota mínima: 4,0/10. |
| Prácticas de laboratorio | 25% | 4 prácticas en PostgreSQL. Entrega de scripts SQL y memoria. Asistencia mínima 80%. |
| Participación y trabajos | 15% | Mini-proyectos de diseño ER y quizzes en clase. |

---

## Bibliografía

1. Ramakrishnan, R. & Gehrke, J. (2003). *Database Management Systems* (3a ed.). McGraw-Hill.
2. Silberschatz, A., Korth, H. & Sudarshan, S. (2019). *Database System Concepts* (7a ed.). McGraw-Hill.
3. Date, C. J. (2004). *An Introduction to Database Systems* (8a ed.). Addison-Wesley.
4. PostgreSQL Global Development Group (2024). *PostgreSQL Documentation*. postgresql.org/docs

---

## Profesor responsable

**Dr. Ricardo Fernández Blanco** | Departamento de Sistemas de Información
Email: r.fernandez@universidad.es | Tutorías: Martes 9:00-11:00 y Jueves 11:00-13:00 (Despacho C-305)
