from dataclasses import dataclass
from pathlib import Path

import omegaconf
from omegaconf import OmegaConf

@dataclass
class AppConfig:
    name: str
    age: int
    height: float

config_file = Path(__file__).parent / "text_config.yaml"

content = OmegaConf.load(config_file)
schema = OmegaConf.structured(AppConfig)
merged = OmegaConf.merge(content, schema)
conf = OmegaConf.to_object(merged)
print(conf.name)