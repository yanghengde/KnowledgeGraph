import os
import json
from src.ontology.llm_builder import read_wiki_document, generate_ontology_from_wiki

def build_ontology(module_key, wiki_filename, output_filename):
    wiki_path = os.path.join(os.path.dirname(__file__), "src", "ontology", "wiki_kb", wiki_filename)
    output_path = os.path.join(os.path.dirname(__file__), "src", "ontology", "wiki_kb", output_filename)
    
    if os.path.exists(wiki_path):
        print(f"Reading {wiki_path}...")
        # Since these PDFs are huge, let's limit the text so DeepSeek doesn't time out or hit token limits.
        # We'll take the first 40,000 characters which is roughly 10,000 tokens.
        content = read_wiki_document(wiki_path)[:40000] 
        print(f"Sending to DeepSeek LLM for {module_key} ontology extraction (this may take a minute)...")
        ontology = generate_ontology_from_wiki(content, module_key)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(ontology, f, indent=4, ensure_ascii=False)
            
        print(f"Ontology extracted and saved to {output_path}")
    else:
        print(f"Wiki document not found at {wiki_path}")

if __name__ == "__main__":
    build_ontology("Operation Modeling", "operation_modeling.md", "operation_ontology.json")
    build_ontology("Spec Modeling", "spec_modeling.md", "spec_ontology.json")
    build_ontology("WorkCenter Modeling", "workcenter_modeling.md", "workcenter_ontology.json")
    build_ontology("Factory Modeling", "factory_modeling.md", "factory_ontology.json")
    build_ontology("MfgLine Modeling", "mfgline_modeling.md", "mfgline_ontology.json")
    build_ontology("MfgCalendar Modeling", "mfgcalendar_modeling.md", "mfgcalendar_ontology.json")
    build_ontology("Product Modeling", "product_modeling.md", "product_ontology.json")
    build_ontology("BOM Modeling", "bom_modeling.md", "bom_ontology.json")
    build_ontology("ERPBOM Modeling", "erpbom_modeling.md", "erpbom_ontology.json")
    build_ontology("Container Modeling", "container_modeling.md", "container_ontology.json")
    build_ontology("Carrier Modeling", "carrier_modeling.md", "carrier_ontology.json")
    build_ontology("BusinessRule Modeling", "businessrule_modeling.md", "businessrule_ontology.json")
    build_ontology("Data Collection Modeling", "datacollection_modeling.md", "datacollection_ontology.json")
    build_ontology("Quality Modeling", "quality_modeling.md", "quality_ontology.json")
    build_ontology("Electronic Procedure Modeling", "electronic_procedure_modeling.md", "electronic_procedure_ontology.json")
    build_ontology("Resource Modeling", "resource_modeling.md", "resource_ontology.json")
    build_ontology("Material Modeling", "material_modeling.md", "material_ontology.json")
    build_ontology("Employee Modeling", "employee_modeling.md", "employee_ontology.json")
    build_ontology("Role Modeling", "role_modeling.md", "role_ontology.json")
    build_ontology("MfgOrder Modeling", "mfgorder_modeling.md", "mfgorder_ontology.json")
    build_ontology("Maintenance Modeling", "maintenance_modeling.md", "maintenance_ontology.json")
    build_ontology("Part Modeling", "part_modeling.md", "part_ontology.json")
    build_ontology("Organization Modeling", "organization_modeling.md", "organization_ontology.json")
    build_ontology("BillOfProcess Modeling", "billofprocess_modeling.md", "billofprocess_ontology.json")
    build_ontology("Team Modeling", "team_modeling.md", "team_ontology.json")
    build_ontology("Terminal Modeling", "terminal_modeling.md", "terminal_ontology.json")
    build_ontology("SalesOrder Modeling", "salesorder_modeling.md", "salesorder_ontology.json")
    build_ontology("Sampling Modeling", "sampling_modeling.md", "sampling_ontology.json")
