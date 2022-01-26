# -*- coding: utf-8 -*-
# @Author: Dongqing Sun
# @E-mail: Dongqingsun96@gmail.com
# @Date:   2020-07-19 17:20:32
# @Last Modified by:   Dongqing Sun
# @Last Modified time: 2020-11-02 17:35:25


import sys
import os
import re
import logging
from argparse import ArgumentError


def scatac_validator(args):
    """
    Validate parameters from scatac-init argument parsers.
    """
    if args.platform == "10x-genomics":
        if args.format == "fastq":
            if args.input_path == "":
                logging.error("--input_path is required. Please specify the directory where fastq files are stored!")
                exit(1)
            if args.fasta == "":
                logging.error("--fasta is required if fastq files are provided!")
                exit(1)
            if args.whitelist == "":
                logging.error("--whitelist is required for 10x-genomics data!")
                exit(1)
        if args.format == "bam":
            if args.input_path == "":
                logging.error("--input_path is required. Please specify the directory where bam files are stored!")
                exit(1)
        if args.format == "fragments":
            if args.input_path == "":
                logging.error("--input_path is required. Please specify the directory where fragments files are stored!")
                exit(1)
    if args.mapping == "chromap":
        if args.format == "fastq":
            if args.index == "":
                logging.error("--index is required if using chromap as alignment tool!")

    if args.platform == "sci-ATAC-seq":
        if args.format == "fastq":
            if args.input_path == "":
                logging.error("--input_path is required. Please specify the directory where fastq files are stored!")
                exit(1)
            if args.fasta == "":
                logging.error("--fasta is required if fastq files are provided!")
                exit(1)
        if args.format == "fragments":
            logging.error("Format of 'fragments' is supported only when the platform is '10x-genomics'.")
            exit(1)
        if args.mapping == "chromap" or args.mapping == "":
            logging.error("sci-ATAC-seq only support mapping with minimap2")

    if args.platform == "microfluidic":
        if args.format == "fastq":
            if args.input_path == "":
                logging.error("--input_path is required. Please specify the directory where fastq files are stored!")
                exit(1)
            if args.fasta == "":
                logging.error("--fasta is required if fastq files are provided!")
                exit(1)
        if args.format == "bam":
            logging.error("Format of 'bam' is supported when the platform is '10x-genomics' or 'sci-ATAC-seq'.")
            exit(1)
        if args.format == "fragments":
            logging.error("Format of 'fragments' is supported only when the platform is '10x-genomics'.")
            exit(1)

    if args.signature not in ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']:
        if os.path.exists(args.signature):
            pass
        else:
            logging.error("Please specify the signature built in MAESTRO or provide customized signature file. See --signature help for more details!")
            exit(1)


def scrna_validator(args):
    """
    Validate parameters from scrna-init argument parsers.
    """

    if args.platform == "10x-genomics":
        if args.whitelist == "":
            logging.error("--whitelist is required for 10x-genomics data!")
            exit(1)

    if args.platform == "Dropseq":
        if args.input_path == "":
            logging.error("--input_path is required for Dropsea data. Please specify the directory where fastq files are stored!")
            exit(1)
        if args.fastq_barcode == "":
            logging.error("--fastq-barcode is required for Dropsea data. Please specify the barcode fastq file!")
            exit(1)
        if args.fastq_transcript == "":
            logging.error("--fastq-transcript is required for Dropsea data. Please specify the transcript fastq file!")
            exit(1)
        if args.whitelist == "":
            logging.error("--whitelist is required for Dropsea data. Please provide the barcode whitelist.")
            exit(1)

    if args.platform == "Smartseq2":
        if args.input_path == "":
            logging.error("--input_path is required. Please specify the directory where fastq files are stored!")
            exit(1)
        if args.rsem == "":
            logging.error("--rsem is required. Please provide the prefix of transcript references for RSEM. See --rsem help for more details.")
            exit(1)

    if args.signature not in ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']:
        if os.path.exists(args.signature):
            pass
        else:
            logging.error("Please specify the signature built in MAESTRO or provide customized signature file. See --signature help for more details!")
            exit(1)
