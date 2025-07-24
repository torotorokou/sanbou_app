from pathlib import Path

BASE_PATH = Path("/app")
PDF_PATH = BASE_PATH / "local_data" / "master" / "SOLVEST.pdf"
JSON_PATH = BASE_PATH / "local_data" / "master" / "structured_SOLVEST_output_with_tags.json"
FAISS_PATH = BASE_PATH / "local_data" / "master" / "vectorstore" / "solvest_faiss_corrected"
ENV_PATH = BASE_PATH / "config" / ".env"
YAML_PATH = BASE_PATH / "local_data" / "master" / "category_question_templates_with_tags.yaml"
