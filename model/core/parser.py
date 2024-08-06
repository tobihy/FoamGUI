import re

import pyparsing as pp
from pyparsing import (
    CharsNotIn,
    Combine,
    Literal,
    OneOrMore,
    ParseException,
    SkipTo,
    StringEnd,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    nums,
)

from model.core.values import Scalar, Tensor, Value
from model.custom_ordered_dict import CustomOrderedDict


class FoamCommentParser:
    def __init__(self) -> None:
        # Regex pattern for start comment
        # self.pattern = re.compile(
        #     r"/\*-*?\*-[\s*\S*]*?-\*-*?\*\\.*?\\\*-*?\*/",
        #     re.DOTALL,
        # )
        self.forward_star = pp.Literal("/*")
        self.backward_star = pp.Literal("\\*")
        self.star = pp.Literal("*")
        self.star_forward = pp.Literal("*/")
        self.star_backward = pp.Literal("*\\")
        self.dash = pp.Literal("-")
        self.star_dash = pp.Literal("*-")
        self.dash_star = pp.Literal("-*")

    def create_parser(self):
        self.expression = pp.Combine(
            self.forward_star
            + pp.OneOrMore(self.dash)
            + self.star_dash
            + pp.SkipTo(self.dash_star, include=True)
            + pp.OneOrMore(self.dash)
            + self.star_backward
            + pp.SkipTo(self.backward_star, include=True)
            + pp.OneOrMore(self.dash)
            + self.star_forward
        )

        comment_parser = self.expression.set_name(
            "start comment header"
        ).set_parse_action("".join)

        return comment_parser


class FoamDataHeaderParser:
    def __init__(self) -> None:
        # Regex pattern for data header
        self.pattern = re.compile(r"FoamFile\s*\{\s*(.*?)\s*\}", re.DOTALL)
        self.custom_alphanums = pp.alphanums + "_:.#$*/,<>"

        # Define a simple parser for key-value pairs
        self.key = pp.Word(self.custom_alphanums)
        self.value = pp.Word(self.custom_alphanums) | pp.dbl_quoted_string
        self.key_value_pair = self.key + self.value + pp.Suppress(";")

        self.foam_file_content = pp.ZeroOrMore(
            pp.Group(self.key_value_pair)
        ).set_parse_action(lambda toks: CustomOrderedDict(toks.as_list()))

        self.expression = (
            pp.Suppress("FoamFile")
            + pp.Suppress("{")
            + self.foam_file_content
            + pp.Suppress("}")
        )

    def create_parser(self):
        return self.expression.set_parse_action(lambda toks: toks.as_list())

    def create_remover(self):
        return self.expression.set_parse_action(lambda: "")


class ScalarValueParser:
    def __init__(self) -> None:
        self.sci_real_pattern = r"[+-]?\d+\.?\d*[eE][+-]?\d+"
        self.sci_real = (
            pp.Regex(self.sci_real_pattern)
            .set_name("scientific real number")
            .set_parse_action("".join)
        )

        self.scalar = (
            self.sci_real | pp.pyparsing_common.real | pp.pyparsing_common.integer
        )
        self.uniform_scalar = pp.Keyword("uniform") + self.scalar
        self.nonuniform_scalar = pp.Keyword("nonuniform") + self.scalar
        self.default_scalar = self.scalar
        self.expression = (
            self.uniform_scalar | self.nonuniform_scalar | self.default_scalar
        ) + StringEnd()  # ensures that after parsing, we are at the end of the string

    def parse_action(self, toks):
        try:
            if toks[0] == "uniform":
                return Value(True, Scalar(toks[1]))
            elif toks[0] == "nonuniform":
                return Value(False, Scalar(toks[1]))
            else:
                return Scalar(toks[0])
        except Exception as e:
            raise ParseException(f"Failed to parse scalar: {e}")

    def create_parser(self):
        return self.expression.set_parse_action(self.parse_action)


class VectorValueParser:
    def __init__(self) -> None:
        self.vector = pp.Group(
            pp.Suppress("(")
            + pp.DelimitedList(pp.pyparsing_common.number * 3, delim=pp.White())
            + pp.Suppress(")")
        )

        self.uniform_vector = pp.Keyword("uniform") + self.vector
        self.nonuniform_vector = pp.Keyword("nonuniform") + self.vector
        self.default_vector = self.vector
        self.vector_value = (
            self.uniform_vector | self.nonuniform_vector | self.default_vector
        )

    def create_parser(self):
        return self.vector_value.set_parse_action(
            lambda toks: (
                Value(True, Tensor(toks.as_list()[1]))
                if len(toks) > 1 and toks[0] == "uniform"
                else (
                    Value(False, Tensor(toks.as_list()[1]))
                    if len(toks) > 1 and toks[0] == "nonuniform"
                    else Tensor(toks.as_list()[0])
                )
            )
        )
