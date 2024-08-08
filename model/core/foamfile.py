import os
import re
from pathlib import Path

import pyparsing as pp
from pyparsing import ParseResults

from model.core.dimensioned_scalar import DimensionedScalar
from model.core.list import List
from model.core.parser import (
    FoamCommentParser,
    FoamDataHeaderParser,
    ScalarValueParser,
    VectorValueParser,
)
from model.custom_ordered_dict import CustomOrderedDict


# Adapted from OpenFOAM file parser made by napyk
# GitHub link: https://github.com/napyk/foamfile
class FoamFile:
    def __init__(self, path, mode="r", foam_class=None):
        self.mode = mode
        self.path = path
        self.file = None
        self.header = CustomOrderedDict(
            [
                ("version", 2.0),
                ("format", "ascii"),
                ("object", Path(path).name),
                ("class", foam_class),
            ]
        )
        self.start_comment = [
            "/*--------------------------------*- C++ -*----------------------------------*\\",
            "  =========                   |",
            "  \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox",
            "   \\\\    /   O peration     | Website:  https://openfoam.org",
            "    \\\\  /    A nd           | Version:  6",
            "     \\\\/     M anipulation  |",
            "\\*---------------------------------------------------------------------------*/\n",
        ]
        self.spacer = [
            "\n// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n"
        ]
        self.end_comment = [
            "\n// ************************************************************************* //\n"
        ]

    def __enter__(self):
        self.file = open(self.path, self.mode)
        return self

    def __exit__(self, *args, **kwargs):
        if self.file:
            self.file.close()

    def set_header(
        self,
        file_name: str,
        version: float = 2.0,
        format: str = "ascii",
        cls: str = "dictionary",
    ):
        self.header = CustomOrderedDict(
            [
                ("version", version),
                ("format", format),
                ("object", file_name),
                ("class", cls),
            ]
        )

    def remove_comments(self, string):
        # /* COMMENT */
        # pp.cStyleComment
        string = re.sub(re.compile("/\\*.*?\\*/", re.DOTALL), "", string)
        # // COMMENT
        # pp.dblSlashComment
        string = re.sub(re.compile("//.*?\n"), "", string)
        return string

    def extract_start_comment(self, text):
        # Regex pattern for start comment
        start_pattern = re.compile(
            r"/\*-*?\*-[\s*\S*]*?-\*-*?\*\\.*?\\\*-*?\*/",
            re.DOTALL,
        )

        # Search for comment in text
        parser = FoamCommentParser().create_parser()
        self.start_comment = str.split(parser.parse_string(text).as_list()[0], "\n")
        return text

    def extract_and_remove_header(self, text):
        # Parse and remove header from text
        data_header_parser = FoamDataHeaderParser()
        parser = data_header_parser.create_parser()
        self.header: CustomOrderedDict = parser.parse_string(text).as_list()[0]

        remover = data_header_parser.create_remover()
        text = remover.transform_string(text)
        return text

    def from_foam(self, text) -> ParseResults:
        dictionary_value = pp.Forward()
        list_element = pp.Forward()

        custom_alphanums = pp.alphanums + "_:.#$*/,<>|"

        enclosed_function = pp.Forward()
        function = (
            "(" + pp.ZeroOrMore(pp.Word(custom_alphanums) | enclosed_function) + ")"
        )
        named_function = pp.Combine(
            pp.Word(custom_alphanums)
            + "("
            + pp.ZeroOrMore(pp.Word(custom_alphanums) | function)
            + ")"
        )
        enclosed_function << function  # type: ignore

        field_match_string = pp.Combine(
            pp.Literal('"')
            + pp.Literal("(")
            + pp.DelimitedList(pp.Word(custom_alphanums), delim="|", combine=True)
            + pp.Literal(")")
            + pp.Literal(".*")
            + pp.Literal('"')
        )

        custom_quoted_string = pp.Combine(
            pp.Literal('"') + pp.Word(custom_alphanums) + pp.Literal('"')
        )

        dictionary_key = (
            named_function
            | field_match_string
            | custom_quoted_string
            | pp.Word(custom_alphanums)
        )

        dictionary_key_value = pp.Group(
            dictionary_key + pp.Suppress(pp.White()) + dictionary_value
        ) + pp.Suppress(pp.Optional(";"))

        dictionary_standalone_value = (
            dictionary_value + pp.Suppress(pp.Optional(";"))
        ).set_parse_action(lambda toks: [[toks[0], None]])

        dictionary_entry = dictionary_key_value | dictionary_standalone_value

        dictionary_entries = pp.ZeroOrMore(dictionary_entry).add_parse_action(
            lambda toks: CustomOrderedDict(toks.as_list())
        )

        dictionary_object = pp.Suppress("{") + dictionary_entries + pp.Suppress("}")

        named_dictionary_object = pp.Group(
            pp.Word(custom_alphanums) + pp.Suppress(pp.White()) + dictionary_object
        ) + pp.Suppress(pp.Optional(";"))

        list_object = (
            pp.Suppress("(")
            + pp.ZeroOrMore(pp.Group(pp.DelimitedList(list_element, delim=pp.White())))
            + pp.Suppress(")")
        ).set_parse_action(lambda toks: [List(toks.as_list()[0])] if toks else [List()])

        # TODO add token identifier
        named_list_object = pp.Word(custom_alphanums) + list_object + pp.Suppress(";")

        # directives
        # TODO #include filename
        # directive = pp.Regex("#([^\s]+)") + custom_quoted_string

        # [0 2 -1 0 0 0 0]
        dimension_set = (
            pp.Suppress("[")
            + pp.DelimitedList(pp.pyparsing_common.number * 7, delim=pp.White())
            + pp.Suppress("]")
        ).set_parse_action(lambda toks: DimensionedScalar(toks.as_list()))

        # scalars
        scalar_value_parser = ScalarValueParser().create_parser()

        # vectors
        vector_value_parser = VectorValueParser().create_parser()

        field_value = scalar_value_parser | vector_value_parser

        dictionary_value << (
            (
                (
                    pp.OneOrMore(
                        named_function
                        | field_value
                        | dimension_set
                        | pp.pyparsing_common.number
                        | pp.Word(custom_alphanums)
                    ).set_parse_action(
                        lambda toks: (
                            " ".join([str(i) for i in toks])
                            if len(toks) > 1
                            else toks[0]
                        )
                    )
                    | custom_quoted_string
                    | list_object
                )
                + pp.Suppress(";")
            )
            | (dictionary_object + pp.Suppress(pp.Optional(";")))
            | custom_quoted_string
        )  # type: ignore

        list_element << (
            named_dictionary_object
            | list_object
            | pp.pyparsing_common.number
            | pp.Word(custom_alphanums)
        )  # type: ignore

        combined = dictionary_entries | named_list_object | named_dictionary_object
        return combined.parse_string(text)  # parse all text

    def read(self):
        if self.file is None:
            self.file = open(self.path, self.mode)
        text = self.file.read()
        text = self.extract_start_comment(text)
        text = self.remove_comments(text)
        text = self.extract_and_remove_header(text)
        text = self.from_foam(text)
        self.close()
        return text[0]

    def to_foam(
        self,
        foam_object=None,
        level=0,
        maxlength=50,
    ):
        if not foam_object:
            return []

        lines = []

        if type(foam_object) in (list, tuple):
            for list_entry in foam_object:
                if type(list_entry) in (list, tuple):
                    lines.append(
                        "\t" * level + "(" + " ".join(self.to_foam(list_entry, 0)) + ")"
                    )
                elif type(list_entry) in (dict, CustomOrderedDict):
                    lines.append("\t" * level + "{")
                    lines += self.to_foam(list_entry, level + 1)
                    lines.append("\t" * level + "}")
                else:
                    lines.append("\t" * level + str(list_entry))
        elif type(foam_object) in (dict, CustomOrderedDict):
            if len(foam_object) > 0:
                tab_expander = max([len(i) for i in foam_object if type(i) is str]) + 1
            for key, value in foam_object.items():
                if type(value) in (dict, CustomOrderedDict):
                    lines += ["\t" * level + f"{key}", "\t" * level + "{"]
                    lines += self.to_foam(value, level + 1)
                    lines.append("\t" * level + "}")
                elif type(value) in (list, tuple):
                    lines += ["\t" * level + f"{key}", "\t" * level + "("]
                    lines += self.to_foam(value, level + 1)
                    lines.append("\t" * level + ");")
                else:
                    if key in [
                        "#include",
                        "#includeIfPresent",
                        "#includeEtc",
                        "#includeFunc",
                        "#remove",
                    ]:
                        lines.append(
                            "\t" * level + str(key).ljust(tab_expander) + str(value)
                        )
                    elif not value:
                        # flag-type object
                        if key:
                            lines.append("\t" * level + str(key) + ";")
                    else:
                        lines.append(
                            "\t" * level
                            + str(key).ljust(tab_expander)
                            + str(value)
                            + ";"
                        )
        return lines

    def write(self, content=None):
        if self.file is None:
            self.file = open(self.path, "w")
        os.makedirs(os.path.abspath(os.path.dirname(self.path)), exist_ok=True)
        self.file.write(
            "\n".join(
                self.start_comment
                + self.to_foam({"FoamFile": self.header})
                + self.spacer
                + self.to_foam(content)
                + self.end_comment
            )
        )
        self.close()

    def close(self):
        if self.file:
            self.file.close()
            self.file = None
