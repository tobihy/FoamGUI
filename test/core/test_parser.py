from unittest.mock import MagicMock, patch

import pytest
from pyparsing import (
    Forward,
    Group,
    Literal,
    ParseException,
    ParserElement,
    ParseResults,
    Word,
    ZeroOrMore,
    nums,
)

from model.core.parser import (
    FoamCommentParser,
    FoamDataHeaderParser,
    ScalarValueParser,
    VectorValueParser,
)
from model.core.values import Scalar, Tensor, Value
from model.custom_ordered_dict import CustomOrderedDict


@pytest.fixture
def comment_parser():
    yield FoamCommentParser().create_parser()


@pytest.fixture
def data_header_parser():
    yield FoamDataHeaderParser().create_parser()


@pytest.fixture
def scalar_value_parser():
    yield ScalarValueParser().create_parser()


@pytest.fixture
def vector_value_parser():
    yield VectorValueParser().create_parser()


def list_helper(
    parser: ParserElement,
    valid_tests: list,
    expected_outputs: list,
    invalid_tests: list,
):
    for i in range(len(valid_tests)):
        assert parser.parse_string(valid_tests[i]).as_list()[0] == expected_outputs[i]

    for test_str in invalid_tests:
        with pytest.raises(ParseException):
            parser.parse_string(test_str)


def dict_helper(
    parser: ParserElement,
    valid_tests: list,
    expected_outputs: list,
    invalid_tests: list,
):
    for i in range(len(valid_tests)):
        test_str = valid_tests[i]
        parse_res = parser.parse_string(test_str)
        assert parse_res[0] == expected_outputs[i]

    for test_str in invalid_tests:
        with pytest.raises(ParseException):
            parser.parse_string(test_str)


def test_comment_parser(comment_parser):
    valid_tests = [
        """/*--------------------------------*- C++ -*----------------------------------*\\
           |      =========                  |                                           |
           |     \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox     |
           |      \\\\    /   O peration     | Website:  https://openfoam.org            |
           |       \\\\  /    A nd           | Version:  6                               |
           |        \\\\/     M anipulation  |                                           |
           \\*---------------------------------------------------------------------------*/"""
    ]

    invalid_tests = [
        """/*---------------------------------- C++ ------------------------------------*\\
           |      =========                  |                                           |
           |     \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox     |
           |      \\\\    /   O peration     | Website:  https://openfoam.org            |
           |       \\\\  /    A nd           | Version:  6                               |
           |        \\\\/     M anipulation  |                                           |
           \\*---------------**------------------**----------------------------**--------*/"""
    ]

    list_helper(comment_parser, valid_tests, valid_tests, invalid_tests)


def test_data_header_parser(data_header_parser):
    valid_tests = [
        """FoamFile
            {
                version     2.0;
                format      ascii;
                class       dictionary;
                object      fvSolution;
            }"""
    ]

    expected_outputs = [
        CustomOrderedDict(
            {
                "version": "2.0",
                "format": "ascii",
                "class": "dictionary",
                "object": "fvSolution",
            }
        )
    ]

    invalid_tests = [
        """FoamFile
            (
                version     2.0;
                format      ascii;
                class       dictionary;
                object      fvSolution;
            )""",
        """FoamFile
            [
                version     2.0;
                format      ascii;
                class       dictionary;
                object      fvSolution;
            ]""",
    ]

    dict_helper(data_header_parser, valid_tests, expected_outputs, invalid_tests)


@pytest.mark.parametrize(
    "input_string, expected_value",
    [
        ("1.23e-4", "1.23e-4"),
        ("-1.2e+3", "-1.2e+3"),
        ("0.87e-2", "0.87e-2"),
        ("+7.8E+12", "+7.8E+12"),
        ("9e6", "9e6"),
        ("-4.56789e-8", "-4.56789e-8"),
    ],
)
def test_parse_scientific_real(input_string, expected_value, scalar_value_parser):
    # Setup the mock to return a specific value
    mock_scalar_instance = MagicMock(spec=Scalar)
    mock_scalar_instance.value = expected_value

    with patch(
        "model.core.parser.Scalar", return_value=mock_scalar_instance
    ) as mock_scalar_class:
        # Call the parser
        result = scalar_value_parser.parse_string(input_string)

        # Assert Scalar is called once
        mock_scalar_class.assert_called_once_with(input_string)

        # Verify the result is the mock instance
        assert result.as_list()[0] == mock_scalar_instance


@pytest.mark.parametrize(
    "input_string",
    [
        "1.2.3",  # Invalid input (multiple decimal points)
        "1.23e",  # Invalid input (incomplete scientific notation)
        "1.23e-",  # Invalid input (incomplete scientific notation)
        "1.23e+",  # Invalid input (incomplete scientific notation)
        "",  # Empty input
    ],
)
def test_parse_scientific_invalid(scalar_value_parser, input_string):
    with pytest.raises(ParseException):
        scalar_value_parser.parseString(input_string)


@pytest.mark.parametrize(
    "input_string, expected_value",
    [("(0.0 0.0 0.0)", [0.0, 0.0, 0.0]), ("(1 2 3)", [1, 2, 3])],
)
def test_parse_vector(input_string, expected_value, vector_value_parser):
    # Setup the mocks
    mock_vector_instance = MagicMock(spec=Tensor)
    mock_vector_instance.value = expected_value

    with patch(
        "model.core.parser.Tensor", return_value=mock_vector_instance
    ) as mock_vector_class:
        # Call the parser
        result = vector_value_parser.parse_string(input_string)

        # Assert Scalar is called once
        mock_vector_class.assert_called_once_with(
            expected_value
        )  # List is first processed by pyparsing.delimitedList

        # Verify the result is the mock instance
        assert result.as_list()[0] == mock_vector_instance
