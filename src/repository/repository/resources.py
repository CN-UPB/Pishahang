from config2.config import config
from pathlib import Path
import yaml

SCHEMA_DIR = Path(__file__).parents[1] / Path(config.schema_dir)


def load_schema_file(path: Path):
    with open(path) as schema_file:
        return yaml.safe_load(schema_file)


resources = {
    name: load_schema_file(SCHEMA_DIR / path)
    for name, path in [
        ("cosds", "complex-service-descriptor/cosd-schema.yml"),
        ("cosrs", "complex-service-record/cosr-schema.yml"),
    ]
}
