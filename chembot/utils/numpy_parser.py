"""Extract reference documentation from the NumPy source tree.

"""
import inspect
import textwrap
import re
import pydoc
import types
import typing
from warnings import warn
from collections.abc import Callable, Mapping
import sys
from functools import cached_property


def strip_blank_lines(line):
    """Remove leading and trailing blank lines from a list of lines"""
    while line and not line[0].strip():
        del line[0]
    while line and not line[-1].strip():
        del line[-1]
    return line


class Reader:
    """A line-based string reader."""

    def __init__(self, data):
        """
        Parameters
        ----------
        data : str
           String with lines separated by '\\n'.

        """
        if isinstance(data, list):
            self._str = data
        else:
            self._str = data.split("\n")  # store string as list of lines

        self.reset()
        self._line = 0

    def __getitem__(self, n):
        return self._str[n]

    def reset(self):
        self._line = 0  # current line nr

    def read(self):
        if not self.eof():
            out = self[self._line]
            self._line += 1
            return out
        else:
            return ""

    def seek_next_non_empty_line(self):
        for line in self[self._line:]:
            if line.strip():
                break
            else:
                self._line += 1

    def eof(self):
        return self._line >= len(self._str)

    def read_to_condition(self, condition_func):
        start = self._line
        for line in self[start:]:
            if condition_func(line):
                return self[start: self._line]
            self._line += 1
            if self.eof():
                return self[start: self._line + 1]
        return []

    def read_to_next_empty_line(self):
        self.seek_next_non_empty_line()

        def is_empty(line):
            return not line.strip()

        return self.read_to_condition(is_empty)

    def read_to_next_unindented_line(self):
        def is_unindented(line):
            return line.strip() and (len(line.lstrip()) == len(line))

        return self.read_to_condition(is_unindented)

    def peek(self, n=0):
        if self._line + n < len(self._str):
            return self[self._line + n]
        else:
            return ""

    def is_empty(self):
        return not "".join(self._str).strip()


class ParseError(Exception):
    def __str__(self):
        message = self.args[0]
        if hasattr(self, "docstring"):
            message = f"{message} in {self.docstring!r}"
        return message


class Parameter:
    __slots__ = ("name", "type_", "description")

    def __init__(self, name: str, type_: str, description: list[str]):
        self.name = name
        self.type_ = type_
        self.description = description

    def __str__(self):
        return f"Parameter(name: {self.name}, type_: {self.type_}, description: {self.description})"

    def __repr__(self):
        return self.__str__()


