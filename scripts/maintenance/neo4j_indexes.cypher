// ============================================================================
// Neo4j Constraints and Indexes for Camstar/Opcenter Ontology
// ============================================================================

// 1. Unique constraint on OntologyClass name (automatically creates a lookup index)
// Ensures no duplicate classes can be inserted and speeds up class-based queries (e.g. sidebar and path highlights).
CREATE CONSTRAINT unique_ontology_class_name IF NOT EXISTS
FOR (c:OntologyClass) REQUIRE c.name IS UNIQUE;

// 2. Index on OntologyProperty name
// Optimizes queries searching for specific properties.
CREATE INDEX ontology_property_name IF NOT EXISTS
FOR (p:OntologyProperty) ON (p.name);

// 3. Index on OntologyProperty className
// Optimizes HAS_PROPERTY relations and attribute queries grouped by class.
CREATE INDEX ontology_property_class_name IF NOT EXISTS
FOR (p:OntologyProperty) ON (p.className);

// 4. Composite unique constraint on OntologyProperty (className, name)
// Prevents duplicate property entries within the same class and optimizes loader MERGE statements.
CREATE CONSTRAINT unique_ontology_property IF NOT EXISTS
FOR (p:OntologyProperty) REQUIRE (p.className, p.name) IS UNIQUE;

