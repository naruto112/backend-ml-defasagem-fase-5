"""Domain catalog use cases."""

from typing import Any

from app.repositories import DomainRepository


class DomainNotFoundError(LookupError):
    pass


class DomainService:
    def __init__(self, repository: DomainRepository) -> None:
        self._repository = repository

    @staticmethod
    def _serialize(field: Any) -> dict[str, Any]:
        converters = {"integer": int, "number": float, "string": str}
        convert = converters.get(field.data_type, str)
        return {
            "field": field.name,
            "label": field.label,
            "type": field.data_type,
            "required": field.required,
            "options": [
                {
                    "value": convert(option.value),
                    "label": option.label,
                    "order": option.display_order,
                }
                for option in field.options
            ],
        }

    def list_active_domains(self) -> list[dict[str, Any]]:
        return [self._serialize(field) for field in self._repository.list_active_with_options()]

    def get_active_domain(self, field_name: str) -> dict[str, Any]:
        field = self._repository.get_active_by_name(field_name)
        if field is None:
            raise DomainNotFoundError(field_name)
        return self._serialize(field)
