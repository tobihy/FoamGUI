import pytest

from model.custom_ordered_dict import CustomOrderedDict


@pytest.fixture
def simple_odict():
    return CustomOrderedDict(
        {"a": 1, "b": CustomOrderedDict({"ba": 21, "bb": 22}), "c": 3}
    )


@pytest.fixture
def complex_odict():
    return CustomOrderedDict(
        {
            "0": CustomOrderedDict(
                {
                    "U": CustomOrderedDict(
                        {
                            "dimensions": "[0 1 -1 0 0 0 0]",
                            "internalField": "uniform ( 8.07 0 0 )",
                            "boundaryField": CustomOrderedDict(
                                {
                                    "airinlet": CustomOrderedDict(
                                        {
                                            "type": "surfaceNormalFixedValue",
                                            "refValue": "uniform -15.32",
                                        }
                                    ),
                                    "waterinlet": CustomOrderedDict(
                                        {
                                            "type": "fixedValue",
                                            "value": "$internalField",
                                        }
                                    ),
                                    "outlet": CustomOrderedDict(
                                        {
                                            "type": "pressureInletOutletVelocity",
                                            "value": "$internalField",
                                        }
                                    ),
                                    "model": CustomOrderedDict({"type": "noSlip"}),
                                    "symmetry": CustomOrderedDict({"type": "symmetry"}),
                                    "side": CustomOrderedDict({"type": "slip"}),
                                }
                            ),
                        }
                    )
                }
            ),
            "system": CustomOrderedDict(
                {
                    "controlDict": CustomOrderedDict(
                        {
                            "application": "<application>",
                            "startFrom": "startTime",
                            "startTime": 0,
                            "stopAt": "endTime",
                            "endTime": 10,
                            "deltaT": 0.005,
                            "writeControl": "timeStep",
                            "writeInterval": 100,
                            "purgeWrite": 1,
                            "writeFormat": "binary",
                            "writePrecision": 6,
                            "writeCompression": "off",
                            "timeFormat": "general",
                            "timePrecision": 6,
                            "adjustTimeStep": "no",
                            "runTimeModifiable": "true",
                            "functions": {},
                        }
                    )
                }
            ),
            "constant": CustomOrderedDict(
                {
                    "transportProperties": CustomOrderedDict(
                        {
                            "transportModel": "Newtonian",
                            "nu": "nu [0 2 -1 0 0 0 0] 1e-06",
                            "alpha": "alpha [0 2 -1 0 0 0 0] 0",
                            "Pr": "Pr [0 0 0 0 0 0 0] 0.7",
                        }
                    )
                }
            ),
        }
    )


def get_nested_value(key_path: list[str], odict: CustomOrderedDict):
    curr = odict
    for key in key_path:
        if key not in curr:
            raise KeyError(f"Key {key} not found.")
        curr = curr[key]
    return curr


def test_update_nested_value_valid(simple_odict):
    simple_odict.update_nested_value(["b"], "ba", "updated_value")
    assert get_nested_value(["b", "ba"], simple_odict) == "updated_value"


def test_update_nested_value_invalid_key(simple_odict):
    with pytest.raises(KeyError):
        simple_odict.update_nested_value(["b"], "bc", "updated_value")


def test_update_nested_value_invalid_path(simple_odict):
    with pytest.raises(KeyError):
        simple_odict.update_nested_value(["d"], "da", "updated_value")


def test_update_nested_value_invalid_root_key(simple_odict):
    with pytest.raises(KeyError):
        simple_odict.update_nested_value([], "d", "updated_value")


def test_update_nested_value_valid_complex(complex_odict):
    complex_odict.update_nested_value(
        ["0", "U", "boundaryField", "airinlet"], "type", "fixedValue"
    )
    assert (
        complex_odict.get_nested_value(["0", "U", "boundaryField", "airinlet", "type"])
        == "fixedValue"
    )


def test_update_nested_value_invalid_key_complex(complex_odict):
    with pytest.raises(KeyError):
        complex_odict.update_nested_value(
            ["0", "U", "boundaryField", "waterinlet"], "refValue", "fixedValue"
        )


