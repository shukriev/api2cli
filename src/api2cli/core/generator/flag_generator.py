from __future__ import annotations

from api2cli.core.analyzer.naming_engine import get_short_flag, to_kebab_case
from api2cli.models.commands import FlagDef, FlagType
from api2cli.models.spec import ParameterDef, ParameterLocation, RequestBodyDef, SchemaDef

_TYPE_MAP: dict[str, FlagType] = {
    "string": FlagType.STRING,
    "integer": FlagType.INTEGER,
    "number": FlagType.FLOAT,
    "boolean": FlagType.BOOLEAN,
    "array": FlagType.ARRAY,
    "object": FlagType.JSON,
}


def _schema_to_flag_type(schema: SchemaDef | None) -> FlagType:
    if schema is None:
        return FlagType.STRING
    return _TYPE_MAP.get(schema.type or "string", FlagType.STRING)


def _is_simple_schema(schema: SchemaDef) -> bool:
    if schema.type != "object":
        return False
    for prop_schema in schema.properties.values():
        if prop_schema.type in ("object", "array") or prop_schema.properties:
            return False
    return True


class FlagGenerator:
    """Generates FlagDef list from endpoint parameters and request body."""

    def generate(
        self,
        parameters: list[ParameterDef],
        request_body: RequestBodyDef | None,
    ) -> list[FlagDef]:
        """Generate flags from parameters and request body.

        Args:
            parameters: List of endpoint parameters.
            request_body: Optional request body definition.

        Returns:
            List of FlagDef objects for the command.
        """
        flags: list[FlagDef] = []
        taken_shorts: set[str] = set()

        for param in parameters:
            flag_name = to_kebab_case(param.name)
            flag_type = _schema_to_flag_type(param.schema_def)
            required = param.required or param.location == ParameterLocation.PATH

            default = None
            if param.schema_def and param.schema_def.default is not None:
                default = param.schema_def.default

            short = get_short_flag(flag_name, taken_shorts)
            if short:
                taken_shorts.add(short)

            flags.append(
                FlagDef(
                    name=flag_name,
                    short=short,
                    type=flag_type,
                    required=required,
                    default=default,
                    description=param.description,
                    choices=param.schema_def.enum if param.schema_def else None,
                )
            )

        if request_body:
            body_schema = request_body.content.get("application/json")
            if body_schema is None and request_body.content:
                # Try first available content type
                body_schema = next(iter(request_body.content.values()))

            if body_schema and _is_simple_schema(body_schema):
                for prop_name, prop_schema in body_schema.properties.items():
                    flag_name = to_kebab_case(prop_name)
                    flag_type = _schema_to_flag_type(prop_schema)
                    required_prop = prop_name in body_schema.required

                    short = get_short_flag(flag_name, taken_shorts)
                    if short:
                        taken_shorts.add(short)

                    flags.append(
                        FlagDef(
                            name=flag_name,
                            short=short,
                            type=flag_type,
                            required=required_prop,
                            description=prop_schema.description,
                            choices=prop_schema.enum,
                        )
                    )
            else:
                short = get_short_flag("body", taken_shorts)
                if short:
                    taken_shorts.add(short)
                flags.append(
                    FlagDef(
                        name="body",
                        short=short,
                        type=FlagType.JSON,
                        required=request_body.required,
                        description="Request body as JSON string",
                    )
                )

        return flags
