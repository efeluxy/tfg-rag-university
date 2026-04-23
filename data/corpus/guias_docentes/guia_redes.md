# Guía Docente — Redes I
**Universidad Demo | Documento oficial | Actualización: 2025-01-15**
**Categoría: guia_docente**

---

## Identificación

| Campo | Valor |
|-------|-------|
| Código | INF203 |
| Nombre | Redes I |
| Créditos ECTS | 6 |
| Curso | 2o |
| Semestre | 3o |
| Carácter | Obligatoria |
| Prerrequisitos | INF105 (Fundamentos de Computadores) |
| Grado | Ingeniería Informática |

---

## Objetivos de aprendizaje

1. Comprender los fundamentos de las redes de computadores y el modelo OSI/TCP-IP.
2. Analizar los protocolos de las capas de enlace, red y transporte.
3. Configurar redes locales básicas y entender el funcionamiento de switches y routers.
4. Aplicar técnicas de direccionamiento IP (IPv4 e IPv6) y subnetting.
5. Utilizar herramientas de diagnóstico de redes (ping, traceroute, Wireshark).
6. Identificar vulnerabilidades básicas de red y medidas de mitigación.

---

## Temario

### Tema 1: Introducción a las redes
- 1.1 Tipos de redes: LAN, WAN, MAN, Internet
- 1.2 Modelos de referencia: OSI (7 capas) y TCP/IP (4 capas)
- 1.3 Medios de transmisión: par trenzado, fibra óptica, inalámbrico
- 1.4 Conceptos de ancho de banda, latencia y throughput

### Tema 2: Capa de enlace de datos
- 2.1 Tramas, direcciones MAC y el protocolo Ethernet
- 2.2 Switches y dominios de colisión/broadcast
- 2.3 Detección y corrección de errores: CRC y bits de paridad
- 2.4 Protocolo ARP y funcionamiento de las tablas CAM

### Tema 3: Capa de red — IP
- 3.1 Direccionamiento IPv4: clases, máscara de subred y CIDR
- 3.2 Subnetting y supernetting (VLSM)
- 3.3 Protocolo IP: fragmentación, TTL y cabecera IP
- 3.4 Introducción a IPv6: formato de dirección y principales diferencias

### Tema 4: Enrutamiento
- 4.1 Concepto de router y tablas de enrutamiento
- 4.2 Enrutamiento estático vs. dinámico
- 4.3 Protocolos de enrutamiento: RIP, OSPF (conceptos básicos)
- 4.4 NAT (Network Address Translation) y sus implicaciones

### Tema 5: Capa de transporte
- 5.1 Puertos y sockets: concepto de socket como par IP:Puerto
- 5.2 UDP: datagrama, ventajas e inconvenientes, casos de uso
- 5.3 TCP: segmento, control de flujo, control de congestión
- 5.4 Establecimiento y cierre de conexiones TCP (three-way handshake)

### Tema 6: Capa de aplicación y herramientas
- 6.1 DNS: resolución de nombres, registros A, CNAME, MX
- 6.2 HTTP/HTTPS: request/response, métodos, códigos de estado
- 6.3 DHCP: asignación dinámica de direcciones
- 6.4 Herramientas de diagnóstico: ping, traceroute, nmap, Wireshark

---

## Metodología

| Actividad | Horas presenciales | Horas autónomo |
|-----------|-------------------|----------------|
| Clases teóricas | 28 h | 32 h |
| Prácticas de laboratorio | 22 h | 48 h |
| Tutorías y actividades | 5 h | 15 h |
| **Total** | **55 h** | **95 h (= 150 h total)** |

---

## Evaluación

| Componente | Peso | Descripción |
|------------|------|-------------|
| Examen final escrito | 60% | Preguntas teóricas + ejercicios de subnetting y protocolos. Nota mínima: 4,0/10. |
| Prácticas de laboratorio | 25% | 5 prácticas con Packet Tracer y Wireshark. Asistencia mínima: 80%. |
| Participación y trabajos | 15% | Análisis de capturas de red y cuestionarios. |

---

## Bibliografía

1. Tanenbaum, A. S. & Wetherall, D. J. (2021). *Computer Networks* (6a ed.). Pearson.
2. Kurose, J. F. & Ross, K. W. (2021). *Computer Networking: A Top-Down Approach* (8a ed.). Pearson.
3. Stevens, W. R. (1994). *TCP/IP Illustrated, Vol. 1*. Addison-Wesley.
4. Cisco Networking Academy (2023). *CCNA Routing and Switching Introduction*. Cisco Press.

---

## Profesor responsable

**Dr. Pablo Torres Serrano** | Departamento de Arquitectura y Tecnología de Computadores
Email: p.torres@universidad.es | Tutorías: Lunes 12:00-14:00 y Viernes 10:00-12:00 (Despacho D-201)
