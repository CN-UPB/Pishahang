from appcfg import get_config
from pathlib import Path
import json

config = get_config(__name__)

SCHEMA_DIR = Path(__file__).parents[1] / Path(config["schema_dir"])


def load_schema_file(path: Path):
    with path.with_suffix(".json").open() as f:
        return json.load(f)


resources = {
    name: load_schema_file(SCHEMA_DIR / path)
    for name, path in [
        ("function-descriptors", "descriptors/functions/any"),
        ("service-descriptors", "descriptors/service/service"),
        ("function-records", "records/functions/any"),
        ("service-records", "records/service"),
    ]
}
