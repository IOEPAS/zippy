"""Generator json from logs."""


def wrap_json_output(input_file):
    """Wrap json outut for log."""
    json_starting = '{"logs":['
    json_ending = "]}"

    yield json_starting
    yield ",".join(input_file.readlines()).replace("}{", "},{")
    yield json_ending