def test_update_nested_value_invalid_path_complex(complex_odict):
    with pytest.raises(KeyError):
        complex_odict.update_nested_value(["a", "b"], "c", "hello")


def test_rename_key_simple(simple_odict):
    actual = simple_odict.rename_key([], "b", "new_b")
    expected = CustomOrderedDict(
        {"a": 1, "new_b": CustomOrderedDict({"ba": 21, "bb": 22}), "c": 3}
    )
    assert expected == actual


def test_rename_key_complex(complex_odict):
    actual = complex_odict.rename_key(["0", "U"], "dimensions", "d")
    expected = CustomOrderedDict(
        {
            "d": "[0 1 -1 0 0 0 0]",
            "internalField": "uniform ( 8.07 0 0 )",
            "boundaryField": CustomOrderedDict(
                {
                    "airinlet": CustomOrderedDict(
                        {
                            "type": "surfaceNormalFixedValue",
                            "refValue": "uniform -15.32",
                        }
                    ),
                    "waterinlet": CustomOrderedDict(
                        {
                            "type": "fixedValue",
                            "value": "$internalField",
                        }
                    ),
                    "outlet": CustomOrderedDict(
                        {
                            "type": "pressureInletOutletVelocity",
                            "value": "$internalField",
                        }
                    ),
                    "model": CustomOrderedDict({"type": "noSlip"}),
                    "symmetry": CustomOrderedDict({"type": "symmetry"}),
                    "side": CustomOrderedDict({"type": "slip"}),
                }
            ),
        }
    )
    assert expected == actual


def test_insert_before_simple(simple_odict):
    simple_odict.insert([], "cc", 33, "c")
    actual = simple_odict
    expected = CustomOrderedDict(
        {"a": 1, "b": CustomOrderedDict({"ba": 21, "bb": 22}), "cc": 33, "c": 3}
    )
    assert expected == actual


def test_insert_before_complex(complex_odict):
    complex_odict.insert(
        ["0", "U", "boundaryField", "airinlet"], "test", "example", "refValue"
    )
    actual = complex_odict
    expected = CustomOrderedDict(
        {
            "0": CustomOrderedDict(
                {
                    "U": CustomOrderedDict(
                        {
                            "dimensions": "[0 1 -1 0 0 0 0]",
                            "internalField": "uniform ( 8.07 0 0 )",
                            "boundaryField": CustomOrderedDict(
                                {
                                    "airinlet": CustomOrderedDict(
                                        {
                                            "type": "surfaceNormalFixedValue",
                                            "test": "example",
                                            "refValue": "uniform -15.32",
                                        }
                                    ),
                                    "waterinlet": CustomOrderedDict(
                                        {
                                            "type": "fixedValue",
                                            "value": "$internalField",
                                        }
                                    ),
                                    "outlet": CustomOrderedDict(
                                        {
                                            "type": "pressureInletOutletVelocity",
                                            "value": "$internalField",
                                        }
                                    ),
                                    "model": CustomOrderedDict({"type": "noSlip"}),
                                    "symmetry": CustomOrderedDict({"type": "symmetry"}),
                                    "side": CustomOrderedDict({"type": "slip"}),
                                }
                            ),
                        }
                    )
                }
            ),
            "system": CustomOrderedDict(
                {
                    "controlDict": CustomOrderedDict(
                        {
                            "application": "<application>",
                            "startFrom": "startTime",
                            "startTime": 0,
                            "stopAt": "endTime",
                            "endTime": 10,
                            "deltaT": 0.005,
                            "writeControl": "timeStep",
                            "writeInterval": 100,
                            "purgeWrite": 1,
                            "writeFormat": "binary",
                            "writePrecision": 6,
                            "writeCompression": "off",
                            "timeFormat": "general",
                            "timePrecision": 6,
                            "adjustTimeStep": "no",
                            "runTimeModifiable": "true",
                            "functions": {},
                        }
                    )
                }
            ),
            "constant": CustomOrderedDict(
                {
                    "transportProperties": CustomOrderedDict(
                        {
                            "transportModel": "Newtonian",
                            "nu": "nu [0 2 -1 0 0 0 0] 1e-06",
                            "alpha": "alpha [0 2 -1 0 0 0 0] 0",
                            "Pr": "Pr [0 0 0 0 0 0 0] 0.7",
                        }
                    )
                }
            ),
        }
    )
    assert expected == actual


