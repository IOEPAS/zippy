"""Generator json from logs."""


def write_json_output(input_stream, output_stream):
    """Wrap json output for log."""
    output_stream.write(b"[")

    while True:
        line = input_stream.readline()
        next_line = input_stream.readline()

        output_stream.write(line.replace(b"}{", b"},{"))

        if next_line:
            output_stream.write(b",")
            output_stream.write(next_line.replace(b"}{", b"},{"))
        else:
            break

    output_stream.write(b"]")
