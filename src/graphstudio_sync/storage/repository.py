"""Compose control-plane persistence around one engine and settings object."""
from src.graphstudio_sync.config import SyncSettings
from .database import control_engine
from .connections import ConnectionsRepository
from .sync_runs import SyncRunsRepository
from .model_catalog import ModelCatalogRepository
from .contracts import ContractsRepository
from .model_changes import ModelChangesRepository


class ControlPlaneRepository(ConnectionsRepository, SyncRunsRepository, ModelCatalogRepository, ContractsRepository, ModelChangesRepository):
    def __init__(self, settings: SyncSettings):
        self.settings = settings
        self.engine = control_engine(settings)

