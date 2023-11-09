import abc
import dataclasses
import functools
import re
from typing import Any, Generic, TypeVar, Union, get_args

_ArgType = Union[int, str]
T = TypeVar("T", bound=_ArgType)
Warnings = list[str]

@dataclasses.dataclass
class _PromptArg(abc.ABC, Generic[T]):
    name: str
    @classmethod
    def get_type(cls) -> T:
        return get_args(cls.__orig_bases__[0])[0]

    @abc.abstractmethod
    def parse(self, raw: T) -> [T, Warnings]:
        """Returns the parsed value and a possibly empty list of warnings."""\


@dataclasses.dataclass
class IntArg(_PromptArg[int]):
    default_value: int
    min_value: int | None = None
    max_value: int | None = None

    def parse(self, raw: str) -> tuple[int, Warnings]:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"Invalid argument {self.name}: must be integer") from exc
        if self.min_value is not None and value < self.min_value:
            return self.min_value, [f"{self.name} {value} too low, defaulting to {self.min_value}"]
        if self.max_value is not None and value > self.max_value:
            return self.max_value, [f"{self.name} {value} too high, defaulting to {self.max_value}"]
        return value, []


@dataclasses.dataclass
class Config:
    _result_type: type
    _arg_list: list[str]
    _config: list[_PromptArg]


def make_config(name: str, config: list[_PromptArg]) -> Config:
    result_dc = dataclasses.make_dataclass(f"{name}Result", [
        (arg.name, arg.get_type(), dataclasses.field(default=arg.default_value))
        for arg in config
    ])
    arg_list = [arg.name for arg in config]
    return Config(result_dc, arg_list, config)


@dataclasses.dataclass
class ParsedPrompt:
    cleaned: str
    result: Any
    warnings: list[str]


_REGEX_TEMPLATE = r'\$ARGNAME=([^\s\$]*)'
_REGEX_CATCHALL = r'\$([^\s]*)=([^\s\$]*)'
def _regex(name: str):
    return _REGEX_TEMPLATE.replace("ARGNAME", name)
def _leftover_args(parsed: str):
    return [
        f"{kv[0]}={kv[1]}"
        for kv in re.findall(_REGEX_CATCHALL, parsed)
    ]


def parse_args(raw_prompt: str, config: Any) -> ParsedPrompt:
    arg_map = {}  # Map from names to values
    warnings = []

    def capture_value(arg: T, match):
        value, arg_warnings = arg.parse(match.group(1))
        warnings.extend(arg_warnings)
        arg_map[arg.name] = value
        return ""

    # pylint: disable=protected-access
    for arg in config._config:
        raw_prompt = re.sub(_regex(arg.name), functools.partial(capture_value, arg), raw_prompt)

    unrecognized = _leftover_args(raw_prompt)
    if unrecognized:
        known_args = ", ".join(f"{arg.name} ({arg.get_type().__name__})" for arg in config._config)
        raise ValueError(f"Unrecognized arguments: {unrecognized}.\nKnown: {known_args}")

    result = config._result_type(**arg_map)

    return ParsedPrompt(cleaned=raw_prompt, result=result, warnings=warnings)