def test_insert_after_simple(simple_odict):
    simple_odict.insert([], "cc", 33, "c", after=True)
    actual = simple_odict
    expected = CustomOrderedDict(
        {"a": 1, "b": CustomOrderedDict({"ba": 21, "bb": 22}), "c": 3, "cc": 33}
    )
    assert expected == actual


def test_insert_after_complex(complex_odict):
    complex_odict.insert(
        ["0", "U", "boundaryField", "airinlet"],
        "test",
        "example",
        "refValue",
        after=True,
    )
    actual = complex_odict
    expected = CustomOrderedDict(
        {
            "0": CustomOrderedDict(
                {
                    "U": CustomOrderedDict(
                        {
                            "dimensions": "[0 1 -1 0 0 0 0]",
                            "internalField": "uniform ( 8.07 0 0 )",
                            "boundaryField": CustomOrderedDict(
                                {
                                    "airinlet": CustomOrderedDict(
                                        {
                                            "type": "surfaceNormalFixedValue",
                                            "refValue": "uniform -15.32",
                                            "test": "example",
                                        }
                                    ),
                                    "waterinlet": CustomOrderedDict(
                                        {
                                            "type": "fixedValue",
                                            "value": "$internalField",
                                        }
                                    ),
                                    "outlet": CustomOrderedDict(
                                        {
                                            "type": "pressureInletOutletVelocity",
                                            "value": "$internalField",
                                        }
                                    ),
                                    "model": CustomOrderedDict({"type": "noSlip"}),
                                    "symmetry": CustomOrderedDict({"type": "symmetry"}),
                                    "side": CustomOrderedDict({"type": "slip"}),
                                }
                            ),
                        }
                    )
                }
            ),
            "system": CustomOrderedDict(
                {
                    "controlDict": CustomOrderedDict(
                        {
                            "application": "<application>",
                            "startFrom": "startTime",
                            "startTime": 0,
                            "stopAt": "endTime",
                            "endTime": 10,
                            "deltaT": 0.005,
                            "writeControl": "timeStep",
                            "writeInterval": 100,
                            "purgeWrite": 1,
                            "writeFormat": "binary",
                            "writePrecision": 6,
                            "writeCompression": "off",
                            "timeFormat": "general",
                            "timePrecision": 6,
                            "adjustTimeStep": "no",
                            "runTimeModifiable": "true",
                            "functions": {},
                        }
                    )
                }
            ),
            "constant": CustomOrderedDict(
                {
                    "transportProperties": CustomOrderedDict(
                        {
                            "transportModel": "Newtonian",
                            "nu": "nu [0 2 -1 0 0 0 0] 1e-06",
                            "alpha": "alpha [0 2 -1 0 0 0 0] 0",
                            "Pr": "Pr [0 0 0 0 0 0 0] 0.7",
                        }
                    )
                }
            ),
        }
    )
    assert expected == actual


def test_insert_nested_item_simple(simple_odict):
    simple_odict.insert([], "test", "example")
    actual = simple_odict
    expected = CustomOrderedDict(
        {
            "a": 1,
            "b": CustomOrderedDict({"ba": 21, "bb": 22}),
            "c": 3,
            "test": "example",
        }
    )
    assert len(simple_odict) == 4
    assert simple_odict.get("test", None) == "example"
    assert expected == actual


def test_insert_nested_item_complex(complex_odict):
    complex_odict.insert(["0", "U", "boundaryField", "airinlet"], "test", "example")
    actual_nested_dict = complex_odict.get_nested_value(
        ["0", "U", "boundaryField", "airinlet"]
    )
    expected_nested_dict = CustomOrderedDict(
        {
            "type": "surfaceNormalFixedValue",
            "refValue": "uniform -15.32",
            "test": "example",
        }
    )
    assert len(actual_nested_dict) == 3
    assert actual_nested_dict.get("test", None) == "example"
    assert expected_nested_dict == actual_nested_dict


