@dataclass
class Configuration:
    name: str
    timeout: int = 30
    retries: int = 3
    settings: Optional[Dict[str, Any]] = None


@call
def save_configuration(config: Configuration) -> None:
    # Implementation
    pass
