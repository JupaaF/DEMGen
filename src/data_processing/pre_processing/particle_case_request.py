from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ParticleGenerationContext:
    parameters: Mapping[str, Any]
    project_root: Path
    run_dir: Path


@dataclass(frozen=True)
class ParticleCaseRequest:
    case_number: int
    output_file_name: str
    packing_density: float | None = None
