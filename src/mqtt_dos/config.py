"""Configuração central de um run de treino."""

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "MQTT Under Attack Dataset" / "DoS.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

MODEL_NAMES = (
    "LDA",
    "QDA",
    "GaussianNB",
    "DecisionTree",
    "RandomForest",
    "GradientBoosting",
    "SVM",
)
SELECTOR_NAMES = (
    "LowVariance",
    "ANOVA",
    "MutualInformation",
    "Lasso",
    "LinearSVC",
    "ExtraTrees",
)


@dataclass(frozen=True)
class RunConfig:
    """Parâmetros de um run; os defaults seguem o protocolo do paper WPMC."""

    run_name: str = "paper_protocol"
    random_state: int = 42
    test_size: float = 0.2
    n_trials: int = 30
    cv_folds: int = 5
    top_k: int = 15
    tune_subsample: dict[str, int] = field(default_factory=lambda: {"SVM": 15_000})
    models: tuple[str, ...] = MODEL_NAMES
    selectors: tuple[str, ...] = SELECTOR_NAMES

    def __post_init__(self) -> None:
        if not 0 < self.test_size < 1:
            raise ValueError(f"test_size deve estar entre 0 e 1, recebido {self.test_size}")
        if self.cv_folds < 2:
            raise ValueError(f"cv_folds deve ser pelo menos 2, recebido {self.cv_folds}")
        unknown_models = set(self.models) - set(MODEL_NAMES)
        if unknown_models:
            raise ValueError(f"modelos desconhecidos: {sorted(unknown_models)}")
        unknown_selectors = set(self.selectors) - set(SELECTOR_NAMES)
        if unknown_selectors:
            raise ValueError(f"seletores desconhecidos: {sorted(unknown_selectors)}")

    @property
    def output_dir(self) -> Path:
        return OUTPUTS_DIR / self.run_name
