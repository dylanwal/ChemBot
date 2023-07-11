"""Extract reference documentation from the NumPy source tree.

"""
import inspect
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


class Parameter:
    __slots__ = ("name", "type_", "description", "default")
    empty = inspect.Parameter.empty

    def __init__(self,
                 name: str,
                 type_: type | types.UnionType | empty = empty,
                 description: list[str] = None,
                 default=empty
                 ):
        self.name = name
        self.type_ = type_
        self.description = description
        self.default = default

    @property
    def required(self) -> bool:
        if self.default is Parameter.empty:
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
    _section_labels_lower = {k.lower(): v for k, v in sections.items()}

    def __init__(self, name: str):
        self.name = name
        self.signature: str | None = None
        self.summary: str | None = None
        self.parameters: list[Parameter] | None = None
        self.returns: list[Parameter] | None = None
        self.raises = None
        self.warns = None
        self.see_also = None
        self.notes = None
        self.warnings = None
        self.references = None
        self.examples = None

    def __str__(self):
        return self.signature

    def __repr__(self):
        return self.__str__()

    @classmethod
    def section_match(cls, text: str) -> str | None:
        match = text.lower().strip()
        for section in cls._section_labels_lower:
            if match in section:
                return cls._section_labels_lower[section]

        return None

    def add(self, section: str, lines: [str]):
        if section == "parameters":
            setattr(self, "parameters", add_parameters(lines))
        elif section == "returns":
            setattr(self, "returns", add_parameters(lines))
        else:
            if getattr(self, section) is not None:
                raise ValueError(f"'{section}' defined twice in doc string.")
            setattr(self, section, lines)


def add_parameters(lines: list[str]) -> list[Parameter]:
    parameter_lines = split_parameter_lines(lines)

    parameters = []
    for parameter_line in parameter_lines:
        parameters.append(parameter_line_to_parameter_object(parameter_line))

    return parameters


def split_parameter_lines(lines: list[str, ...]) -> list[list[str, ...]]:
    parameters = []
    parameter_lines = []
    for line in lines:
        if line[:2] != "  ":
            if parameter_lines:
                parameters.append(parameter_lines)
            parameter_lines = [line]
        else:
            parameter_lines.append(line.strip())

    if parameter_lines:
        parameters.append(parameter_lines)

    return parameters


def parameter_line_to_parameter_object(lines: list[str, ...]) -> Parameter:
    line1 = lines[0].split(":")
    parameter = Parameter(name=line1[0])
    if len(line1) > 2:
        parameter.type_ = line1[1]

    if len(lines) > 1:
        parameter.description = lines[1:]

    return parameter


def parse_numpy_docstring_and_signature(func: typing.Callable) -> NumpyDocString:
    """ main entry point """
    docstring = parse_numpy_docstring(func.__name__, inspect.getdoc(func))
    add_signature(func, docstring)
    return docstring


def parse_numpy_docstring(name: str, docstring: str) -> NumpyDocString:
    """Parse a NumPy-style docstring and return a dictionary of sections."""
    doc = NumpyDocString(name)
    if not docstring:
        return doc

    # Split the docstring into lines
    lines = docstring.split('\n')

    # Iterate through each line
    current_section = "summary"
    section_lines = []
    for line in lines:
        line_ = line.strip()

        # blank line
        if not line_:
            continue

        # underline line
        if line_[:4] == "----":
            continue

        # Check if the line matches a section pattern
        section_match = doc.section_match(line_)
        if section_match:
            doc.add(current_section, section_lines)
            section_lines = []
            current_section = section_match
            continue

        section_lines.append(line)

    doc.add(current_section, section_lines)

    return doc


def add_signature(function: typing.Callable, doc: NumpyDocString):
    signature = inspect.signature(function)
    doc.signature = function.__name__ + str(signature)

    parameter_objs = get_signature_parameters(list(signature.parameters.values()))
    doc.parameters = merge_parameters(parameter_objs, doc.parameters)

    returns_objs = get_return_parameters(signature.return_annotation)
    doc.returns = merge_parameters_return(returns_objs, doc.returns)


def get_signature_parameters(parameter_signatures: list[inspect.Parameter]) -> list[Parameter]:
    if not parameter_signatures:
        return []

    parameters = []
    for parameter_signature in parameter_signatures:
        if parameter_signature.name == "self":
            continue

        parameters.append(
            Parameter(
                name=parameter_signature.name,
                type_=parameter_signature.annotation,
                default=parameter_signature.default
            )
        )

    return parameters


def get_return_parameters(type_: type | types.UnionType) -> None | list[Parameter]:
    if type_ is inspect.Parameter.empty:
        return None

    return [Parameter(name="return", type_=type_)]


def merge_parameters(
        parameters1: list[Parameter],
        parameters2: list[Parameter]
) -> list[Parameter]:
    parameters = []

    if not parameters1:
        return parameters2

    if not parameters2:
        return parameters1

    # both are defined
    for parameter1 in parameters1:
        for i, parameter2 in enumerate(parameters2):
            if parameter1.name == parameter2.name:
                parameter1.description = parameter2.description
                parameters2.pop(i)
                break

        parameters.append(parameter1)

    for parameter in parameters2:
        parameters.append(parameter)

    return parameters


def merge_parameters_return(
        parameters1: list[Parameter],
        parameters2: list[Parameter]
) -> list[Parameter]:
    if not parameters1:
        return parameters2

    if not parameters2:
        return parameters1

    # both are defined
    parameters1[0].description = parameters2[0].description
    return parameters1
