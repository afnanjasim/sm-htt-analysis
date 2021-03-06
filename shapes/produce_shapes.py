#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser
ROOT.gErrorIgnoreLevel = ROOT.kError

from shape_producer.cutstring import Cut, Cuts, Weight
from shape_producer.systematics import Systematics, Systematic
from shape_producer.categories import Category
from shape_producer.binning import ConstantBinning, VariableBinning
from shape_producer.variable import Variable
from shape_producer.systematic_variations import Nominal, DifferentPipeline, SquareAndRemoveWeight, create_systematic_variations, AddWeight, ReplaceWeight, Relabel
from shape_producer.process import Process
from shape_producer.estimation_methods import AddHistogramEstimationMethod
from shape_producer.channel import ETSM, MTSM, TTSM

from itertools import product

import argparse
import yaml

import logging
logger = logging.getLogger()


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Produce shapes for 2016 Standard Model analysis.")

    parser.add_argument(
        "--directory",
        required=True,
        type=str,
        help="Directory with Artus outputs.")
    parser.add_argument(
        "--et-friend-directory",
        default=None,
        type=str,
        help=
        "Directory arranged as Artus output and containing a friend tree for et."
    )
    parser.add_argument(
        "--mt-friend-directory",
        default=None,
        type=str,
        help=
        "Directory arranged as Artus output and containing a friend tree for mt."
    )
    parser.add_argument(
        "--tt-friend-directory",
        default=None,
        type=str,
        help=
        "Directory arranged as Artus output and containing a friend tree for tt."
    )
    parser.add_argument(
        "--fake-factor-friend-directory",
        default=None,
        type=str,
        help=
        "Directory arranged as Artus output and containing friend trees to data files with fake factors."
    )
    parser.add_argument(
        "--datasets", required=True, type=str, help="Kappa datsets database.")
    parser.add_argument(
        "--binning", required=True, type=str, help="Binning configuration.")
    parser.add_argument(
        "--channels",
        default=[],
        nargs='+',
        type=str,
        help="Channels to be considered.")
    parser.add_argument("--era", type=str, help="Experiment era.")
    parser.add_argument(
        "--gof-channel",
        default=None,
        type=str,
        help="Channel for goodness of fit shapes.")
    parser.add_argument(
        "--QCD-extrap-fit",
        default=False,
        action='store_true',
        help="Create shapes for QCD extrapolation factor determination.")
    parser.add_argument(
        "--gof-variable",
        type=str,
        help="Variable for goodness of fit shapes.")
    parser.add_argument(
        "--HIG16043",
        action="store_true",
        default=False,
        help="Create shapes of HIG16043 reference analysis.")
    parser.add_argument(
        "--num-threads",
        default=32,
        type=int,
        help="Number of threads to be used.")
    parser.add_argument(
        "--backend",
        default="classic",
        choices=["classic", "tdf"],
        type=str,
        help="Backend. Use classic or tdf.")
    parser.add_argument(
        "--tag", default="ERA_CHANNEL", type=str, help="Tag of output files.")
    parser.add_argument(
        "--skip-systematic-variations",
        default=False,
        type=str,
        help="Do not produce the systematic variations.")
    return parser.parse_args()