def test_insert_nested_dict_simple(simple_odict):
    simple_odict.insert([], "test", CustomOrderedDict())
    actual = simple_odict
    expected = CustomOrderedDict(
        {
            "a": 1,
            "b": CustomOrderedDict({"ba": 21, "bb": 22}),
            "c": 3,
            "test": CustomOrderedDict(),
        }
    )
    assert expected == actual


def test_insert_nested_dict_complex(complex_odict):
    complex_odict.insert(
        ["0", "U", "boundaryField", "airinlet"], "test", CustomOrderedDict()
    )
    actual_nested_dict = complex_odict.get_nested_value(
        ["0", "U", "boundaryField", "airinlet"]
    )
    expected_nested_dict = CustomOrderedDict(
        {
            "type": "surfaceNormalFixedValue",
            "refValue": "uniform -15.32",
            "test": CustomOrderedDict(),
        }
    )
    assert len(actual_nested_dict) == 3
    assert actual_nested_dict.get("test", None) == CustomOrderedDict()
    assert expected_nested_dict == actual_nested_dict


def test_remove_simple(simple_odict):
    simple_odict.remove(["b"], "ba")
    simple_odict.remove([], "c")
    actual = simple_odict
    expected = CustomOrderedDict({"a": 1, "b": CustomOrderedDict({"bb": 22})})
    assert expected == actual


def test_remove_complex(complex_odict):
    # remove key-value pair
    complex_odict.remove(["0", "U"], "dimensions")
    assert "dimensions" not in complex_odict.get_nested_value(["0", "U"]).keys()

    # remove key-odict pair
    complex_odict.remove(["0", "U"], "boundaryField")
    assert "boundaryField" not in complex_odict.get_nested_value(["0", "U"]).keys()


def test_remove_all_simple(simple_odict):
    simple_odict.remove_all(["b"])
    target_dict = simple_odict.get_nested_value("b")
    assert isinstance(target_dict, CustomOrderedDict)
    assert len(target_dict) == 0


def test_remove_all_simple_invalid_key(simple_odict):
    with pytest.raises(KeyError):
        simple_odict.remove_all(["d"])


def test_remove_all_simple_not_dict(simple_odict):
    with pytest.raises(ValueError):
        simple_odict.remove_all(["a"])


def test_map_keys_to_target_all_keys_present():
    example_dict = CustomOrderedDict({"a": 0, "b": 0, "c": 0})
    target_dict = CustomOrderedDict({"a": 1, "b": 2, "c": 3})

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict({"a": 1, "b": 2, "c": 3})

    assert result == expected


def test_map_keys_to_target_some_keys_present():
    example_dict = CustomOrderedDict({"a": 0, "b": 0, "c": 0})
    target_dict = CustomOrderedDict({"a": 1, "c": 3, "d": 4})

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict({"a": 1, "b": 0, "c": 3})

    assert result == expected


def test_map_keys_to_target_no_keys_present():
    example_dict = CustomOrderedDict({"a": 0, "b": 0, "c": 0})
    target_dict = CustomOrderedDict({"d": 4, "e": 5})

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict({"a": 0, "b": 0, "c": 0})

    assert result == expected


def test_map_keys_to_target_empty_example_dict():
    example_dict = CustomOrderedDict()
    target_dict = CustomOrderedDict({"a": 1, "b": 2, "c": 3})

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict()

    assert result == expected


def test_map_keys_to_target_both_empty():
    example_dict = CustomOrderedDict()
    target_dict = CustomOrderedDict()

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict()

    assert result == expected


def test_map_keys_to_target_example_with_extra_keys():
    example_dict = CustomOrderedDict({"a": 0, "b": 0, "c": 0, "d": 0})
    target_dict = CustomOrderedDict({"a": 1, "b": 2})

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict({"a": 1, "b": 2, "c": 0, "d": 0})

    assert result == expected


def test_map_keys_to_target_target_with_extra_keys():
    example_dict = CustomOrderedDict({"a": 0, "b": 0})
    target_dict = CustomOrderedDict({"a": 1, "b": 2, "c": 3, "d": 4})

    result = example_dict.map_keys_to_target_dict(target_dict)
    expected = CustomOrderedDict({"a": 1, "b": 2})

    assert result == expected
