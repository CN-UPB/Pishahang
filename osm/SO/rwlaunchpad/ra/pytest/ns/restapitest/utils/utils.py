
from .imports import * # noqa


def parse_cli():
    """Parse command line options
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--confd-host", help="confd IP",
                        dest='confd_host',
                        default='127.0.0.1')
    args = parser.parse_args()

    return args


def parse_input_data(file_name):
    """
    open the input file and make into a python Dict Obj
    """

    data = ''

    with open(file_name, 'r') as ipf:
        data = json.load(ipf)

    return data