def main(args):
    # Container for all distributions to be drawn
    logger.info("Set up shape variations.")
    systematics = Systematics(
        "{}_shapes.root".format(args.tag),
        num_threads=args.num_threads,
        skip_systematic_variations=args.skip_systematic_variations)

    # Era selection
    if "2016" in args.era:
        from shape_producer.estimation_methods_2016 import DataEstimation, HTTEstimation, ggHEstimation, ggHEstimation_0J, ggHEstimation_1J_PTH_0_60, ggHEstimation_1J_PTH_60_120, ggHEstimation_1J_PTH_120_200, ggHEstimation_1J_PTH_GT200, ggHEstimation_GE2J_PTH_0_60, ggHEstimation_GE2J_PTH_60_120, ggHEstimation_GE2J_PTH_120_200, ggHEstimation_GE2J_PTH_GT200, ggHEstimation_VBFTOPO_JET3, ggHEstimation_VBFTOPO_JET3VETO, qqHEstimation, qqHEstimation_VBFTOPO_JET3VETO, qqHEstimation_VBFTOPO_JET3, qqHEstimation_REST, qqHEstimation_VH2JET, qqHEstimation_PTJET1_GT200, VHEstimation, ZTTEstimation, ZTTEstimationTT, ZLEstimationMTSM, ZLEstimationETSM, ZLEstimationTT, ZJEstimationMT, ZJEstimationET, ZJEstimationTT, WEstimation, TTTEstimationMT, TTTEstimationET, TTTEstimationTT, TTJEstimationMT, TTJEstimationET, TTJEstimationTT, VVTEstimationLT, VVJEstimationLT, VVTEstimationTT, VVJEstimationTT, EWKZEstimation, QCDEstimationMT, QCDEstimationET, QCDEstimationTT, ZTTEmbeddedEstimation, TTLEstimationMT, TTLEstimationET, TTLEstimationTT, TTTTEstimationMT, TTTTEstimationET, FakeEstimationLT, FakeEstimationTT
        from shape_producer.era import Run2016
        era = Run2016(args.datasets)
    else:
        logger.critical("Era {} is not implemented.".format(args.era))
        raise Exception

    # Channels and processes
    # yapf: disable
    directory = args.directory
    et_friend_directory = args.et_friend_directory
    mt_friend_directory = args.mt_friend_directory
    tt_friend_directory = args.tt_friend_directory
    ff_friend_directory = args.fake_factor_friend_directory
    mt = MTSM()
    if args.QCD_extrap_fit:
        mt.cuts.remove("muon_iso")
        mt.cuts.add(Cut("(iso_1<0.5)*(iso_1>=0.15)", "muon_iso_loose"))
    mt_processes = {
        "data"  : Process("data_obs", DataEstimation  (era, directory, mt, friend_directory=mt_friend_directory)),
        "HTT"   : Process("HTT",      HTTEstimation   (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH"   : Process("ggH125",   ggHEstimation   (era, directory, mt, friend_directory=mt_friend_directory)),
        "qqH"   : Process("qqH125",   qqHEstimation   (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_0J"               : Process("ggH_0J125",               ggHEstimation_0J              (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_1J_PTH_0_60"      : Process("ggH_1J_PTH_0_60125",      ggHEstimation_1J_PTH_0_60     (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_1J_PTH_60_120"    : Process("ggH_1J_PTH_60_120125",    ggHEstimation_1J_PTH_60_120   (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_1J_PTH_120_200"   : Process("ggH_1J_PTH_120_200125",   ggHEstimation_1J_PTH_120_200  (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_1J_PTH_GT200"     : Process("ggH_1J_PTH_GT200125",     ggHEstimation_1J_PTH_GT200    (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_GE2J_PTH_0_60"    : Process("ggH_GE2J_PTH_0_60125",    ggHEstimation_GE2J_PTH_0_60   (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_GE2J_PTH_60_120"  : Process("ggH_GE2J_PTH_60_120125",  ggHEstimation_GE2J_PTH_60_120 (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_GE2J_PTH_120_200" : Process("ggH_GE2J_PTH_120_200125", ggHEstimation_GE2J_PTH_120_200(era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_GE2J_PTH_GT200"   : Process("ggH_GE2J_PTH_GT200125",   ggHEstimation_GE2J_PTH_GT200  (era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_VBFTOPO_JET3VETO" : Process("ggH_VBFTOPO_JET3VETO125", ggHEstimation_VBFTOPO_JET3VETO(era, directory, mt, friend_directory=mt_friend_directory)),
        "ggH_VBFTOPO_JET3"     : Process("ggH_VBFTOPO_JET3125",     ggHEstimation_VBFTOPO_JET3    (era, directory, mt, friend_directory=mt_friend_directory)),
        "qqH_VBFTOPO_JET3VETO" : Process("qqH_VBFTOPO_JET3VETO125", qqHEstimation_VBFTOPO_JET3VETO(era, directory, mt, friend_directory=mt_friend_directory)),
        "qqH_VBFTOPO_JET3"     : Process("qqH_VBFTOPO_JET3125",     qqHEstimation_VBFTOPO_JET3    (era, directory, mt, friend_directory=mt_friend_directory)),
        "qqH_REST"             : Process("qqH_REST125",             qqHEstimation_REST            (era, directory, mt, friend_directory=mt_friend_directory)),
        "qqH_VH2JET"           : Process("qqH_VH2JET125",           qqHEstimation_VH2JET          (era, directory, mt, friend_directory=mt_friend_directory)),
        "qqH_PTJET1_GT200"     : Process("qqH_PTJET1_GT200125",     qqHEstimation_PTJET1_GT200    (era, directory, mt, friend_directory=mt_friend_directory)),
        "VH"    : Process("VH125",    VHEstimation    (era, directory, mt, friend_directory=mt_friend_directory)),
        "ZTT"   : Process("ZTT",      ZTTEstimation   (era, directory, mt, friend_directory=mt_friend_directory)),
        "ZL"    : Process("ZL",       ZLEstimationMTSM(era, directory, mt, friend_directory=mt_friend_directory)),
        "ZJ"    : Process("ZJ",       ZJEstimationMT  (era, directory, mt, friend_directory=mt_friend_directory)),
        "W"     : Process("W",        WEstimation     (era, directory, mt, friend_directory=mt_friend_directory)),
        "TTT"   : Process("TTT",      TTTEstimationMT (era, directory, mt, friend_directory=mt_friend_directory)),
        "TTJ"   : Process("TTJ",      TTJEstimationMT (era, directory, mt, friend_directory=mt_friend_directory)),
        "VVT"   : Process("VVT",      VVTEstimationLT (era, directory, mt, friend_directory=mt_friend_directory)),
        "VVJ"   : Process("VVJ",      VVJEstimationLT (era, directory, mt, friend_directory=mt_friend_directory)),
        "EWKZ"  : Process("EWKZ",     EWKZEstimation  (era, directory, mt, friend_directory=mt_friend_directory)),
        "FAKES" : Process("jetFakes",    FakeEstimationLT(era, directory, mt, friend_directory=[mt_friend_directory, ff_friend_directory])),
        "EMB"   : Process("EMB", ZTTEmbeddedEstimation(era, directory, mt, friend_directory=mt_friend_directory)),
        "TTL"   : Process("TTL", TTLEstimationMT (era, directory, mt, friend_directory=mt_friend_directory))
        }

    mt_processes["QCD"] = Process("QCD", QCDEstimationMT(era, directory, mt, [mt_processes[process] for process in ["ZTT", "ZJ", "ZL", "W", "TTT", "TTJ", "VVT", "VVJ", "EWKZ"]], mt_processes["data"], extrapolation_factor=1.17))
    et = ETSM()
    if args.QCD_extrap_fit:
        et.cuts.remove("ele_iso")
        et.cuts.add(Cut("(iso_1<0.5)*(iso_1>=0.1)", "ele_iso_loose"))
    et_processes = {
        "data"  : Process("data_obs", DataEstimation  (era, directory, et, friend_directory=et_friend_directory)),
        "HTT"   : Process("HTT",      HTTEstimation   (era, directory, et, friend_directory=et_friend_directory)),
        "ggH"   : Process("ggH125",   ggHEstimation   (era, directory, et, friend_directory=et_friend_directory)),
        "qqH"   : Process("qqH125",   qqHEstimation   (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_0J"               : Process("ggH_0J125",               ggHEstimation_0J              (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_1J_PTH_0_60"      : Process("ggH_1J_PTH_0_60125",      ggHEstimation_1J_PTH_0_60     (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_1J_PTH_60_120"    : Process("ggH_1J_PTH_60_120125",    ggHEstimation_1J_PTH_60_120   (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_1J_PTH_120_200"   : Process("ggH_1J_PTH_120_200125",   ggHEstimation_1J_PTH_120_200  (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_1J_PTH_GT200"     : Process("ggH_1J_PTH_GT200125",     ggHEstimation_1J_PTH_GT200    (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_GE2J_PTH_0_60"    : Process("ggH_GE2J_PTH_0_60125",    ggHEstimation_GE2J_PTH_0_60   (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_GE2J_PTH_60_120"  : Process("ggH_GE2J_PTH_60_120125",  ggHEstimation_GE2J_PTH_60_120 (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_GE2J_PTH_120_200" : Process("ggH_GE2J_PTH_120_200125", ggHEstimation_GE2J_PTH_120_200(era, directory, et, friend_directory=et_friend_directory)),
        "ggH_GE2J_PTH_GT200"   : Process("ggH_GE2J_PTH_GT200125",   ggHEstimation_GE2J_PTH_GT200  (era, directory, et, friend_directory=et_friend_directory)),
        "ggH_VBFTOPO_JET3VETO" : Process("ggH_VBFTOPO_JET3VETO125", ggHEstimation_VBFTOPO_JET3VETO(era, directory, et, friend_directory=et_friend_directory)),
        "ggH_VBFTOPO_JET3"     : Process("ggH_VBFTOPO_JET3125",     ggHEstimation_VBFTOPO_JET3    (era, directory, et, friend_directory=et_friend_directory)),
        "qqH_VBFTOPO_JET3VETO" : Process("qqH_VBFTOPO_JET3VETO125", qqHEstimation_VBFTOPO_JET3VETO(era, directory, et, friend_directory=et_friend_directory)),
        "qqH_VBFTOPO_JET3"     : Process("qqH_VBFTOPO_JET3125",     qqHEstimation_VBFTOPO_JET3    (era, directory, et, friend_directory=et_friend_directory)),
        "qqH_REST"             : Process("qqH_REST125",             qqHEstimation_REST            (era, directory, et, friend_directory=et_friend_directory)),
        "qqH_VH2JET"           : Process("qqH_VH2JET125",           qqHEstimation_VH2JET          (era, directory, et, friend_directory=et_friend_directory)),
        "qqH_PTJET1_GT200"     : Process("qqH_PTJET1_GT200125",     qqHEstimation_PTJET1_GT200    (era, directory, et, friend_directory=et_friend_directory)),
        "VH"    : Process("VH125",    VHEstimation    (era, directory, et, friend_directory=et_friend_directory)),
        "ZTT"   : Process("ZTT",      ZTTEstimation   (era, directory, et, friend_directory=et_friend_directory)),
        "ZL"    : Process("ZL",       ZLEstimationETSM(era, directory, et, friend_directory=et_friend_directory)),
        "ZJ"    : Process("ZJ",       ZJEstimationET  (era, directory, et, friend_directory=et_friend_directory)),
        "W"     : Process("W",        WEstimation     (era, directory, et, friend_directory=et_friend_directory)),
        "TTT"   : Process("TTT",      TTTEstimationET (era, directory, et, friend_directory=et_friend_directory)),
        "TTJ"   : Process("TTJ",      TTJEstimationET (era, directory, et, friend_directory=et_friend_directory)),
        "VVT"   : Process("VVT",      VVTEstimationLT (era, directory, et, friend_directory=et_friend_directory)),
        "VVJ"   : Process("VVJ",      VVJEstimationLT (era, directory, et, friend_directory=et_friend_directory)),
        "EWKZ"  : Process("EWKZ",     EWKZEstimation  (era, directory, et, friend_directory=et_friend_directory)),
        "FAKES" : Process("jetFakes",    FakeEstimationLT(era, directory, et, friend_directory=[et_friend_directory, ff_friend_directory])),
        "EMB"   : Process("EMB", ZTTEmbeddedEstimation(era, directory, et, friend_directory=et_friend_directory)),
        "TTL"   : Process("TTL", TTLEstimationET (era, directory, et, friend_directory=et_friend_directory))
        }

    et_processes["QCD"] = Process("QCD", QCDEstimationET(era, directory, et, [et_processes[process] for process in ["ZTT", "ZJ", "ZL", "W", "TTT", "TTJ", "VVT", "VVJ", "EWKZ"]], et_processes["data"], extrapolation_factor=1.16))
    tt = TTSM()
    if args.QCD_extrap_fit:
        tt.cuts.get("os").invert()
    if args.HIG16043:
        tt.cuts.remove("pt_h")
    tt_processes = {
        "data"  : Process("data_obs", DataEstimation  (era, directory, tt, friend_directory=tt_friend_directory)),
        "HTT"   : Process("HTT",      HTTEstimation   (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH"   : Process("ggH125",   ggHEstimation   (era, directory, tt, friend_directory=tt_friend_directory)),
        "qqH"   : Process("qqH125",   qqHEstimation   (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_0J"               : Process("ggH_0J125",               ggHEstimation_0J              (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_1J_PTH_0_60"      : Process("ggH_1J_PTH_0_60125",      ggHEstimation_1J_PTH_0_60     (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_1J_PTH_60_120"    : Process("ggH_1J_PTH_60_120125",    ggHEstimation_1J_PTH_60_120   (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_1J_PTH_120_200"   : Process("ggH_1J_PTH_120_200125",   ggHEstimation_1J_PTH_120_200  (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_1J_PTH_GT200"     : Process("ggH_1J_PTH_GT200125",     ggHEstimation_1J_PTH_GT200    (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_GE2J_PTH_0_60"    : Process("ggH_GE2J_PTH_0_60125",    ggHEstimation_GE2J_PTH_0_60   (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_GE2J_PTH_60_120"  : Process("ggH_GE2J_PTH_60_120125",  ggHEstimation_GE2J_PTH_60_120 (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_GE2J_PTH_120_200" : Process("ggH_GE2J_PTH_120_200125", ggHEstimation_GE2J_PTH_120_200(era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_GE2J_PTH_GT200"   : Process("ggH_GE2J_PTH_GT200125",   ggHEstimation_GE2J_PTH_GT200  (era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_VBFTOPO_JET3VETO" : Process("ggH_VBFTOPO_JET3VETO125", ggHEstimation_VBFTOPO_JET3VETO(era, directory, tt, friend_directory=tt_friend_directory)),
        "ggH_VBFTOPO_JET3"     : Process("ggH_VBFTOPO_JET3125",     ggHEstimation_VBFTOPO_JET3    (era, directory, tt, friend_directory=tt_friend_directory)),
        "qqH_VBFTOPO_JET3VETO" : Process("qqH_VBFTOPO_JET3VETO125", qqHEstimation_VBFTOPO_JET3VETO(era, directory, tt, friend_directory=tt_friend_directory)),
        "qqH_VBFTOPO_JET3"     : Process("qqH_VBFTOPO_JET3125",     qqHEstimation_VBFTOPO_JET3    (era, directory, tt, friend_directory=tt_friend_directory)),
        "qqH_REST"             : Process("qqH_REST125",             qqHEstimation_REST            (era, directory, tt, friend_directory=tt_friend_directory)),
        "qqH_VH2JET"           : Process("qqH_VH2JET125",           qqHEstimation_VH2JET          (era, directory, tt, friend_directory=tt_friend_directory)),
        "qqH_PTJET1_GT200"     : Process("qqH_PTJET1_GT200125",     qqHEstimation_PTJET1_GT200    (era, directory, tt, friend_directory=tt_friend_directory)),
        "VH"    : Process("VH125",    VHEstimation    (era, directory, tt, friend_directory=tt_friend_directory)),
        "ZTT"   : Process("ZTT",      ZTTEstimationTT (era, directory, tt, friend_directory=tt_friend_directory)),
        "ZL"    : Process("ZL",       ZLEstimationTT  (era, directory, tt, friend_directory=tt_friend_directory)),
        "ZJ"    : Process("ZJ",       ZJEstimationTT  (era, directory, tt, friend_directory=tt_friend_directory)),
        "W"     : Process("W",        WEstimation     (era, directory, tt, friend_directory=tt_friend_directory)),
        "TTT"   : Process("TTT",      TTTEstimationTT (era, directory, tt, friend_directory=tt_friend_directory)),
        "TTJ"   : Process("TTJ",      TTJEstimationTT (era, directory, tt, friend_directory=tt_friend_directory)),
        "VVT"   : Process("VVT",      VVTEstimationTT (era, directory, tt, friend_directory=tt_friend_directory)),
        "VVJ"   : Process("VVJ",      VVJEstimationTT (era, directory, tt, friend_directory=tt_friend_directory)),
        "EWKZ"  : Process("EWKZ",     EWKZEstimation  (era, directory, tt, friend_directory=tt_friend_directory)),
        "FAKES" : Process("jetFakes",    FakeEstimationTT(era, directory, tt, friend_directory=[tt_friend_directory, ff_friend_directory])),
        "EMB"   : Process("EMB", ZTTEmbeddedEstimation(era, directory, tt, friend_directory=tt_friend_directory)),
        "TTL"   : Process("TTL", TTLEstimationTT (era, directory, tt, friend_directory=tt_friend_directory))
        }

    tt_processes["QCD"] = Process("QCD", QCDEstimationTT(era, directory, tt, [tt_processes[process] for process in ["ZTT", "ZJ", "ZL", "W", "TTT", "TTJ", "VVT", "VVJ", "EWKZ"]], tt_processes["data"]))

    # Variables and categories
    binning = yaml.load(open(args.binning))

    et_categories = []
    # HIG16043 shapes
    if "et" in args.channels and args.HIG16043:
        for category in ["0jet", "vbf", "boosted"]:
            variable = Variable(
                    binning["HIG16043"]["et"][category]["variable"],
                    VariableBinning(binning["HIG16043"]["et"][category]["binning"]),
                    expression=binning["HIG16043"]["et"][category]["expression"])
            et_categories.append(
                Category(
                    category,
                    et,
                    Cuts(
                        Cut(binning["HIG16043"]["et"][category]["cut_unrolling"],
                            "et_cut_unrolling_{}".format(category)),
                        Cut(binning["HIG16043"]["et"][category]["cut_category"],
                            "et_cut_category_{}".format(category))
                        ),
                    variable=variable))
    # Analysis shapes
    elif "et" in args.channels:
        classes_et = ["ggh", "qqh", "ztt", "zll", "w", "tt", "ss", "misc"]
        for i, label in enumerate(classes_et):
            score = Variable(
                "et_max_score",
                 VariableBinning(binning["analysis"]["et"][label]))
            et_categories.append(
                Category(
                    label,
                    et,
                    Cuts(
                        Cut("et_max_index=={index}".format(index=i), "exclusive_score")),
                    variable=score))
            if label in ["ggh", "qqh"]:
                expression = ""
                for i_e, e in enumerate(binning["stxs_stage1"][label]):
                    offset = (binning["analysis"]["et"][label][-1]-binning["analysis"]["et"][label][0])*i_e
                    expression += "{STXSBIN}*(et_max_score+{OFFSET})".format(STXSBIN=e, OFFSET=offset)
                    if not e is binning["stxs_stage1"][label][-1]:
                        expression += " + "
                score_unrolled = Variable(
                    "et_max_score_unrolled",
                     VariableBinning(binning["analysis"]["et"][label+"_unrolled"]),
                     expression=expression)
                et_categories.append(
                    Category(
                        "{}_unrolled".format(label),
                        et,
                        Cuts(Cut("et_max_index=={index}".format(index=i), "exclusive_score"),
                             Cut("et_max_score>{}".format(1.0/len(classes_et)), "protect_unrolling")),
                        variable=score_unrolled))
    # Goodness of fit shapes
    elif "et" == args.gof_channel:
        score = Variable(
                args.gof_variable,
                VariableBinning(binning["gof"]["et"][args.gof_variable]["bins"]),
                expression=binning["gof"]["et"][args.gof_variable]["expression"])
        if "cut" in binning["gof"]["et"][args.gof_variable].keys():
            cuts=Cuts(Cut(binning["gof"]["et"][args.gof_variable]["cut"], "binning"))
        else:
            cuts=Cuts()
        et_categories.append(
            Category(
                args.gof_variable,
                et,
                cuts,
                variable=score))

    mt_categories = []
    # HIG16043 shapes
    if "mt" in args.channels and args.HIG16043:
        for category in ["0jet", "vbf", "boosted"]:
            variable = Variable(
                    binning["HIG16043"]["mt"][category]["variable"],
                    VariableBinning(binning["HIG16043"]["mt"][category]["binning"]),
                    expression=binning["HIG16043"]["mt"][category]["expression"])
            mt_categories.append(
                Category(
                    category,
                    mt,
                    Cuts(
                        Cut(binning["HIG16043"]["mt"][category]["cut_unrolling"],
                            "mt_cut_unrolling_{}".format(category)),
                        Cut(binning["HIG16043"]["mt"][category]["cut_category"],
                            "mt_cut_category_{}".format(category))
                        ),
                    variable=variable))
    # Analysis shapes
    elif "mt" in args.channels:
        classes_mt = ["ggh", "qqh", "ztt", "zll", "w", "tt", "ss", "misc"]
        for i, label in enumerate(classes_mt):
            score = Variable(
                "mt_max_score",
                 VariableBinning(binning["analysis"]["mt"][label]))
            mt_categories.append(
                Category(
                    label,
                    mt,
                    Cuts(
                        Cut("mt_max_index=={index}".format(index=i), "exclusive_score")),
                    variable=score))
            if label in ["ggh", "qqh"]:
                expression = ""
                for i_e, e in enumerate(binning["stxs_stage1"][label]):
                    offset = (binning["analysis"]["mt"][label][-1]-binning["analysis"]["mt"][label][0])*i_e
                    expression += "{STXSBIN}*(mt_max_score+{OFFSET})".format(STXSBIN=e, OFFSET=offset)
                    if not e is binning["stxs_stage1"][label][-1]:
                        expression += " + "
                score_unrolled = Variable(
                    "mt_max_score_unrolled",
                     VariableBinning(binning["analysis"]["mt"][label+"_unrolled"]),
                     expression=expression)
                mt_categories.append(
                    Category(
                        "{}_unrolled".format(label),
                        mt,
                        Cuts(Cut("mt_max_index=={index}".format(index=i), "exclusive_score"),
                             Cut("mt_max_score>{}".format(1.0/len(classes_mt)), "protect_unrolling")),
                        variable=score_unrolled))
    # Goodness of fit shapes
    elif args.gof_channel == "mt":
        score = Variable(
                args.gof_variable,
                VariableBinning(binning["gof"]["mt"][args.gof_variable]["bins"]),
                expression=binning["gof"]["mt"][args.gof_variable]["expression"])
        if "cut" in binning["gof"]["mt"][args.gof_variable].keys():
            cuts=Cuts(Cut(binning["gof"]["mt"][args.gof_variable]["cut"], "binning"))
        else:
            cuts=Cuts()
        mt_categories.append(
            Category(
                args.gof_variable,
                mt,
                cuts,
                variable=score))

    tt_categories = []
    # HIG16043 shapes
    if "tt" in args.channels and args.HIG16043:
        for category in ["0jet", "vbf", "boosted"]:
            variable = Variable(
                    binning["HIG16043"]["tt"][category]["variable"],
                    VariableBinning(binning["HIG16043"]["tt"][category]["binning"]),
                    expression=binning["HIG16043"]["tt"][category]["expression"])
            tt_categories.append(
                Category(
                    category,
                    tt,
                    Cuts(
                        Cut(binning["HIG16043"]["tt"][category]["cut_unrolling"],
                            "tt_cut_unrolling_{}".format(category)),
                        Cut(binning["HIG16043"]["tt"][category]["cut_category"],
                            "tt_cut_category_{}".format(category))
                        ),
                    variable=variable))
    # Analysis shapes
    elif "tt" in args.channels:
        classes_tt = ["ggh", "qqh", "ztt", "noniso", "misc"]
        for i, label in enumerate(classes_tt):
            score = Variable(
                "tt_max_score",
                 VariableBinning(binning["analysis"]["tt"][label]))
            tt_categories.append(
                Category(
                    label,
                    tt,
                    Cuts(
                        Cut("tt_max_index=={index}".format(index=i), "exclusive_score")),
                    variable=score))
            if label in ["ggh", "qqh"]:
                expression = ""
                for i_e, e in enumerate(binning["stxs_stage1"][label]):
                    offset = (binning["analysis"]["tt"][label][-1]-binning["analysis"]["tt"][label][0])*i_e
                    expression += "{STXSBIN}*(tt_max_score+{OFFSET})".format(STXSBIN=e, OFFSET=offset)
                    if not e is binning["stxs_stage1"][label][-1]:
                        expression += " + "
                score_unrolled = Variable(
                    "tt_max_score_unrolled",
                     VariableBinning(binning["analysis"]["tt"][label+"_unrolled"]),
                     expression=expression)
                tt_categories.append(
                    Category(
                        "{}_unrolled".format(label),
                        tt,
                        Cuts(Cut("tt_max_index=={index}".format(index=i), "exclusive_score"),
                             Cut("tt_max_score>{}".format(1.0/len(classes_tt)), "protect_unrolling")),
                        variable=score_unrolled))
    # Goodness of fit shapes
    elif args.gof_channel == "tt":
        score = Variable(
                args.gof_variable,
                VariableBinning(binning["gof"]["tt"][args.gof_variable]["bins"]),
                expression=binning["gof"]["tt"][args.gof_variable]["expression"])
        if "cut" in binning["gof"]["tt"][args.gof_variable].keys():
            cuts=Cuts(Cut(binning["gof"]["tt"][args.gof_variable]["cut"], "binning"))
        else:
            cuts=Cuts()
        tt_categories.append(
            Category(
                args.gof_variable,
                tt,
                cuts,
                variable=score))

    # Nominal histograms
    # yapf: enable
    signal_nicks = [
        "HTT", "VH", "ggH", "qqH", "qqH_VBFTOPO_JET3VETO", "qqH_VBFTOPO_JET3",
        "qqH_REST", "qqH_PTJET1_GT200", "qqH_VH2JET", "ggH_0J",
        "ggH_1J_PTH_0_60", "ggH_1J_PTH_60_120", "ggH_1J_PTH_120_200",
        "ggH_1J_PTH_GT200", "ggH_GE2J_PTH_0_60", "ggH_GE2J_PTH_60_120",
        "ggH_GE2J_PTH_120_200", "ggH_GE2J_PTH_GT200", "ggH_VBFTOPO_JET3VETO",
        "ggH_VBFTOPO_JET3"
    ]

    if "et" in [args.gof_channel] + args.channels:
        for process, category in product(et_processes.values(), et_categories):
            systematics.add(
                Systematic(
                    category=category,
                    process=process,
                    analysis="smhtt",
                    era=era,
                    variation=Nominal(),
                    mass="125"))

    if "mt" in [args.gof_channel] + args.channels:
        for process, category in product(mt_processes.values(), mt_categories):
            systematics.add(
                Systematic(
                    category=category,
                    process=process,
                    analysis="smhtt",
                    era=era,
                    variation=Nominal(),
                    mass="125"))
    if "tt" in [args.gof_channel] + args.channels:
        for process, category in product(tt_processes.values(), tt_categories):
            systematics.add(
                Systematic(
                    category=category,
                    process=process,
                    analysis="smhtt",
                    era=era,
                    variation=Nominal(),
                    mass="125"))

    # Shapes variations

    # Tau energy scale
    tau_es_3prong_variations = create_systematic_variations(
        "CMS_scale_t_3prong_13TeV", "tauEsThreeProng", DifferentPipeline)
    tau_es_1prong_variations = create_systematic_variations(
        "CMS_scale_t_1prong_13TeV", "tauEsOneProng", DifferentPipeline)
    tau_es_1prong1pizero_variations = create_systematic_variations(
        "CMS_scale_t_1prong1pizero_13TeV", "tauEsOneProngPiZeros",
        DifferentPipeline)
    for variation in tau_es_3prong_variations + tau_es_1prong_variations + tau_es_1prong1pizero_variations:
        for process_nick in ["ZTT", "TTT", "TTL", "VVT", "EWKZ", "EMB"
                             ] + signal_nicks:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # Jet energy scale

    # Inclusive JES shapes
    jet_es_variations = []
    jet_es_variations += create_systematic_variations(
        "CMS_scale_j_13TeV", "jecUnc", DifferentPipeline)

    # Splitted JES shapes
    jet_es_variations += create_systematic_variations(
        "CMS_scale_j_eta0to3_13TeV", "jecUncEta0to3", DifferentPipeline)
    jet_es_variations += create_systematic_variations(
        "CMS_scale_j_eta0to5_13TeV", "jecUncEta0to5", DifferentPipeline)
    jet_es_variations += create_systematic_variations(
        "CMS_scale_j_eta3to5_13TeV", "jecUncEta3to5", DifferentPipeline)
    jet_es_variations += create_systematic_variations(
        "CMS_scale_j_RelativeBal_13TeV", "jecUncRelativeBal",
        DifferentPipeline)

    for variation in jet_es_variations:
        for process_nick in [
                "ZTT", "ZL", "ZJ", "W", "TTT", "TTL", "TTJ", "VVT", "VVJ",
                "EWKZ"
        ] + signal_nicks:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # MET energy scale
    met_unclustered_variations = create_systematic_variations(
        "CMS_scale_met_unclustered_13TeV", "metUnclusteredEn",
        DifferentPipeline)
    # NOTE: Clustered MET not used anymore in the uncertainty model
    #met_clustered_variations = create_systematic_variations(
    #    "CMS_scale_met_clustered_13TeV", "metJetEn", DifferentPipeline)
    for variation in met_unclustered_variations:  # + met_clustered_variations:
        for process_nick in [
                "ZTT", "ZL", "ZJ", "W", "TTT", "TTL", "TTJ", "VVT", "VVJ",
                "EWKZ"
        ] + signal_nicks:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # Z pt reweighting
    zpt_variations = create_systematic_variations(
        "CMS_htt_dyShape_13TeV", "zPtReweightWeight", SquareAndRemoveWeight)
    for variation in zpt_variations:
        for process_nick in ["ZTT", "ZL", "ZJ"]:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # top pt reweighting
    top_pt_variations = create_systematic_variations(
        "CMS_htt_ttbarShape_13TeV", "topPtReweightWeight",
        SquareAndRemoveWeight)
    for variation in top_pt_variations:
        for process_nick in ["TTT", "TTL", "TTJ"]:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # jet to tau fake efficiency
    jet_to_tau_fake_variations = []
    jet_to_tau_fake_variations.append(
        AddWeight("CMS_htt_jetToTauFake_13TeV", "jetToTauFake_weight",
                  Weight("(1.0+pt_2*0.002)", "jetToTauFake_weight"), "Up"))
    jet_to_tau_fake_variations.append(
        AddWeight("CMS_htt_jetToTauFake_13TeV", "jetToTauFake_weight",
                  Weight("(1.0-pt_2*0.002)", "jetToTauFake_weight"), "Down"))
    for variation in jet_to_tau_fake_variations:
        for process_nick in ["ZJ", "TTJ", "W", "VVJ"]:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # ZL fakes energy scale
    ele_fake_es_1prong_variations = create_systematic_variations(
        "CMS_ZLShape_et_1prong_13TeV", "tauEleFakeEsOneProng",
        DifferentPipeline)
    ele_fake_es_1prong1pizero_variations = create_systematic_variations(
        "CMS_ZLShape_et_1prong1pizero_13TeV", "tauEleFakeEsOneProngPiZeros",
        DifferentPipeline)

    if "et" in [args.gof_channel] + args.channels:
        for process_nick in ["ZL"]:
            for variation in ele_fake_es_1prong_variations + ele_fake_es_1prong1pizero_variations:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)

    mu_fake_es_1prong_variations = create_systematic_variations(
        "CMS_ZLShape_mt_1prong_13TeV", "tauMuFakeEsOneProng",
        DifferentPipeline)
    mu_fake_es_1prong1pizero_variations = create_systematic_variations(
        "CMS_ZLShape_mt_1prong1pizero_13TeV", "tauMuFakeEsOneProngPiZeros",
        DifferentPipeline)

    if "mt" in [args.gof_channel] + args.channels:
        for process_nick in ["ZL"]:
            for variation in mu_fake_es_1prong_variations + mu_fake_es_1prong1pizero_variations:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)

    # Zll reweighting
    zll_et_weight_variations = []
    zll_et_weight_variations.append(
        ReplaceWeight(
            "CMS_eFakeTau_1prong_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.98*1.12) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.2) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Up"))
    zll_et_weight_variations.append(
        ReplaceWeight(
            "CMS_eFakeTau_1prong_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.98*0.88) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.2) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Down"))
    zll_et_weight_variations.append(
        ReplaceWeight(
            "CMS_eFakeTau_1prong1pizero_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.98) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.2*1.12) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Up"))
    zll_et_weight_variations.append(
        ReplaceWeight(
            "CMS_eFakeTau_1prong1pizero_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.98) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.2*0.88) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Down"))
    for variation in zll_et_weight_variations:
        for process_nick in ["ZL"]:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
    zll_mt_weight_variations = []
    zll_mt_weight_variations.append(
        ReplaceWeight(
            "CMS_mFakeTau_1prong_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.75*1.25) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.0) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Up"))
    zll_mt_weight_variations.append(
        ReplaceWeight(
            "CMS_mFakeTau_1prong_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.75*0.75) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.0) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Down"))
    zll_mt_weight_variations.append(
        ReplaceWeight(
            "CMS_mFakeTau_1prong1pizero_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.75) + ((decayMode_2 == 1 || decayMode_2 == 2)*1.25) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Up"))
    zll_mt_weight_variations.append(
        ReplaceWeight(
            "CMS_mFakeTau_1prong1pizero_13TeV", "decay_mode_reweight",
            Weight(
                "(((decayMode_2 == 0)*0.75) + ((decayMode_2 == 1 || decayMode_2 == 2)*0.75) + ((decayMode_2 == 10)*1.0))",
                "decay_mode_reweight"), "Down"))
    for variation in zll_mt_weight_variations:
        for process_nick in ["ZL"]:
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)

    # b tagging
    btag_eff_variations = create_systematic_variations(
        "CMS_htt_eff_b_13TeV", "btagEff", DifferentPipeline)
    mistag_eff_variations = create_systematic_variations(
        "CMS_htt_mistag_b_13TeV", "btagMistag", DifferentPipeline)
    for variation in btag_eff_variations + mistag_eff_variations:
        for process_nick in [
                "ZTT", "ZL", "ZJ", "W", "TTT", "TTL", "TTJ", "VVT", "VVJ",
                "EWKZ"
        ] + signal_nicks:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)
    # Embedded event specifics
    mt_decayMode_variations = []
    mt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_3ProngEff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effUp_pi0Nom", "decayMode_SF"),
            "Up"))
    mt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_3ProngEff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effDown_pi0Nom", "decayMode_SF"),
            "Down"))
    mt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effNom_pi0Up", "decayMode_SF"),
            "Up"))
    mt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effNom_pi0Down", "decayMode_SF"),
            "Down"))
    for variation in mt_decayMode_variations:
        for process_nick in ["EMB"]:
            if "mt" in args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
    et_decayMode_variations = []
    et_decayMode_variations.append(
        ReplaceWeight(
            "CMS_3ProngEff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effUp_pi0Nom", "decayMode_SF"),
            "Up"))
    et_decayMode_variations.append(
        ReplaceWeight(
            "CMS_3ProngEff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effDown_pi0Nom", "decayMode_SF"),
            "Down"))
    et_decayMode_variations.append(
        ReplaceWeight(
            "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effNom_pi0Up", "decayMode_SF"),
            "Up"))
    et_decayMode_variations.append(
        ReplaceWeight(
            "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effNom_pi0Down", "decayMode_SF"),
            "Down"))
    for variation in et_decayMode_variations:
        for process_nick in ["EMB"]:
            if "et" in args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
    tt_decayMode_variations = []
    tt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_3ProngEff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effUp_pi0Nom", "decayMode_SF"),
            "Up"))
    tt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_3ProngEff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effDown_pi0Nom", "decayMode_SF"),
            "Down"))
    tt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effNom_pi0Up", "decayMode_SF"),
            "Up"))
    tt_decayMode_variations.append(
        ReplaceWeight(
            "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
            Weight("embeddedDecayModeWeight_effNom_pi0Down", "decayMode_SF"),
            "Down"))
    for variation in tt_decayMode_variations:
        for process_nick in ["EMB"]:
            if "tt" in args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)
    # 10% removed events in ttbar simulation (ttbar -> real tau tau events) will be added/subtracted to ZTT shape to use as systematic
    tttautau_process_mt = Process(
        "TTTT",
        TTTTEstimationMT(
            era, directory, mt, friend_directory=mt_friend_directory))
    tttautau_process_et = Process(
        "TTTT",
        TTTTEstimationET(
            era, directory, et, friend_directory=et_friend_directory))
    tttautau_process_tt = Process(
        "TTTT",
        TTTEstimationTT(
            era, directory, tt, friend_directory=tt_friend_directory))
    if 'mt' in [args.gof_channel] + args.channels:
        for category in mt_categories:
            mt_processes['ZTTpTTTauTauDown'] = Process(
                "ZTTpTTTauTauDown",
                AddHistogramEstimationMethod(
                    "AddHistogram", "nominal", era, directory, mt,
                    [mt_processes["EMB"], tttautau_process_mt], [1.0, -0.1]))
            systematics.add(
                Systematic(
                    category=category,
                    process=mt_processes['ZTTpTTTauTauDown'],
                    analysis="smhtt",
                    era=era,
                    variation=Relabel("CMS_htt_emb_ttbar_13TeV", "Down"),
                    mass="125"))

            mt_processes['ZTTpTTTauTauUp'] = Process(
                "ZTTpTTTauTauUp",
                AddHistogramEstimationMethod(
                    "AddHistogram", "nominal", era, directory, mt,
                    [mt_processes["EMB"], tttautau_process_mt], [1.0, 0.1]))
            systematics.add(
                Systematic(
                    category=category,
                    process=mt_processes['ZTTpTTTauTauUp'],
                    analysis="smhtt",
                    era=era,
                    variation=Relabel("CMS_htt_emb_ttbar_13TeV", "Up"),
                    mass="125"))

    if 'et' in [args.gof_channel] + args.channels:
        for category in et_categories:
            et_processes['ZTTpTTTauTauDown'] = Process(
                "ZTTpTTTauTauDown",
                AddHistogramEstimationMethod(
                    "AddHistogram", "nominal", era, directory, et,
                    [et_processes["EMB"], tttautau_process_et], [1.0, -0.1]))
            systematics.add(
                Systematic(
                    category=category,
                    process=et_processes['ZTTpTTTauTauDown'],
                    analysis="smhtt",
                    era=era,
                    variation=Relabel("CMS_htt_emb_ttbar_13TeV", "Down"),
                    mass="125"))

            et_processes['ZTTpTTTauTauUp'] = Process(
                "ZTTpTTTauTauUp",
                AddHistogramEstimationMethod(
                    "AddHistogram", "nominal", era, directory, et,
                    [et_processes["EMB"], tttautau_process_et], [1.0, 0.1]))
            systematics.add(
                Systematic(
                    category=category,
                    process=et_processes['ZTTpTTTauTauUp'],
                    analysis="smhtt",
                    era=era,
                    variation=Relabel("CMS_htt_emb_ttbar_13TeV", "Up"),
                    mass="125"))
    if 'tt' in [args.gof_channel] + args.channels:
        for category in tt_categories:
            tt_processes['ZTTpTTTauTauDown'] = Process(
                "ZTTpTTTauTauDown",
                AddHistogramEstimationMethod(
                    "AddHistogram", "EMB", era, directory, tt,
                    [tt_processes["EMB"], tttautau_process_tt], [1.0, -0.1]))
            systematics.add(
                Systematic(
                    category=category,
                    process=tt_processes['ZTTpTTTauTauDown'],
                    analysis="smhtt",
                    era=era,
                    variation=Relabel("CMS_htt_emb_ttbar_13TeV", "Down"),
                    mass="125"))

            tt_processes['ZTTpTTTauTauUp'] = Process(
                "ZTTpTTTauTauUp",
                AddHistogramEstimationMethod(
                    "AddHistogram", "nominal", era, directory, tt,
                    [tt_processes["EMB"], tttautau_process_tt], [1.0, 0.1]))
            systematics.add(
                Systematic(
                    category=category,
                    process=tt_processes['ZTTpTTTauTauUp'],
                    analysis="smhtt",
                    era=era,
                    variation=Relabel("CMS_htt_emb_ttbar_13TeV", "Up"),
                    mass="125"))

    # Fake factor uncertainties
    fake_factor_variations_et = []
    fake_factor_variations_mt = []
    for systematic_shift in [
            "ff_qcd{ch}_syst_13TeV{shift}",
            "ff_qcd_dm0_njet0{ch}_stat_13TeV{shift}",
            "ff_qcd_dm0_njet1{ch}_stat_13TeV{shift}",
            "ff_qcd_dm1_njet0{ch}_stat_13TeV{shift}",
            "ff_qcd_dm1_njet1{ch}_stat_13TeV{shift}", "ff_w_syst_13TeV{shift}",
            "ff_w_dm0_njet0{ch}_stat_13TeV{shift}",
            "ff_w_dm0_njet1{ch}_stat_13TeV{shift}",
            "ff_w_dm1_njet0{ch}_stat_13TeV{shift}",
            "ff_w_dm1_njet1{ch}_stat_13TeV{shift}", "ff_tt_syst_13TeV{shift}",
            "ff_tt_dm0_njet0_stat_13TeV{shift}",
            "ff_tt_dm0_njet1_stat_13TeV{shift}",
            "ff_tt_dm1_njet0_stat_13TeV{shift}",
            "ff_tt_dm1_njet1_stat_13TeV{shift}"
    ]:
        for shift_direction in ["Up", "Down"]:
            fake_factor_variations_et.append(
                ReplaceWeight(
                    "CMS_%s" % (systematic_shift.format(ch='_et', shift="")),
                    "fake_factor",
                    Weight(
                        "ff2_{syst}".format(
                            syst=systematic_shift.format(
                                ch="", shift="_%s" % shift_direction.lower())
                            .replace("_13TeV", "")),
                        "fake_factor"), shift_direction))
            fake_factor_variations_mt.append(
                ReplaceWeight(
                    "CMS_%s" % (systematic_shift.format(ch='_mt', shift="")),
                    "fake_factor",
                    Weight(
                        "ff2_{syst}".format(
                            syst=systematic_shift.format(
                                ch="", shift="_%s" % shift_direction.lower())
                            .replace("_13TeV", "")),
                        "fake_factor"), shift_direction))
    if "et" in [args.gof_channel] + args.channels:
        for variation in fake_factor_variations_et:
            systematics.add_systematic_variation(
                variation=variation,
                process=et_processes["FAKES"],
                channel=et,
                era=era)
    if "mt" in [args.gof_channel] + args.channels:
        for variation in fake_factor_variations_mt:
            systematics.add_systematic_variation(
                variation=variation,
                process=mt_processes["FAKES"],
                channel=mt,
                era=era)
    fake_factor_variations_tt = []
    for systematic_shift in [
            "ff_qcd{ch}_syst_13TeV{shift}",
            "ff_qcd_dm0_njet0{ch}_stat_13TeV{shift}",
            "ff_qcd_dm0_njet1{ch}_stat_13TeV{shift}",
            "ff_qcd_dm1_njet0{ch}_stat_13TeV{shift}",
            "ff_qcd_dm1_njet1{ch}_stat_13TeV{shift}",
            "ff_w{ch}_syst_13TeV{shift}", "ff_tt{ch}_syst_13TeV{shift}",
            "ff_w_frac{ch}_syst_13TeV{shift}",
            "ff_tt_frac{ch}_syst_13TeV{shift}",
            "ff_dy_frac{ch}_syst_13TeV{shift}"
    ]:
        for shift_direction in ["Up", "Down"]:
            fake_factor_variations_tt.append(
                ReplaceWeight(
                    "CMS_%s" % (systematic_shift.format(ch='_tt', shift="")),
                    "fake_factor",
                    Weight(
                        "(0.5*ff1_{syst}*(byTightIsolationMVArun2v1DBoldDMwLT_1<0.5)+0.5*ff2_{syst}*(byTightIsolationMVArun2v1DBoldDMwLT_2<0.5))".
                        format(
                            syst=systematic_shift.format(
                                ch="", shift="_%s" % shift_direction.lower())
                            .replace("_13TeV", "")),
                        "fake_factor"), shift_direction))
    if "tt" in [args.gof_channel] + args.channels:
        for variation in fake_factor_variations_tt:
            systematics.add_systematic_variation(
                variation=variation,
                process=tt_processes["FAKES"],
                channel=tt,
                era=era)

    # Gluon-fusion WG1 uncertainty scheme
    ggh_variations = []
    for unc in [
            "THU_ggH_Mig01", "THU_ggH_Mig12", "THU_ggH_Mu", "THU_ggH_PT120",
            "THU_ggH_PT60", "THU_ggH_Res", "THU_ggH_VBF2j", "THU_ggH_VBF3j",
            "THU_ggH_qmtop"
    ]:
        ggh_variations.append(
            AddWeight("{}_13TeV".format(unc), "{}_weight".format(unc),
                      Weight("({})".format(unc), "{}_weight".format(unc)),
                      "Up"))
        ggh_variations.append(
            AddWeight("{}_13TeV".format(unc), "{}_weight".format(unc),
                      Weight("(1.0/{})".format(unc), "{}_weight".format(unc)),
                      "Down"))
    for variation in ggh_variations:
        for process_nick in [nick for nick in signal_nicks if "ggH" in nick]:
            if "et" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=et_processes[process_nick],
                    channel=et,
                    era=era)
            if "mt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=mt_processes[process_nick],
                    channel=mt,
                    era=era)
            if "tt" in [args.gof_channel] + args.channels:
                systematics.add_systematic_variation(
                    variation=variation,
                    process=tt_processes[process_nick],
                    channel=tt,
                    era=era)

    # Produce histograms
    logger.info("Start producing shapes.")
    systematics.produce()
    logger.info("Done producing shapes.")


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("{}_produce_shapes.log".format(args.tag), logging.INFO)
    main(args)
