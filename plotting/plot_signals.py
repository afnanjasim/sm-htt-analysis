#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Dumbledraw.dumbledraw as dd
import Dumbledraw.rootfile_parser as rootfile_parser
import Dumbledraw.styles as styles

import argparse
import copy
import yaml

import logging
logger = logging.getLogger("")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        "Plot signals using Dumbledraw from shapes produced by shape-producer module."
    )
    parser.add_argument(
        "-c",
        "--channels",
        nargs="+",
        type=str,
        required=True,
        help="Channels")
    parser.add_argument("-e", "--era", type=str, required=True, help="Era")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="ROOT file with shapes of processes")
    parser.add_argument(
        "--png", action="store_true", help="Save plots in png format")
    parser.add_argument(
        "--stxs-categories",
        type=int,
        required=True,
        help="Select STXS categorization.")
    parser.add_argument(
        "--stxs-signals", type=int, required=True, help="Select STXS signals.")
    parser.add_argument(
        "--normalize-by-bin-width",
        action="store_true",
        help="Normelize plots by bin width")

    return parser.parse_args()


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def main(args):
    channel_categories = {
        #"et": ["ztt", "zll", "w", "tt", "ss", "misc"],
        "et": ["12", "15", "11", "13", "14", "16"],
        #"mt": ["ztt", "zll", "w", "tt", "ss", "misc"],
        "mt": ["12", "15", "11", "13", "14", "16"],
        #"tt": ["ztt", "noniso", "misc"]
        "tt": ["12", "17", "16"]
    }

    if args.stxs_categories == 0:
        for channel in ["et", "mt", "tt"]:
            channel_categories[channel] += ["1", "2"]
    elif args.stxs_categories == 1:
        for channel in ["et", "mt", "tt"]:
            channel_categories[channel] += [
                "3", "4", "5", "6",
                "7", "8"
            ]
    else:
        logger.critical("Selected unkown STXS categorization {}",
                        args.stxs_categories)
        raise Exception

    if args.stxs_signals == 0:
        signals = ["ggH", "qqH"]
        signal_linestlyes = [1, 1]
    elif args.stxs_signals == 1:
        signals = [
            "qqH_VBFTOPO_JET3VETO", "qqH_VBFTOPO_JET3",
            "qqH_REST", "qqH_PTJET1_GT200", "qqH_VH2JET", "ggH_0J",
            "ggH_1J_PTH_0_60", "ggH_1J_PTH_60_120", "ggH_1J_PTH_120_200",
            "ggH_1J_PTH_GT200", "ggH_GE2J_PTH_0_60", "ggH_GE2J_PTH_60_120",
            "ggH_GE2J_PTH_120_200", "ggH_GE2J_PTH_GT200", "ggH_VBFTOPO_JET3VETO",
            "ggH_VBFTOPO_JET3"
        ]
        signal_linestlyes = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    else:
        logger.critical("Selected unkown STXS signals {}", args.stxs_signals)
        raise Exception
    signal_names = [signal.replace("125", "") for signal in signals]

    channel_dict = {
        "ee": "ee",
        "em": "e#mu",
        "et": "e#tau_{h}",
        "mm": "#mu#mu",
        "mt": "#mu#tau_{h}",
        "tt": "#tau_{h}#tau_{h}"
    }

    category_dict = {
        "1": "ggH",
        "3": "ggH, 0 jet",
        "4": "ggH, 1 jet",
        "5": "ggH, >= 2 jets",
        "2": "VBF",
        "6": "VBF, < 2 jets",
        "7": "VBF, 2 jets",
        "8": "VBF, > 2 jets",
        "12": "Z#rightarrow#tau#tau",
        "15": "Z#rightarrowll",
        "11": "W+jets",
        "13": "t#bar{t}",
        "14": "same sign",
        "16": "misc",
        "17": "noniso"
    }

    rootfile = rootfile_parser.Rootfile_parser(args.input)

    plots = []
    for channel in args.channels:
        for category in channel_categories[channel]:
            # Create plot
            plot = dd.Plot([], "ModTDR", r=0.04, l=0.14)

            # Plot signals
            for i, (signal, name) in enumerate(zip(signals, signal_names)):
                plot.subplot(0).add_hist(
                    rootfile.get(channel, category, signal), name)
                plot.subplot(0).setGraphStyle(
                    name,
                    "hist",
                    linecolor=styles.color_dict[name.split("_")[0]],
                    linewidth=5)
                plot.subplot(0).get_hist(name).SetLineStyle(
                    signal_linestlyes[i])

            # Normalize by bin-width
            if args.normalize_by_bin_width:
                plot.subplot(0).normalizeByBinWidth()

            # Define axes
            plot.subplot(0).setXlabel("NN score")
            if args.normalize_by_bin_width:
                plot.subplot(0).setYlabel("N_{events}/bin width")
            else:
                plot.subplot(0).setYlabel("N_{events}")

            # Draw signals
            plot.subplot(0).setLogY()
            plot.subplot(0).setYlims(1e-3, 1e5)
            plot.subplot(0).Draw(signal_names)

            # Draw additional labels
            plot.DrawCMS()
            if "2016" in args.era:
                plot.DrawLumi("35.9 fb^{-1} (13 TeV)")
            elif "2017" in args.era:
                plot.DrawLumi("41.3 fb^{-1} (13 TeV)")
            else:
                logger.critical("Era {} is not implemented.".format(args.era))
                raise Exception
            plot.DrawChannelCategoryLabel(
                "%s, %s" % (channel_dict[channel], category_dict[category]))

            # Create legends
            plot.add_legend(width=0.40, height=0.30)
            plot.legend(0).setNColumns(1)
            for i, name in enumerate(signal_names):
                plot.legend(0).add_entry(0, name, name, 'l')
            plot.legend(0).Draw()

            # Save plot
            postfix = "stxsSignals{}".format(args.stxs_signals)
            plot.save("plots/%s_%s_%s_%s.%s" % (args.era, channel, category,
                                                postfix, "png"
                                                if args.png else "pdf"))

            plots.append(
                plot
            )  # work around to have clean up seg faults only at the end of the script


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("{}_plot_signals.log".format(args.era), logging.INFO)
    main(args)
