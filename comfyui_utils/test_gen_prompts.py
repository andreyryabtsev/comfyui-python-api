import re
import pytest

import gen_prompts

def test_runs_at_all():
    assert gen_prompts.parse_args("wow",  gen_prompts.make_config("TestConfig", []))

def test_single():
    config = gen_prompts.make_config("TestConfig", [
        gen_prompts.IntArg("arg", 2, min_value=0, max_value=4)
    ])

    # missing
    parsed = gen_prompts.parse_args("wow", config)
    assert not parsed.warnings
    assert parsed.cleaned == "wow"
    assert parsed.result.arg == 2

    # present
    parsed = gen_prompts.parse_args("wow $arg=3", config)
    assert len(parsed.warnings) == 0
    assert parsed.cleaned == "wow "
    assert parsed.result.arg == 3

    # int too large
    parsed = gen_prompts.parse_args("wow $arg=5", config)
    assert parsed.warnings == ["arg 5 too high, defaulting to 4"]
    assert parsed.cleaned == "wow "
    assert parsed.result.arg == 4

    # str doesn't parse
    config = gen_prompts.make_config("TestConfig", [
        gen_prompts.IntArg("veg", 2, min_value=0, max_value=4)
    ])
    with pytest.raises(Exception, match="Invalid argument veg: must be integer"):
        parsed = gen_prompts.parse_args("wow $veg=tomato", config)

    # wrong argument
    with pytest.raises(Exception, match=re.escape("Unrecognized arguments: ['wew=tomato']")):
        parsed = gen_prompts.parse_args("wow $wew=tomato", config)
