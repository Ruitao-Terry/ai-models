# (C) Copyright 2023 European Centre for Medium-Range Weather Forecasts.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import argparse
import logging
import os
import shlex
import sys

from .model import available_inputs, available_models, available_outputs, load_model

LOG = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()

    # See https://github.com/pytorch/pytorch/issues/77764
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    parser.add_argument(
        "--models",
        action="store_true",
        help="List models and exit",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Turn on debug",
    )

    parser.add_argument(
        "--input",
        default="mars",
        help="Source to use",
        choices=available_inputs(),
    )

    parser.add_argument(
        "--file",
        help="Source to use if source=file",
    )

    parser.add_argument(
        "--output",
        default="file",
        help="Where to output the results",
        choices=available_outputs(),
    )

    parser.add_argument(
        "--date",
        default="-1",
        help="For which analysis date to start the inference (default: yesterday)",
    )

    parser.add_argument(
        "--time",
        type=int,
        default=12,
        help="For which analysis time to start the inference (default: 12)",
    )

    parser.add_argument(
        "--assets",
        default=os.environ.get("AI_MODELS_ASSETS", "."),
        help="Path to directory containing the weights and other assets",
    )

    parser.add_argument(
        "--assets-sub-directory",
        help="Load assets from a subdirectory of --assets based on the name of the model.",
        action="store_true",
    )

    parser.add_argument(
        "--download-assets",
        help="Download assets if they do not exists.",
        action="store_true",
    )

    parser.add_argument(
        "--path",
        help="Path where to write the output of the model",
    )

    parser.add_argument(
        "--fields",
        help="Show the fields needed as input for the model",
        action="store_true",
    )

    parser.add_argument(
        "--expver",
        help="Set the experiment version of the model output",
    )

    parser.add_argument(
        "--num-threads",
        type=int,
        default=1,
        help="Number of threads. Only relevant for some models.",
    )

    parser.add_argument(
        "--lead-time",
        type=int,
        default=240,
        help="Length of forecast in hours.",
    )

    parser.add_argument(
        "--model-version",
        default="latest",
        help="Model version",
    )

    if "--models" not in sys.argv:
        parser.add_argument(
            "model",
            metavar="MODEL",
            choices=available_models(),
            help="The model to run",
        )

    args = parser.parse_args()

    if args.models:
        for p in sorted(available_models()):
            print(p)
        sys.exit(0)

    if args.assets_sub_directory:
        args.assets = os.path.join(args.assets, args.model)

    if args.path is None:
        args.path = f"{args.model}.grib"

    if args.file is not None:
        args.input = "file"

    if not args.fields:
        logging.basicConfig(
            level="DEBUG" if args.debug else "INFO",
            format="%(asctime)s %(levelname)s %(message)s",
        )

    model = load_model(args.model, **vars(args))

    if args.fields:
        model.print_fields()
        sys.exit(0)

    try:
        model.run()
    except FileNotFoundError as e:
        LOG.exception(e)
        LOG.error(
            "It is possible that some files requited by %s are missing.",
            args.model,
        )
        LOG.error("Rerun the command as:")
        LOG.error(
            "   %s",
            shlex.join([sys.argv[0], "--download-assets"] + sys.argv[1:]),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
