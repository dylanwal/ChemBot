"""Extract reference documentation from the NumPy source tree.

"""
import inspect
import re
import types
import typing


def strip_blank_lines(line):
    """Remove leading and trailing blank lines from a list of lines"""
    while line and not line[0].strip():
        del line[0]
    while line and not line[-1].strip():
        del line[-1]
    return line


class ParseError(Exception):
    def __str__(self):
        message = self.args[0]
        if hasattr(self, "docstring"):
            message = f"{message} in {self.docstring!r}"
        return message


class NotDefined:
    def __str__(self):
        return "Not Defined"


NOT_DEFINED = NotDefined()


class TypeList:
    outer = list

    def __init__(self, inner: type):
        self.inner = inner

    def __str__(self):
        return f"{self.outer.__name__}[{self.inner.__name__}]"

    def __repr__(self):
        return self.__repr__()


class TypeOptions:
    def __init__(self, types_: list[type | TypeList] = None):
        self.types = types_ if types_ is not None else []

    def add(self, option: type | TypeList):
        self.types.append(option)


class Parameter:
    __slots__ = ("name", "type_", "description", "default_value")

    def __init__(self, name: str, type_: TypeOptions, description: list[str], default_value=NOT_DEFINED):
        self.name = name
        self.type_ = type_
        self.description = description
        self.default_value = default_value if default_value is not NOT_DEFINED else NotDefined()

    @property
    def required(self) -> bool:
        if self.default_value is NOT_DEFINED:
            return False
        return True

    def __str__(self):
        return f"Parameter(name: {self.name}, type_: {self.type_}, description: {self.description})"

    def __repr__(self):
        return self.__str__()


class NumpyDocString:
    """Parses a numpydoc string to an abstract representation

    Instances define a mapping from section title to structured data.

    """
    sections = {
        "Signature": "signature",
        "Summary": "summary",
        "Extended Summary": "extended_summary",
        "Parameters": "parameters",
        "Returns": "returns",
        "Yields": "yields",
        "Receives": "receives",
        "Raises": "raises",
        "Warns": "warns",
        "Other Parameters": "other_parameters",
        "Attributes": "attributes",
        "Methods": "methods",
        "See Also": "see_also",
        "Notes": "notes",
        "Warnings": "warnings",
        "References": "references",
        "Examples": "examples",
        "index": "index",
    }
    section_labels_lower = {k.lower(): v for k, v in sections.items()}

    def __init__(self):
        self.signature: str | None = None
        self.summary: str | None = None
        self.extended_summary: str | None = None
        self.parameters: list[Parameter] | None = None
        self.returns: list[Parameter] | None = None
        self.yields = None
        self.receives = None
        self.raises = None
        self.warns = None
        self.other_parameters = None
        self.attributes = None
        self.methods = None
        self.see_also = None
        self.notes = None
        self.warnings = None
        self.references = None
        self.examples = None
        self.index = None

    @classmethod
    def section_match(cls, text: str) -> str | None:
        match = text.lower().strip()
        for section in cls.section_labels_lower:
            if match in section:
                return cls.section_labels_lower[section]

        return None

    def add(self, section: str, lines: [str]):
        if section == "parameters":
            self.add_parameters(lines)
        else:
            if getattr(self, section) is not None:
                raise ValueError(f"'{section}' defined twice in doc string.")
            setattr(self, "section", lines)

    def add_parameters(self, lines: list[str]):
        pass


def parse_numpy_docstring_and_typehints(func: typing.Callable) -> NumpyDocString:
    docstring = parse_numpy_docstring(inspect.getdoc(func))
    add_type_hints(func, docstring)
    return docstring


def parse_numpy_docstring(docstring: str) -> NumpyDocString:
    """Parse a NumPy-style docstring and return a dictionary of sections."""
    doc = NumpyDocString()
    # Split the docstring into lines
    lines = docstring.split('\n')

    # Iterate through each line
    current_section = ""
    section_lines = []
    for line in lines:
        line = line.strip()

        # blank line
        if not line:
            continue

        # underline line
        if line[:4] is "----":
            continue

        # Check if the line matches a section pattern
        section_match = doc.section_match(line)
        if section_match:
            doc.add(current_section, section_lines)
            section_lines = []
            current_section = section_match
            continue

        section_lines.append(line)

    return doc


def add_type_hints(function: callable, doc: NumpyDocString):
    type_hints = typing.get_type_hints(function)
    if type_hints:
        add_return(type_hints, doc)  # run first to pop off returns from type_hints
        add_parameter(type_hints, doc)


def add_parameter(type_hints: dict, doc: NumpyDocString):
    if not type_hints:
        return

    doc_param_names = [p.name for p in doc.parameters]
    for i, param in enumerate(type_hints):
        if param in doc_param_names:
            type_ = type_hints[param]
            if str(type_).startswith("Optional"):
                type_ = type_.__args__[0]
            doc.parameters[i].type_ = type_
        else:
            doc.parameters.append(Parameter(param, type(param), []))


def add_return(type_hints: dict, doc: NumpyDocString):
    if 'return' not in type_hints:
        return

    return_param = breakup_type(type_hints.pop("return"))

    length = len(doc.returns) - 1
    for i, param in enumerate(return_param):
        # if no parameters, or more parameter than in docstring; add them
        if i > length:
            doc.returns.append(Parameter(f"return_{i}", param, []))
        else:
            doc_param: Parameter = doc.returns[i]
            doc_param.type_ = param


def breakup_type(type_: type) -> tuple[type, ...] | list[type, ...]:
    if isinstance(type_, types.UnionType):
        return type_.__args__

    if type_.__name__ == "tuple" or type_.__name__ == "list":
        return type_.__args__

    return (type_,)


def parse_type(type_: str) -> TypeOptions:
    if not type_:
        raise ValueError("")

    type_ = type_.replace(" ", "").split("|")

    options = TypeOptions()
    for t in type_:
        options.add(string_to_type(t))

    return options


def string_to_type(type_: str) -> type | TypeList:
    if type_ in registry:
        return registry.get(type_)

    if type_.startswith("list"):
        return TypeList(string_to_type(type_[5:-1]))  # [5:-1] removes 'list[ ]'
    if type_.startswith("tuple"):
        raise NotImplementedError
    if type_.startswith("set"):
        raise NotImplementedError
    if type_.startswith("dict"):
        raise NotImplementedError

    raise ValueError(f"Unknown type: {type_}")