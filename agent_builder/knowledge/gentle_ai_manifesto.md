# Gentle-AI Engineering Manifesto

Este manifiesto establece los estándares técnicos, arquitectónicos y de calidad obligatorios para todos los miembros del equipo de software (Product Owner, Analistas, Arquitectos, Desarrolladores, DevOps y QA).

---

## 1. Filosofía de Ingeniería
- **Conceptos > Código**: No se escribe código sin entender a fondo el problema de negocio y el modelo de dominio.
- **Contra la inmediatez**: Se prioriza la solidez arquitectónica, el desacoplamiento y la mantenibilidad sobre la velocidad superficial.
- **La IA es una herramienta**: La IA ejecuta bajo dirección explícita; los contratos, validaciones y arquitectura son gobernados por criterios técnicos estrictos.

---

## 2. Arquitectura y Diseño de Software
- **Arquitectura Limpia / Hexagonal (Ports & Adapters)**:
  - El núcleo de negocio (Dominio y Casos de Uso) debe ser completamente independiente de frameworks, bases de datos, UI y librerías externas.
  - La comunicación entre capas se realiza exclusivamente a través de interfaces (Puertos) e implementaciones desacopladas (Adaptadores).
- **Decisiones Documentadas (ADR)**:
  - Toda decisión de arquitectura o elección de stack debe documentar el contexto, los trade-offs analizados y las alternativas descartadas.
- **Principios SOLID**:
  - Responsabilidad Única (SRP), Abierto/Cerrado (OCP), Sustitución de Liskov (LSP), Segregación de Interfaces (ISP) e Inversión de Dependencias (DIP).

---

## 3. Desarrollo Guiado por Especificaciones (Spec-Driven Development - SDD)
- **Especificaciones como Fuente Única de Verdad (Single Source of Truth)**:
  - Todo cambio o funcionalidad nace de una especificación formal y ejecutable (PRD + Historias de Usuario con escenarios Gherkin).
  - Flujo inmutable: `Especificación → Diseño/Arquitectura → Tareas → Implementación → Verificación (QA Gate)`.
  - El código es un derivado de la especificación, nunca al revés.
- **El Criterio Gherkin es un Contrato Inviolable**:
  - Cada escenario Dado/Cuando/Entonces (Given/When/Then) es una especificación ejecutable.
  - Ninguna historia o funcionalidad se considera 'Done' sin pruebas automatizadas (API y Playwright E2E) que verifiquen el contrato.
- **QA como Guardián de la Verificación (Verification Gate)**:
  - QA no improvisa pruebas al azar: cada caso de prueba (TP/CP) tiene trazabilidad 1:1 con un escenario Gherkin de la especificación.
  - El dictamen de QA verifica de forma determinística si la implementación cumple o no con la especificación aprobada.
- **Cobertura Mínima**:
  - Toda especificación debe cubrir: camino feliz, caminos alternos y manejo explícito de errores y bordes.
- **Valores Medibles y Determinísticos**:
  - Prohibidos los términos ambiguos ("rápido", "adecuado", "amigable"). Se definen códigos HTTP exactos, límites numéricos, timeouts en ms y estados de DOM observables.

---

## 4. Estándares de Código y Entregables
- **Idioma de los Artefactos**:
  - Código fuente, nombres de variables, funciones, clases, tablas, migraciones, comentarios y commits se escriben en **inglés** por estándar de la industria.
  - La documentación de negocio o requerimientos de usuario se mantiene en el idioma acordado para el producto.
- **Conventional Commits**:
  - Uso estricto del formato: `<type>(<scope>): <short description>`.
  - Tipos válidos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`.
- **Cero Atribución de IA**:
  - Queda terminantemente prohibido incluir "Co-Authored-By", firmas de IA o comentarios que atribuyan código a modelos de lenguaje en commits o código fuente.
- **Seguridad**:
  - Prohibido versionar credenciales, API keys, secretos o tokens en repositorios o logs. Solo se documentan los nombres de las variables de entorno.

---

## 5. Pruebas Unitarias de Alto Valor y Mutation Testing
- **Patrón AAA (Arrange, Act, Assert) Obligatorio**:
  - Toda prueba unitaria debe estructurarse explícitamente en tres bloques limpios:
    1. **Arrange**: Preparar el estado inicial, dependencias y datos de prueba precisos.
    2. **Act**: Invocar la acción concreta del método o caso de uso bajo prueba.
    3. **Assert**: Verificar de forma estricta los efectos colaterales, valores de retorno y excepciones esperadas.
- **Prohibido el Test Padding (Pruebas Basura / Cosméticas)**:
  - Queda terminantemente prohibido escribir pruebas que solo busquen inflar métricas de cobertura de líneas sin verificar comportamiento de negocio real.
  - Prohibidos los tests sin asserts, asserts triviales (`assert True`, `assert result is not None` cuando debe validarse el contenido) o tests sobre-mockeados que prueben los mocks en lugar de la lógica de dominio.
- **Criterio de Mutation Testing (Mutation Score)**:
  - El valor de una prueba unitaria no se mide por las líneas de código que ejecuta, sino por **los mutantes que es capaz de matar**.
  - Si un mutante introduce una alteración conceptual (ej: invertir un operador de comparación `>` por `>=`, cambiar un operador lógico `and` por `or`, omitir una validación o forzar un retorno temprano) y la prueba unitaria sigue pasando en verde, **la prueba carece de valor y debe ser rechazada**.
- **Auditoría de Pruebas Unitarias por QA (Grey-Box Quality Gate)**:
  - El QA con dominio técnico de código y de negocio (QA Semi Senior) audita activamente el código de las pruebas unitarias entregadas por los desarrolladores.
  - QA evalúa: adherencia estricta a AAA, claridad de intencionalidad, aserciones determinísticas y resistencia ante mutaciones de código. Pruebas cosméticas son devueltas inmediatamente como deuda técnica a corregir.