class NumpyDocString(Mapping):
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

    def __init__(self, docstring, config=None):
        orig_docstring = docstring
        docstring = textwrap.dedent(docstring).split("\n")

        self._doc = Reader(docstring)

        self.signature = ""
        self.summary = []
        self.extended_summary = []
        self.parameters = []
        self.returns = []
        self.yields = []
        self.receives = []
        self.raises = []
        self.warns = []
        self.other_parameters = []
        self.attributes = []
        self.methods = []
        self.see_also = []
        self.notes = []
        self.warnings = []
        self.references = ""
        self.examples = ""
        self.index = {}

        try:
            self._parse()
        except ParseError as e:
            e.docstring = orig_docstring
            raise

    def __getitem__(self, key):
        return getattr(self, self.sections[key])

    def __setitem__(self, key, value):
        if key not in self.sections:
            self._error_location(f"Unknown section {key}", error=False)
        else:
            setattr(self, self.sections[key], value)

    def __iter__(self):
        for section in self.sections:
            yield getattr(self, self.sections[section])
        # return iter(self._parsed_data)

    def __len__(self):
        return len(self.sections)

    def _is_at_section(self):
        self._doc.seek_next_non_empty_line()

        if self._doc.eof():
            return False

        l1 = self._doc.peek().strip()  # e.g. Parameters

        if l1.startswith(".. index::"):
            return True

        l2 = self._doc.peek(1).strip()  # ---------- or ==========
        if len(l2) >= 3 and (set(l2) in ({"-"}, {"="})) and len(l2) != len(l1):
            snip = "\n".join(self._doc._str[:2]) + "..."
            self._error_location(
                f"potentially wrong underline length... \n{l1} \n{l2} in \n{snip}",
                error=False,
            )
        return l2.startswith("-" * len(l1)) or l2.startswith("=" * len(l1))

    def _strip(self, doc):
        i = 0
        j = 0
        for i, line in enumerate(doc):
            if line.strip():
                break

        for j, line in enumerate(doc[::-1]):
            if line.strip():
                break

        return doc[i: len(doc) - j]

    def _read_to_next_section(self):
        section = self._doc.read_to_next_empty_line()

        while not self._is_at_section() and not self._doc.eof():
            if not self._doc.peek(-1).strip():  # previous line was empty
                section += [""]

            section += self._doc.read_to_next_empty_line()

        return section

    def _read_sections(self):
        while not self._doc.eof():
            data = self._read_to_next_section()
            name = data[0].strip()

            if name.startswith(".."):  # index section
                yield name, data[1:]
            elif len(data) < 2:
                yield StopIteration
            else:
                yield name, self._strip(data[2:])

    def _parse_param_list(self, content, single_element_is_type=False):
        content = dedent_lines(content)
        r = Reader(content)
        params = []
        while not r.eof():
            header = r.read().strip()
            if ":" in header:  # line changed
                arg_name, arg_type = header.split(":", maxsplit=1)  # line changed
                arg_name = arg_name.rstrip()  # line changed
                arg_type = arg_type.lstrip()  # line changed
            else:
                arg_name, arg_type = header, ""  # line changed

            desc = r.read_to_next_unindented_line()
            desc = dedent_lines(desc)
            desc = strip_blank_lines(desc)

            params.append(Parameter(arg_name, arg_type, desc))

        return params

    # See also supports the following formats.
    #
    # <FUNCNAME>
    # <FUNCNAME> SPACE* COLON SPACE+ <DESC> SPACE*
    # <FUNCNAME> ( COMMA SPACE+ <FUNCNAME>)+ (COMMA | PERIOD)? SPACE*
    # <FUNCNAME> ( COMMA SPACE+ <FUNCNAME>)* SPACE* COLON SPACE+ <DESC> SPACE*

    # <FUNCNAME> is one of
    #   <PLAIN_FUNCNAME>
    #   COLON <ROLE> COLON BACKTICK <PLAIN_FUNCNAME> BACKTICK
    # where
    #   <PLAIN_FUNCNAME> is a legal function name, and
    #   <ROLE> is any nonempty sequence of word characters.
    # Examples: func_f1  :meth:`func_h1` :obj:`~baz.obj_r` :class:`class_j`
    # <DESC> is a string describing the function.

    _role = r":(?P<role>(py:)?\w+):"
    _funcbacktick = r"`(?P<name>(?:~\w+\.)?[a-zA-Z0-9_\.-]+)`"
    _funcplain = r"(?P<name2>[a-zA-Z0-9_\.-]+)"
    _funcname = r"(" + _role + _funcbacktick + r"|" + _funcplain + r")"
    _funcnamenext = _funcname.replace("role", "rolenext")
    _funcnamenext = _funcnamenext.replace("name", "namenext")
    _description = r"(?P<description>\s*:(\s+(?P<desc>\S+.*))?)?\s*$"
    _func_rgx = re.compile(r"^\s*" + _funcname + r"\s*")
    _line_rgx = re.compile(
        r"^\s*"
        + r"(?P<allfuncs>"
        + _funcname  # group for all function names
        + r"(?P<morefuncs>([,]\s+"
        + _funcnamenext
        + r")*)"
        + r")"
        + r"(?P<trailing>[,\.])?"  # end of "allfuncs"
        + _description  # Some function lists have a trailing comma (or period)  '\s*'
    )

    # Empty <DESC> elements are replaced with '..'
    empty_description = ".."

    def _parse_see_also(self, content):
        """
        func_name : Descriptive text
            continued text
        another_func_name : Descriptive text
        func_name1, func_name2, :meth:`func_name`, func_name3

        """

        content = dedent_lines(content)

        items = []

        def parse_item_name(text):
            """Match ':role:`name`' or 'name'."""
            m = self._func_rgx.match(text)
            if not m:
                self._error_location(f"Error parsing See Also entry {line!r}")
            role = m.group("role")
            name = m.group("name") if role else m.group("name2")
            return name, role, m.end()

        rest = []
        for line in content:
            if not line.strip():
                continue

            line_match = self._lineine_rgx.match(line)
            description = None
            if line_match:
                description = line_match.group("desc")
                if line_match.group("trailing") and description:
                    self._error_location(
                        "Unexpected comma or period after function list at index %d of "
                        'line "%s"' % (line_match.end("trailing"), line),
                        error=False,
                    )
            if not description and line.startswith(" "):
                rest.append(line.strip())
            elif line_match:
                funcs = []
                text = line_match.group("allfuncs")
                while True:
                    if not text.strip():
                        break
                    name, role, match_end = parse_item_name(text)
                    funcs.append((name, role))
                    text = text[match_end:].strip()
                    if text and text[0] == ",":
                        text = text[1:].strip()
                rest = list(filter(None, [description]))
                items.append((funcs, rest))
            else:
                self._error_location(f"Error parsing See Also entry {line!r}")
        return items

    def _parse_index(self, section, content):
        """
        .. index: default
           :refguide: something, else, and more

        """

        def strip_each_in(lst):
            return [s.strip() for s in lst]

        out = {}
        section = section.split("::")
        if len(section) > 1:
            out["default"] = strip_each_in(section[1].split(","))[0]
        for line in content:
            line = line.split(":")
            if len(line) > 2:
                out[line[1]] = strip_each_in(line[2].split(","))
        return out

    def _parse_summary(self):
        """Grab signature (if given) and summary"""
        if self._is_at_section():
            return

        # If several signatures present, take the last one
        while True:
            summary = self._doc.read_to_next_empty_line()
            summary_str = " ".join([s.strip() for s in summary]).strip()
            compiled = re.compile(r"^([\w., ]+=)?\s*[\w\.]+\(.*\)$")
            if compiled.match(summary_str):
                self["Signature"] = summary_str
                if not self._is_at_section():
                    continue
            break

        if summary is not None:
            self["Summary"] = summary

        if not self._is_at_section():
            self["Extended Summary"] = self._read_to_next_section()

    def _parse(self):
        self._doc.reset()
        self._parse_summary()

        sections = list(self._read_sections())
        section_names = {section for section, content in sections}

        has_returns = "Returns" in section_names
        has_yields = "Yields" in section_names
        # We could do more tests, but we are not. Arbitrarily.
        if has_returns and has_yields:
            msg = "Docstring contains both a Returns and Yields section."
            raise ValueError(msg)
        if not has_yields and "Receives" in section_names:
            msg = "Docstring contains a Receives section but not Yields."
            raise ValueError(msg)

        for section, content in sections:
            if not section.startswith(".."):
                section = (s.capitalize() for s in section.split(" "))
                section = " ".join(section)
                if self.get(section):
                    self._error_location(
                        "The section %s appears twice in  %s"
                        % (section, "\n".join(self._doc._str))
                    )

            if section in ("Parameters", "Other Parameters", "Attributes", "Methods"):
                self[section] = self._parse_param_list(content)
            elif section in ("Returns", "Yields", "Raises", "Warns", "Receives"):
                self[section] = self._parse_param_list(
                    content, single_element_is_type=True
                )
            elif section.startswith(".. index::"):
                self["index"] = self._parse_index(section, content)
            elif section == "See Also":
                self["See Also"] = self._parse_see_also(content)
            else:
                self[section] = content

    @property
    def _obj(self):
        if hasattr(self, "_cls"):
            return self._cls
        elif hasattr(self, "_f"):
            return self._f
        return None

    def _error_location(self, msg, error=True):
        if self._obj is not None:
            # we know where the docs came from:
            try:
                filename = inspect.getsourcefile(self._obj)
            except TypeError:
                filename = None
            # Make UserWarning more descriptive via object introspection.
            # Skip if introspection fails
            name = getattr(self._obj, "__name__", None)
            if name is None:
                name = getattr(getattr(self._obj, "__class__", None), "__name__", None)
            if name is not None:
                msg += f" in the docstring of {name}"
            msg += f" in {filename}." if filename else ""
        if error:
            raise ValueError(msg)
        else:
            warn(msg)

    # string conversion routines

    def _str_header(self, name, symbol="-"):
        return [name, len(name) * symbol]

    def _str_indent(self, doc, indent=4):
        return [" " * indent + line for line in doc]

    def _str_signature(self):
        if self["Signature"]:
            return [self["Signature"].replace("*", r"\*")] + [""]
        return [""]

    def _str_summary(self):
        if self["Summary"]:
            return self["Summary"] + [""]
        return []

    def _str_extended_summary(self):
        if self["Extended Summary"]:
            return self["Extended Summary"] + [""]
        return []

    def _str_param_list(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            for param in self[name]:
                parts = []
                if param.name:
                    parts.append(param.name)
                if param.type_:
                    parts.append(param.type_)
                out += [" : ".join(parts)]
                if param.description and "".join(param.description).strip():
                    out += self._str_indent(param.description)
            out += [""]
        return out

    def _str_section(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            out += self[name]
            out += [""]
        return out

    def _str_see_also(self, func_role):
        if not self["See Also"]:
            return []
        out = []
        out += self._str_header("See Also")
        out += [""]
        last_had_desc = True
        for funcs, desc in self["See Also"]:
            assert isinstance(funcs, list)
            links = []
            for func, role in funcs:
                if role:
                    link = f":{role}:`{func}`"
                elif func_role:
                    link = f":{func_role}:`{func}`"
                else:
                    link = f"`{func}`_"
                links.append(link)
            link = ", ".join(links)
            out += [link]
            if desc:
                out += self._str_indent([" ".join(desc)])
                last_had_desc = True
            else:
                last_had_desc = False
                out += self._str_indent([self.empty_description])

        if last_had_desc:
            out += [""]
        out += [""]
        return out

    def _str_index(self):
        idx = self["index"]
        out = []
        output_index = False
        default_index = idx.get("default", "")
        if default_index:
            output_index = True
        out += [f".. index:: {default_index}"]
        for section, references in idx.items():
            if section == "default":
                continue
            output_index = True
            out += [f"   :{section}: {', '.join(references)}"]
        if output_index:
            return out
        return ""

    def __str__(self, func_role=""):
        out = []
        out += self._str_signature()
        out += self._str_summary()
        out += self._str_extended_summary()
        for param_list in (
                "Parameters",
                "Returns",
                "Yields",
                "Receives",
                "Other Parameters",
                "Raises",
                "Warns",
        ):
            out += self._str_param_list(param_list)
        out += self._str_section("Warnings")
        out += self._str_see_also(func_role)
        for s in ("Notes", "References", "Examples"):
            out += self._str_section(s)
        for param_list in ("Attributes", "Methods"):
            out += self._str_param_list(param_list)
        out += self._str_index()
        return "\n".join(out)


def dedent_lines(lines):
    """Deindent a list of lines maximally"""
    return textwrap.dedent("\n".join(lines)).split("\n")


class FunctionDoc(NumpyDocString):
    def __init__(self, func, role="func", doc=None, config=None):
        self._f = func
        self._role = role  # e.g. "func" or "meth"

        if doc is None:
            if func is None:
                raise ValueError("No function or docstring given")
            doc = inspect.getdoc(func) or ""
        if config is None:
            config = {}
        NumpyDocString.__init__(self, doc, config)

    def get_func(self):
        func_name = getattr(self._f, "__name__", self.__class__.__name__)
        if inspect.isclass(self._f):
            func = getattr(self._f, "__call__", self._f.__init__)
        else:
            func = self._f
        return func, func_name

    def __str__(self):
        out = ""

        func, func_name = self.get_func()

        roles = {"func": "function", "meth": "method"}

        if self._role:
            if self._role not in roles:
                print(f"Warning: invalid role {self._role}")
            out += f".. {roles.get(self._role, '')}:: {func_name}\n    \n\n"

        out += super().__str__(func_role=self._role)
        return out


class ObjDoc(NumpyDocString):
    def __init__(self, obj, doc=None, config=None):
        self._f = obj
        if config is None:
            config = {}
        NumpyDocString.__init__(self, doc, config=config)


class ClassDoc(NumpyDocString):
    extra_public_methods = ["__call__"]

    def __init__(self, cls, doc=None, modulename="", func_doc=FunctionDoc, config=None):
        if not inspect.isclass(cls) and cls is not None:
            raise ValueError(f"Expected a class or None, but got {cls!r}")
        self._cls = cls

        if "sphinx" in sys.modules:
            from sphinx.ext.autodoc import ALL
        else:
            ALL = object()

        if config is None:
            config = {}
        self.show_inherited_members = config.get("show_inherited_class_members", True)

        if modulename and not modulename.endswith("."):
            modulename += "."
        self._mod = modulename

        if doc is None:
            if cls is None:
                raise ValueError("No class or documentation string given")
            doc = pydoc.getdoc(cls)

        NumpyDocString.__init__(self, doc)

        _members = config.get("members", [])
        if _members is ALL:
            _members = None
        _exclude = config.get("exclude-members", [])

        if config.get("show_class_members", True) and _exclude is not ALL:

            def splitlines_x(s):
                if not s:
                    return []
                else:
                    return s.splitlines()

            for field, items in [
                ("Methods", self.methods),
                ("Attributes", self.properties),
            ]:
                if not self[field]:
                    doc_list = []
                    for name in sorted(items):
                        if name in _exclude or (_members and name not in _members):
                            continue
                        try:
                            doc_item = pydoc.getdoc(getattr(self._cls, name))
                            doc_list.append(Parameter(name, "", splitlines_x(doc_item)))
                        except AttributeError:
                            pass  # method doesn't exist
                    self[field] = doc_list

    @property
    def methods(self):
        if self._cls is None:
            return []
        return [
            name
            for name, func in inspect.getmembers(self._cls)
            if (
                    (not name.startswith("_") or name in self.extra_public_methods)
                    and isinstance(func, Callable)
                    and self._is_show_member(name)
            )
        ]

    @property
    def properties(self):
        if self._cls is None:
            return []
        return [
            name
            for name, func in inspect.getmembers(self._cls)
            if (
                    not name.startswith("_")
                    and (
                            func is None
                            or isinstance(func, (property, cached_property))
                            or inspect.isdatadescriptor(func)
                    )
                    and self._is_show_member(name)
            )
        ]

    def _is_show_member(self, name):
        if self.show_inherited_members:
            return True  # show all class members
        if name not in self._cls.__dict__:
            return False  # class member is inherited, we do not show it
        return True


def get_doc_object(
        obj,
        what=None,
        doc=None,
        config=None,
        class_doc=ClassDoc,
        func_doc=FunctionDoc,
        obj_doc=ObjDoc,
) -> NumpyDocString:
    if what is None:
        if inspect.isclass(obj):
            what = "class"
        elif inspect.ismodule(obj):
            what = "module"
        elif isinstance(obj, Callable):
            what = "function"
        else:
            what = "object"
    if config is None:
        config = {}

    if what == "class":
        return class_doc(obj, func_doc=func_doc, doc=doc, config=config)
    elif what in ("function", "method"):
        return func_doc(obj, doc=doc, config=config)
    else:
        if doc is None:
            doc = pydoc.getdoc(obj)
        return obj_doc(obj, doc, config=config)


def add_type_hints_to_doc_dict(function: callable, doc: NumpyDocString):
    type_hints = typing.get_type_hints(function)
    if type_hints:
        add_return(type_hints, doc)  # run first to pop off returns from type_hints
        add_parameter(type_hints, doc)


def add_parameter(type_hints: dict, doc: NumpyDocString):
    if not type_hints:
        return

    # if "Parameters" not in doc:
    #     doc["Parameters"] = []

    # doc_param = doc_dict["Parameters"]
    doc_param_names = [p.name for p in doc.parameters]
    for i, param in enumerate(type_hints):
        if param in doc_param_names:
            doc.parameters[i].type_ = type_hints[param].__name__
        else:
            doc.parameters.append(Parameter(param, type(param).__name__, ""))


def add_return(type_hints: dict, doc: NumpyDocString):
    if 'return' not in type_hints:
        return

    return_param = breakup_type(type_hints.pop("return"))

    # if "Returns" not in doc_dict:
    #     doc_dict["Returns"] = []

    length = len(doc.returns) - 1
    for i, param in enumerate(return_param):
        # if no parameters, or more parameter than in docstring; add them
        if i > length:
            doc.returns.append(Parameter(f"return_{i}", param.__name__, ""))
        else:
            doc_param: Parameter = doc.returns[i]
            doc_param.type_ = param.__name__


def breakup_type(type_: type) -> tuple[type, ...] | list[type, ...]:
    if isinstance(type_, types.UnionType):
        return type_.__args__

    if type_.__name__ == "tuple" or type_.__name__ == "list":
        return type_.__args__

    return (type_,)


def get_numpy_style_docstring(func: callable) -> NumpyDocString:
    result = get_doc_object(func)
    add_type_hints_to_doc_dict(func, result)

    return result


#######################################################################################################################
#######################################################################################################################

def local_run():
    class Equip:
        def __init__(self):
            self.a = 1

        def read_status(self):
            pass

        def _read_status(self) -> str:
            """
            read status
            all functions have this

            Returns
            -------
            status:
                current equipment status

            """
            return "str"

        def _write_status(self, status):
            """
            read status
            all functions have this

            Returns
            -------
            status: str, int
                current equipment status

            """
            return "str"

        # def _read_none(self):
        #     a = 1

    class Light(Equip):
        def __init__(self):
            super().__init__()
            self._b = "stuff"

        def write_power(self, text: str):
            """ pass"""
            self._write_power(power=0.1)

        def _write_power(self, power: float):
            """
            write power

            Parameters
            ----------
            power:
                light power
                range: [0, 1]


            """
            a = 1

        def _read_comm(self) -> tuple[str, int, list[int, ...]]:
            """
            read_comm
            """
            pass

    class_ = Light
    funcs = [func for func in dir(class_) if
             callable(getattr(class_, func)) and (func.startswith("_read") or func.startswith("_write"))]
    print(funcs)

    for func in funcs:
        func = getattr(class_, func)
        result = get_numpy_style_docstring(func)
        print(result)
        print("")


if __name__ == "__main__":
    local_run()
