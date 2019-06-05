import os
import sys

if __name__ == "__main__":
    # set python path
    sys.path.insert(0, os.getcwd())

    # setup django : django app 이 아닌 곳에서는 삭제할 것
    DEPLOYMENT_LEVEL = os.environ.setdefault("DEPLOYMENT_LEVEL", "development")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings_{dlevel}".format(dlevel=DEPLOYMENT_LEVEL))
    import django

    django.setup()

from base.utils import console_log, ArgumentParser, ReaderContext, WriterContext, LineStripReader


def main(**kwargs):
    parser = ArgumentParser(**kwargs)
    parser.add_argument("--input_file_path", type=str, default=None)
    parser.add_argument("--output_file_path", type=str, default=None)
    args = parser.parse_args()

    console_log("{} start".format(__file__))
    with ReaderContext(path=args.input_file_path) as input_f, WriterContext(path=args.output_file_path) as output_f:
        for line in LineStripReader(input_f):
            output_f.write(line)
            output_f.write("\n")
    console_log("{} end".format(__file__))


if __name__ == "__main__":
    main()
