# -*- coding: utf-8 -*-
# @Author: Dongqing Sun
# @E-mail: Dongqingsun96@gmail.com
# @Date:   2020-02-23 19:40:27
# @Last Modified by: Gali Bai
# @Last Modified time: 2021-07-12 17:34:46

import os
import shutil
import argparse as ap
from jinja2 import Template
from pkg_resources import resource_filename

def scrna_parser(subparsers):
    """
    Add main function scrna-init argument parsers.
    """

    workflow = subparsers.add_parser("scrna-init", help = "Initialize the MAESTRO scRNA-seq workflow in a given directory. "
        "This will install a Snakefile and a config file in this directory. "
        "You can configure the config file according to your needs, and run the workflow with Snakemake.")

    # Input files arguments
    group_input = workflow.add_argument_group("Input files arguments")
    group_input.add_argument("--platform", dest = "platform", default = "10x-genomics",
        choices = ["10x-genomics", "Dropseq", "Smartseq2"],
        help = "Platform of single cell RNA-seq. DEFAULT: 10x-genomics.")
    group_input.add_argument("--sample-file", dest = "sample_file", type = str, default = "samples.json",
        help = "JSON file with sample file information")
    group_input.add_argument("--fastq-barcode", dest = "fastq_barcode", type = str, default = "",
        help = "Specify the barcode fastq file, only for the platform of 'Dropseq'. "
        "If there are multiple pairs of fastq, please provide a comma-separated list of barcode fastq files. "
        "For example, --fastq-barcode test1_1.fastq,test2_1.fastq")
    group_input.add_argument("--fastq-transcript", dest = "fastq_transcript", type = str, default = "",
        help = "Specify the transcript fastq file, only for the platform of 'Dropseq'. "
        "If there are multiple pairs of fastq, please provide a comma-separated list of barcode fastq files. "
        "For example, --fastq-barcode test1_2.fastq,test2_2.fastq")
    group_input.add_argument("--species", dest = "species", default = "GRCh38",
        choices = ["GRCh38", "GRCm38"], type = str,
        help = "Specify the genome assembly (GRCh38 for human and GRCm38 for mouse). DEFAULT: GRCh38.")

    #STARsolo arguments
    group_star = workflow.add_argument_group("STARsolo parameters arguments")
    group_star.add_argument("--STARsolo_Features", dest= "STARsolo_Features", default = "Gene", type = str,
        choices = ["Gene", "GeneFull", "Gene GeneFull", "SJ", "Velocyto"],
        help = "Parameters passed to STARsolo --soloFeatures."
        "specify --soloFeatures Gene for single-cell data."
        "specify --soloFeatures GeneFull for single-nuclei data"
        "specify --soloFeatures Gene GeneFull for getting both counts in exons level and exon + intron level (velocity)")
    group_star.add_argument("--STARsolo_threads", dest = "STARsolo_threads", default = 12, type = int,
        help = "Threads for running STARsolo. DEFAULT: 12.")

    # Output arguments
    group_output = workflow.add_argument_group("Running and output arguments")
    group_output.add_argument("--cores", dest = "cores", default = 10,
        type = int, help = "The number of cores to use. DEFAULT: 10.")
    group_output.add_argument("--rseqc", dest = "rseqc", action = "store_true",
        help = "Whether or not to run RSeQC. "
        "If set, the pipeline will include the RSeQC part and then takes a longer time. "
        "By default (not set), the pipeline will skip the RSeQC part.")
    group_output.add_argument("--directory", dest = "directory", type = str, default = "MAESTRO",
        help = "Path to the directory where the workflow shall be initialized and results shall be stored. DEFAULT: MAESTRO.")
    group_output.add_argument("--mergedname", dest = "mergedname", type = str, default = "All_sample",
        help = "Prefix of merged output files. DEFAULT: All_sample. ")
    group_output.add_argument("--outprefix", dest = "outprefix", type = str, default = "MAESTRO",
        help = "Prefix of output files. DEFAULT: MAESTRO. ")

    # Quality control cutoff
    group_cutoff = workflow.add_argument_group("Quality control arguments")
    group_cutoff.add_argument("--count-cutoff", dest = "count_cutoff", default = 1000, type = int,
        help = "Cutoff for the number of count in each cell. DEFAULT: 1000.")
    group_cutoff.add_argument("--gene-cutoff", dest = "gene_cutoff", default = 500, type = int,
        help = "Cutoff for the number of genes included in each cell. DEFAULT: 500.")
    group_cutoff.add_argument("--cell-cutoff", dest = "cell_cutoff", default = 10, type = int,
        help = "Cutoff for the number of cells covered by each gene. DEFAULT: 10.")

    # Reference genome arguments
    group_reference = workflow.add_argument_group("Reference genome arguments")
    group_reference.add_argument("--mapindex", dest = "mapindex",
        required = True,
        help = "Genome index directory for STAR. Users can just download the index file for human and mouse "
        "from http://cistrome.org/~galib/MAESTRO/references/scRNA/Refdata_scRNA_MAESTRO_GRCh38_1.2.2.tar.gz and "
        "http://cistrome.org/~galib/MAESTRO/references/scRNA/Refdata_scRNA_MAESTRO_GRCm38_1.2.2.tar.gz, respectively, and decompress them. "
        "Then specify the index directory for STAR, for example, 'Refdata_scRNA_MAESTRO_GRCh38_1.2.2/GRCh38_STAR_2.7.6a'.")
    group_reference.add_argument("--rsem", dest = "rsem", default = "",
        help = "The prefix of transcript references for RSEM used by rsem-prepare-reference (Only required when the platform is Smartseq2). "
        "Users can directly download the annotation file for huamn and mouse from "
        "http://cistrome.org/~galib/MAESTRO/references/scRNA/Refdata_scRNA_MAESTRO_GRCh38_1.1.0.tar.gz and "
        "http://cistrome.org/~galib/MAESTRO/references/scRNA/Refdata_scRNA_MAESTRO_GRCm38_1.1.0.tar.gz,, respectively, and decompress them. "
        "Then specify the prefix for RSEM, for example, 'Refdata_scRNA_MAESTRO_GRCh38_1.1.0/GRCh38_RSEM_1.3.2/GRCh38'.")

    # Barcode arguments
    group_barcode = workflow.add_argument_group("Barcode arguments, for platform of 'Dropseq' or '10x-genomics'")
    group_barcode.add_argument("--whitelist", dest = "whitelist", type = str, default = "",
        help = "If the platform is 'Dropseq' or '10x-genomics', please specify the barcode library (whitelist) "
        "so that STARsolo can do the error correction and demultiplexing of cell barcodes. "
        "The 10X Chromium whitelist file can be found inside the CellRanger distribution. "
        "Please make sure that the whitelist is compatible with the specific version of the 10X chemistry: V2 or V3. "
        "For example, in CellRanger 3.1.0, the V2 whitelist is "
        "'cellranger-3.1.0/cellranger-cs/3.1.0/lib/python/cellranger/barcodes/737K-august-2016.txt'. "
        "The V3 whitelist is 'cellranger-3.1.0/cellranger-cs/3.1.0/lib/python/cellranger/barcodes/3M-february-2018.txt'. ")
    group_barcode.add_argument("--barcode-start", dest = "barcode_start", type = int, default = 1,
        help = "The start site of each barcode. DEFAULT: 1. ")
    group_barcode.add_argument("--barcode-length", dest = "barcode_length", type = int, default = 16,
        help = "The length of cell barcode. For 10x-genomics, the length of barcode is 16. DEFAULT: 16. ")
    group_barcode.add_argument("--umi-start", dest = "umi_start", type = int, default = 17,
        help = "The start site of UMI. DEFAULT: 17. ")
    group_barcode.add_argument("--umi-length", dest = "umi_length", type = int, default = 10,
        help = "The length of UMI. For 10x-genomics, the length of V2 chemistry is 10. "
        "For 10X V3 chemistry, the length is 12. DEFAULT: 10. ")
    group_barcode.add_argument("--trimR1", dest = "trimR1", action = "store_true",
        help = "Whether or not to run the R1 file. "
        "If set, the pipeline will include the trim off anything after the R1 reads past barcode information. "
        "Only necessary if reads were sequenced past these barcodes, by default not set.")


    # Regulator identification
    group_regulator = workflow.add_argument_group("Regulator identification arguments")
    group_regulator.add_argument("--lisadir", dest = "lisadir", type = str, default = "",
        help = "Path to lisa data files. For human and mouse, data can be downloaded from http://cistrome.org/~alynch/data/lisa_data/hg38_1000_2.0.h5"
        "and http://cistrome.org/~alynch/data/lisa_data/mm10_1000_2.0.h5")


    # Signature file arguments
    group_signature = workflow.add_argument_group("Cell signature arguments")
    group_signature.add_argument("--signature", dest = "signature", type = str, default = "human.immune.CIBERSORT",
        help = "Cell signature file used to annotate cell types. MAESTRO provides several sets of built-in cell signatures. "
        "Users can choose from ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']. "
        "Custom cell signatures are also supported. In this situation, users need to provide the file location of cell signatures, "
        "and the signature file is tab-seperated without header. The first column is cell type, and the second column is signature gene. "
        "DEFAULT: human.immune.CIBERSORT.")

    return

def scatac_parser(subparsers):
    """
    Add main function scatac-init argument parsers.
    """
    workflow = subparsers.add_parser("scatac-init", help = "Initialize the MAESTRO scATAC-seq workflow in a given directory. "
        "This will install the snakemake rules and a config file in this directory. "
        "You can configure the config file according to your needs, and run the workflow with Snakemake "
        "(https://bitbucket.org/johanneskoester/snakemake).")

    # Multi-Sample processing parameters
    group_multi = workflow.add_argument_group(" multi-sample processing parameters")
    group_multi.add_argument("--batch", dest = "batch", action = "store_true",
        help = "If set as true, peaks will be called on each sample individually first and peaks from all samples will be merged."
        "A count matrix for each sample will be produced based on the merged peak set.")
    group_multi.add_argument("--consensus_peaks", dest = "consensus_peaks", action = "store_true",
        help = "When batch is TRUE, users can define whether to merge consensus peaks from each sample."
        "If set as true, users should also set number of cutoff_samples to define consensus.")
    group_multi.add_argument("--cutoff_samples", dest = "cutoff_samples", default = 2, type = int,
        help = "Minimum number of samples to present consensus peaks. The peaks present in at least cutoff_samples will be kept")
    group_multi.add_argument("--bulk_peaks", dest = "bulk_peaks", action = "store_true",
        help = "For multi-samples from the same experiment, if set as true, peaks will be called after merging all bam file."
        "Bulk_peaks and consensus_peaks are mutually exclusive.")
    group_multi.add_argument("--downsample", dest = "downsample", action = "store_true",
        help = "For deeply sequenced samples, bam files can be downsampled to a certain number of reads (target_reads) to get peak set.")
    group_multi.add_argument("--target_reads", dest = "target_reads", default = 50000000, type = int,
        help = "Number of reads to be kept in downsampling. If the sample has fewer than the target_reads, the original number of reads will be kept.")

    # Input files arguments
    group_input = workflow.add_argument_group("Input files arguments")
    group_input.add_argument("--input_path", dest = "input_path", type = str, default = "",
        help = "Path to input fastq files.")
    group_input.add_argument("--gzip", dest = "gzip", action = "store_true",
        help = "Set as True if the input files are gzipped.")
    group_input.add_argument("--species", dest = "species", default = "GRCh38",
        choices = ["GRCh38", "GRCm38"], type = str,
        help = "Specify the genome assembly (GRCh38 for human and GRCm38 for mouse). DEFAULT: GRCh38.")
    group_input.add_argument("--platform", dest = "platform", default = "10x-genomics",
        choices = ["10x-genomics", "sci-ATAC-seq", "microfluidic"],
        help = "Platform of single cell ATAC-seq. DEFAULT: 10x-genomics.")
    group_input.add_argument("--format", dest = "format", default = "fastq",
        choices = ["fastq", "fragments", "bam"], type = str,
        help = "The format of input files. Users can start with sequencing fastq files, "
        "bam files with CB tag or fragments.tsv.gz file generated by CellRanger ATAC.")
    group_input.add_argument("--mapping", dest = "mapping", default = "chromap", type = str,
        choices = ["chromap", "minimap2"],
        help = "Choose the aligment tool for scATAC-seq from either chromap or minimap2. DEFAULT: chromap.")
    group_input.add_argument("--deduplication", dest = "deduplication", default = "cell-level",
        choices = ["cell-level", "bulk-level"], type = str,
        help = "deduplication level: cell level or bulk level ")

    # Reference genome arguments
    group_reference = workflow.add_argument_group("Reference genome arguments")
    group_reference.add_argument("--giggleannotation", dest = "giggleannotation",
        required = True,
        help = "Path of the giggle annotation file required for regulator identification. "
        "Please download the annotation file from "
        "http://cistrome.org/~galib/MAESTRO/references/giggle.all.tar.gz and decompress it.")
    group_reference.add_argument("--fasta", dest = "fasta", type = str,
        default = "",
        help = "Genome fasta file for minimap2 and chromap."
        "Users can just download the fasta file for huamn and mouse from "
        "http://cistrome.org/~galib/MAESTRO/references/scATAC/Refdata_scATAC_MAESTRO_GRCh38_1.1.0.tar.gz and "
        "http://cistrome.org/~galib/MAESTRO/references/scATAC/Refdata_scATAC_MAESTRO_GRCm38_1.1.0.tar.gz, respectively and decompress them. "
        "For example, 'Refdata_scATAC_MAESTRO_GRCh38_1.1.0/GRCh38_genome.fa'.")
    group_reference.add_argument("--index", dest = "index", type = str,
        default = "",
        help = "Path of the reference index file for chromap. "
        "Users need to build the index file for the reference using command "
        "chromap -i -r ref.fa -o index")

    # Barcode library arguments
    group_barcode = workflow.add_argument_group("Barcode library arguments, only for platform of 'sci-ATAC-seq' and '10x-genomics'")
    group_barcode.add_argument("--whitelist", dest = "whitelist", type = str,
        default = "",
        help = "If the platform is 'sci-ATAC-seq' or '10x-genomics', please specify the barcode library (whitelist) "
        "so that the pipeline can correct cell barcodes with 1 base mismatched. "
        "Otherwise, the pipeline will automatically output the barcodes with enough read count (>1000)."
        "The 10X Chromium whitelist file can be found inside the CellRanger-ATAC distribution. "
        "For example, in CellRanger-ATAC 1.1.0, the whitelist is "
        "'cellranger-atac-1.1.0/cellranger-atac-cs/1.1.0/lib/python/barcodes/737K-cratac-v1.txt'. ")

    # Output arguments
    group_output = workflow.add_argument_group("Output arguments")
    group_output.add_argument("--cores", dest = "cores", default = 8,
        type = int, help = "Number of cores to use. DEFAULT: 8.")
    group_output.add_argument("--directory", "-d",  dest = "directory", type = str, default = "MAESTRO",
        help = "Path to the directory where the workflow shall be initialized and results shall be stored. DEFAULT: MAESTRO.")

    # Signature file arguments
    group_annotation = workflow.add_argument_group("Cell-type annotation arguments")
    group_annotation.add_argument("--annotation", dest = "annotation", action = "store_true",
        help = "Whether or not to perform cell-type annotation. "
        "By default (not set), MAESTRO will skip the step of cell-type annotation. "
        "If set, please specify the method of cell-type annotation through --method. ")
    group_annotation.add_argument("--method", dest = "method", type = str, default = "RP-based",
        choices = ["RP-based", "peak-based", "both"],
        help = "Method to annotate cell types. MAESTRO provides two strategies to annotate cell types for scATAC-seq data. "
        "Users can choose from 'RP-based' and 'peak-based', or choose to run both of them. "
        "One is based on gene regulatory potential predicted by RP model. Another is based on the bulk chromatin accessibility data from Cistrome database. "
        "If 'RP-based' is set, MAESTRO performs the cell-type annotation using the gene regulatory potential to represent gene expression, "
        "and the logFC of gene regulatory potential between one cluster and all the other cells is used to calculate the gene signature scores. "
        "If 'peak-based' is set, MAESTRO utilizes GIGGLE to evaluate the enrichment of bulk chromatin accessibility peaks on cluster-specific peaks from scATAC-seq data, "
        "and then transfers the Cistrome cluster identity from the most enriched bulk chromatin accessibility data as the cell-type annotation for the scATAC-seq cluster. "
        "See the MAESTRO paper for more details. DEFAULT: RP-based. ")
    group_annotation.add_argument("--signature", dest = "signature", type = str, default = "human.immune.CIBERSORT",
        help = "Cell signature file used to annotate cell types (required when method is set as 'RP-based'). MAESTRO provides several sets of built-in cell signatures. "
        "Users can choose from ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']. "
        "Custom cell signatures are also supported. In this situation, users need to provide the file location of cell signatures, "
        "and the signature file is tab-seperated without header. The first column is cell type, and the second column is signature gene. "
        "DEFAULT: human.immune.CIBERSORT. ")

    # Customized peak arguments
    group_peak = workflow.add_argument_group("Customized peak arguments")
    group_peak.add_argument("--custompeak", dest = "custompeak", action = "store_true",
        help = "Whether or not to provide custom peaks. If set, users need to provide "
        "the file location of peak file through '--custompeak-file' and then MAESTRO will merge "
        "the custom peak file and the peak file called from all fragments using MACS2. "
        "By default (not set), the pipeline will use the peaks called using MACS2.")
    group_peak.add_argument("--custompeak_file", dest = "custompeak_file", type = str, default = "",
        help = "If '--custompeak' is set, please provide the file location of custom peak file. "
        "The peak file is BED formatted with tab seperated. "
        "The first column is chromsome, the second is chromStart, and the third is chromEnd.")
    group_peak.add_argument("--shortpeak", dest = "shortpeak", action = "store_true",
        help = "Whether or not to call peaks from short fragments (shorter than 150bp). If set, "
        "MAESTRO will merge the peaks called from all fragments and those called from short fragments, "
        "and then use the merged peak file for further analysis. "
        "If not (by default), the pipeline will only use peaks called from all fragments.")
    group_peak.add_argument("--clusterpeak", dest = "clusterpeak", action = "store_true",
        help = "Whether or not to call peaks by cluster. If set, "
        "MAESTRO will split the bam file according to the clustering result, "
        "and then call peaks for each cluster. "
        "By default (not set), MAESTRO will skip this step.")

    # Gene score arguments
    group_genescore = workflow.add_argument_group("Gene score arguments")
    group_genescore.add_argument("--rpmodel", dest = "rpmodel", default = "Enhanced",
        choices = ["Simple", "Enhanced"],
        help = "The RP model to use to calaculate gene score. "
        "For each gene, simple model summarizes the impact of all regulatory elements within the up/dowm-stream of TSS. "
        "On the basis of simple model, enhanced model includes the regulatory elements within the exon region, "
        "and also excludes the regulatory elements overlapped with another gene (the promoter and exon of a nearby gene). "
        "See the MAESTRO paper for more details. DEFAULT: Enhanced.")
    group_genescore.add_argument("--genedistance", dest = "genedistance", default = 10000, type = int,
        help = "Gene score decay distance, could be optional from 1kb (promoter-based regulation) "
        "to 10kb (enhancer-based regulation). DEFAULT: 10000.")

    # Quality control cutoff
    group_cutoff = workflow.add_argument_group("Quality control arguments")
    group_cutoff.add_argument("--peak_cutoff", dest = "peak_cutoff", default = 100, type = int,
        help = "Minimum number of peaks included in each cell. DEFAULT: 100.")
    group_cutoff.add_argument("--count_cutoff", dest = "count_cutoff", default = 1000, type = int,
        help = "Cutoff for the number of count in each cell. DEFAULT: 1000.")
    group_cutoff.add_argument("--frip_cutoff", dest = "frip_cutoff", default = 0.2, type = float,
        help = "Cutoff for fraction of reads in promoter in each cell. DEFAULT: 0.2.")
    group_cutoff.add_argument("--cell_cutoff", dest = "cell_cutoff", default = 10, type = int,
        help = "Minimum number of cells covered by each peak. DEFAULT: 10.")

    return

def integrate_parser(subparsers):
    """
    Add main function init-scatac argument parsers.
    """

    workflow = subparsers.add_parser("integrate-init", help = "Initialize the MAESTRO integration workflow in a given directory. "
        "This will install a Snakefile and a config file in this directory. "
        "You can configure the config file according to your needs, and run the workflow with Snakemake.")

    # Input files arguments
    group_input = workflow.add_argument_group("Input files arguments")
    group_input.add_argument("--rna-object", dest = "rna_object", required = True, type = str,
        help = "Path of scRNA Seurat object generated by MAESTRO scRNA pipeline.")
    group_input.add_argument("--atac-object", dest = "atac_object", required = True, type = str,
        help = "Path of scATAC Seurat object generated by MAESTRO scATAC pipeline.")

    # Output arguments
    group_output = workflow.add_argument_group("Running and output arguments")
    group_output.add_argument("--directory", "-d", dest = "directory", default = "MAESTRO",
        help = "Path to the directory where the workflow shall be initialized and results shall be stored. DEFAULT: MAESTRO.")
    group_output.add_argument("--outprefix", dest = "outprefix", type = str, default = "MAESTRO",
        help = "Prefix of output files. DEFAULT: MAESTRO.")

    return

def multiome_parser(subparsers):
    """
    Add main function init-scatac argument parsers.
    """

    workflow = subparsers.add_parser("multiome-init", help = "Initialize the MAESTRO multiome workflow in a given directory. "
        "This will install a Snakefile and a config file in this directory. "
        "You can configure the config file according to your needs, and run the workflow with Snakemake "
        "(https://bitbucket.org/johanneskoester/snakemake).")

    # Running arguments for multiome data
    group_output = workflow.add_argument_group("Running arguments for both RNA and ATAC libraries")
    group_output.add_argument("--species", dest = "species", default = "GRCh38",
        choices = ["GRCh38", "GRCm38"], type = str,
        help = "Specify the genome assembly (GRCh38 for human and GRCm38 for mouse). DEFAULT: GRCh38.")
    group_output.add_argument("--cores", dest = "cores", default = 8,
        type = int, help = "Number of cores to use. DEFAULT: 8.")
    group_output.add_argument("--directory", "-d",  dest = "directory", type = str, default = "MAESTRO",
        help = "Path to the directory where the workflow shall be initialized and results shall be stored. DEFAULT: MAESTRO.")
    group_output.add_argument("--outprefix", dest = "outprefix", type = str, default = "MAESTRO",
        help = "Prefix of output files. DEFAULT: MAESTRO.")
    group_output.add_argument("--gzip", dest = "gzip", action = "store_true",
        help = "Set as True if the input files are gzipped.")

    # Input files arguments
    group_input_rna = workflow.add_argument_group("Input and running arguments for scRNA-seq")
    group_input_rna.add_argument("--rna-fastq-dir", dest = "rna_fastq_dir", type = str, default = "",
        help = "Directory where RNA fastq files are stored.")
    #group_input_rna.add_argument("--rna-fastq-prefix", dest = "rna_fastq_prefix", type = str, default = "",
        #help = "Sample name of fastq file, only for the platform of '10x-genomics'. "
        #"If there is a file named pbmc_granulocyte_sorted_3k_S1_L004_R2_001.fastq.gz, the prefix is 'pbmc_granulocyte_sorted_3k'.")
    group_input_rna.add_argument("--rna-whitelist", dest = "rna_whitelist", type = str, default = "",
        help = "RNA barcode whitlist for STARsolo to do the error correction and demultiplexing of cell barcodes. "
        "If the multiome data is generated by 10X genomics platform, the barcode library file is located at "
        "<path_to_cellrangerarc>/cellranger-arc-1.0.1/lib/python/cellranger/barcodes/. "
        "The two sets of barcodes from RNA and ATAC should be associated by line number. "
        "For example, the barcode from line 1748 of the RNA barcode list is associated with the barcode from line 1748 of the ATAC barcode list. ")
    group_input_rna.add_argument("--rna-mapindex", dest = "rna_mapindex",
        required = True,
        help = "Genome index directory for STAR. Users can just download the index file for human and mouse "
        "from http://cistrome.org/~galib/Refdata_scRNA_MAESTRO_GRCh38_1.2.2.tar.gz and "
        "http://cistrome.org/~galib/Refdata_scRNA_MAESTRO_GRCm38_1.2.2.tar.gz, respectively, and decompress them. "
        "Then specify the index directory for STAR, for example, 'Refdata_scRNA_MAESTRO_GRCh38_1.2.2/GRCh38_STAR_2.7.6a'.")
    group_input_rna.add_argument("--rseqc", dest = "rseqc", action = "store_true",
        help = "Whether or not to run RSeQC. "
        "If set, the pipeline will include the RSeQC part and then takes a longer time. "
        "By default (not set), the pipeline will skip the RSeQC part.")
    group_input_rna.add_argument("--lisadir", dest = "lisadir", type = str, default = "",
        help = "Path to lisa data files for regulator identification. For human and mouse, data can be downloaded from http://cistrome.org/~alynch/data/lisa_data/hg38_1000_2.0.h5"
        "and http://cistrome.org/~alynch/data/lisa_data/mm10_1000_2.0.h5")

    # Quality control cutoff for scRNA-seq
    group_cutoff_rna = workflow.add_argument_group("Quality control arguments for scRNA-seq")
    group_cutoff_rna.add_argument("--rna-count-cutoff", dest = "rna_count_cutoff", default = 1000, type = int,
        help = "Cutoff for the number of count in each cell for RNA library. DEFAULT: 1000.")
    group_cutoff_rna.add_argument("--rna-gene-cutoff", dest = "rna_gene_cutoff", default = 500, type = int,
        help = "Cutoff for the number of genes included in each cell. DEFAULT: 500.")
    group_cutoff_rna.add_argument("--rna-cell-cutoff", dest = "rna_cell_cutoff", default = 10, type = int,
        help = "Cutoff for the number of cells covered by each gene for RNA library. DEFAULT: 10.")


    # Input files arguments for scATAC-seq
    group_input_atac = workflow.add_argument_group("Input and running arguments for scATAC-seq")
    group_input_atac.add_argument("--atac-fastq-dir", dest = "atac_fastq_dir", type = str, default = "",
        help = "Directory where ATAC fastq files are stored.")
    #group_input_atac.add_argument("--atac-fastq-prefix", dest = "atac_fastq_prefix", type = str, default = "",
        #help = "Sample name of fastq file, only for the platform of '10x-genomics'. "
        #"If there is a file named pbmc_granulocyte_sorted_3k_S12_L001_R1_001.fastq.gz, the prefix is 'pbmc_granulocyte_sorted_3k'.")
    group_input_atac.add_argument("--atac-whitelist", dest = "atac_whitelist", type = str, default = "",
        help = "Location of ATAC barcode library file. "
        "If the multiome data is generated by 10X genomics platform, the barcode library file is located at "
        "<path_to_cellrangerarc>/cellranger-arc-1.0.1/lib/python/atac/barcodes/. "
        "The two sets of barcodes from RNA and ATAC should be associated by line number. "
        "For example, the barcode from line 1748 of the RNA barcode list is associated with the barcode from line 1748 of the ATAC barcode list. ")
    group_input_atac.add_argument("--mapping", dest = "mapping", default = "chromap", type = str,
        choices = ["chromap", "minimap2"],
        help = "Choose the aligment tool for scATAC-seq from either chromap or minimap2. DEFAULT: chromap.")
    group_input_atac.add_argument("--atac-fasta", dest = "atac_fasta",
        default = "",
        help = "Genome fasta file for minimap2 and chromap. "
        "Users can just download the fasta file for huamn and mouse from "
        "http://cistrome.org/~chenfei/MAESTRO/Refdata_scATAC_MAESTRO_GRCh38_1.1.0.tar.gz and "
        "http://cistrome.org/~chenfei/MAESTRO/Refdata_scATAC_MAESTRO_GRCm38_1.1.0.tar.gz, respectively and decompress them. "
        "For example, 'Refdata_scATAC_MAESTRO_GRCh38_1.1.0/GRCh38_genome.fa'.")
    group_input_atac.add_argument("--atac-mapindex", dest = "atac_mapindex", type = str,
        default = "",
        help = "Path of the reference index file for chromap. "
        "Users need to build the index file for the reference using command "
        "chromap -i -r ref.fa -o index")
    group_input_atac.add_argument("--giggleannotation", dest = "giggleannotation", required = True,
        help = "Path of the giggle annotation file required for regulator identification. "
        "Please download the annotation file from "
        "http://cistrome.org/~chenfei/MAESTRO/giggle.tar.gz and decompress it.")

    # Quality control cutoff for scATAC-seq
    group_cutoff = workflow.add_argument_group("Quality control arguments for scATAC-seq")
    group_cutoff.add_argument("--atac-peak-cutoff", dest = "atac_peak_cutoff", default = 100, type = int,
        help = "Minimum number of peaks included in each cell. DEFAULT: 100.")
    group_cutoff.add_argument("--atac-count-cutoff", dest = "atac_count_cutoff", default = 1000, type = int,
        help = "Cutoff for the number of count in each cell for ATAC library. DEFAULT: 1000.")
    group_cutoff.add_argument("--atac-frip-cutoff", dest = "atac_frip_cutoff", default = 0.2, type = float,
        help = "Cutoff for fraction of reads in promoter in each cell. DEFAULT: 0.2.")
    group_cutoff.add_argument("--atac-cell-cutoff", dest = "atac_cell_cutoff", default = 10, type = int,
        help = "Minimum number of cells covered by each peak. DEFAULT: 10.")

    # Customized peak arguments
    group_peak = workflow.add_argument_group("Customized peak arguments for scATAC-seq")
    group_peak.add_argument("--custompeak", dest = "custompeak", action = "store_true",
        help = "Whether or not to provide custom peaks. If set, users need to provide "
        "the file location of peak file through '--custompeak-file' and then MAESTRO will merge "
        "the custom peak file and the peak file called from all fragments using MACS2. "
        "By default (not set), the pipeline will use the peaks called using MACS2.")
    group_peak.add_argument("--custompeak-file", dest = "custompeak_file", type = str, default = "",
        help = "If '--custompeak' is set, please provide the file location of custom peak file. "
        "The peak file is BED formatted with tab seperated. "
        "The first column is chromsome, the second is chromStart, and the third is chromEnd.")
    group_peak.add_argument("--shortpeak", dest = "shortpeak", action = "store_true",
        help = "Whether or not to call peaks from short fragments (shorter than 150bp). If set, "
        "MAESTRO will merge the peaks called from all fragments and those called from short fragments, "
        "and then use the merged peak file for further analysis. "
        "If not (by default), the pipeline will only use peaks called from all fragments.")
    group_peak.add_argument("--clusterpeak", dest = "clusterpeak", action = "store_true",
        help = "Whether or not to call peaks by cluster. If set, "
        "MAESTRO will split the bam file according to the clustering result, "
        "and then call peaks for each cluster. "
        "By default (not set), MAESTRO will skip this step.")

    # Gene score arguments
    group_genescore = workflow.add_argument_group("Gene score arguments for scATAC-seq")
    group_genescore.add_argument("--rpmodel", dest = "rpmodel", default = "Enhanced",
        choices = ["Simple", "Enhanced"],
        help = "The RP model to use to calaculate gene score. "
        "For each gene, simple model summarizes the impact of all regulatory elements within the up/dowm-stream of TSS. "
        "On the basis of simple model, enhanced model includes the regulatory elements within the exon region, "
        "and also excludes the regulatory elements overlapped with another gene (the promoter and exon of a nearby gene). "
        "See the MAESTRO paper for more details. DEFAULT: Enhanced.")
    group_genescore.add_argument("--genedistance", dest = "genedistance", default = 10000, type = int,
        help = "Gene score decay distance, could be optional from 1kb (promoter-based regulation) "
        "to 10kb (enhancer-based regulation). DEFAULT: 10000.")

    # Signature file arguments
    group_annotation = workflow.add_argument_group("Cell-type annotation arguments")
    group_annotation.add_argument("--annotation", dest = "annotation", action = "store_true",
        help = "Whether or not to perform cell-type annotation for scATAC-seq. "
        "Note: MAESTRO will perform cell-type annotation for scRNA-seq whether this argument is set as True or False. "
        "By default (not set), MAESTRO will skip the step of cell-type annotation for scATAC-seq. "
        "If set, please specify the method of cell-type annotation through --method. ")
    group_annotation.add_argument("--method", dest = "method", type = str, default = "RP-based",
        choices = ["RP-based", "peak-based", "both"],
        help = "Method to annotate cell types for scATAC-seq. MAESTRO provides two strategies to annotate cell types for scATAC-seq data. "
        "Users can choose from 'RP-based' and 'peak-based', or choose to run both of them. "
        "One is based on gene regulatory potential predicted by RP model. Another is based on the bulk chromatin accessibility data from Cistrome database. "
        "If 'RP-based' is set, MAESTRO performs the cell-type annotation using the gene regulatory potential to represent gene expression, "
        "and the logFC of gene regulatory potential between one cluster and all the other cells is used to calculate the gene signature scores. "
        "If 'peak-based' is set, MAESTRO utilizes GIGGLE to evaluate the enrichment of bulk chromatin accessibility peaks on cluster-specific peaks from scATAC-seq data, "
        "and then transfers the Cistrome cluster identity from the most enriched bulk chromatin accessibility data as the cell-type annotation for the scATAC-seq cluster. "
        "See the MAESTRO paper for more details. DEFAULT: RP-based. ")
    group_annotation.add_argument("--signature", dest = "signature", type = str, default = "human.immune.CIBERSORT",
        help = "Cell signature file used to annotate cell types. MAESTRO provides several sets of built-in cell signatures. "
        "Users can choose from ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']. "
        "Custom cell signatures are also supported. In this situation, users need to provide the file location of cell signatures, "
        "and the signature file is tab-seperated without header. The first column is cell type, and the second column is signature gene. "
        "DEFAULT: human.immune.CIBERSORT.")

    return


def scatac_config(args):
    """
    Generate scatac config.yaml file.
    """

    try:
        os.makedirs(args.directory)
    except OSError:
        # either directory exists (then we can ignore) or it will fail in the
        # next step.
        pass

    pkgpath = resource_filename('MAESTRO', 'Snakemake')
    template_file = os.path.join(pkgpath, "scATAC", "config_template.yaml")
    configfile = os.path.join(args.directory, "config.yaml")
    config_template = Template(open(template_file, "r").read(), trim_blocks=True, lstrip_blocks=True)
    if args.signature not in ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']:
        signature = os.path.abspath(args.signature)
    else:
        signature = args.signature

    if args.whitelist != "":
        whitelist = os.path.abspath(args.whitelist)
    else:
        whitelist = ""

    with open(configfile, "w") as configout:
        configout.write(config_template.render(
            #multi-sample parameters
            batch = args.batch,
            consensus_peaks = args.consensus_peaks,
            cutoff_samples = args.cutoff_samples,
            bulk_peaks = args.bulk_peaks,
            downsample = args.downsample,
            target_reads = args.target_reads,

            #input file arguments
            input_path = os.path.abspath(args.input_path),
            gzip = args.gzip,
            species = args.species,
            platform = args.platform,
            format = args.format,
            mapping = args.mapping,
            deduplication = args.deduplication,

            #Reference Genome Arguments
            giggleannotation = os.path.abspath(args.giggleannotation),
            fasta = os.path.abspath(args.fasta),
            index = os.path.abspath(args.index),

            #Barcode library arguments
            whitelist = whitelist,

            #Output arguments
            cores = args.cores,

            #Signature file arguments
            annotation = args.annotation,
            method = args.method,
            signature = signature,

            #Customized peak arguments
            custompeaks = args.custompeak,
            custompeaksloc = os.path.abspath(args.custompeak_file),
            shortpeaks = args.shortpeak,
            clusterpeaks = args.clusterpeak,

            #Gene Score Argument
            rpmodel = args.rpmodel,
            genedistance = args.genedistance,

            #Quality control cutoff
            peak = args.peak_cutoff,
            count = args.count_cutoff,
            frip = args.frip_cutoff,
            cell = args.cell_cutoff,))

    source = os.path.join(pkgpath, "scATAC", "Snakefile")
    rules = os.path.join(pkgpath, "scATAC", "rules")
    target = os.path.join(args.directory, "Snakefile")
    dest = os.path.join(args.directory, "rules")
    shutil.copy(source, target)
    shutil.copytree(rules, dest)

def scrna_config(args):
    """
    Generate scrna config.yaml file.
    """

    try:
        os.makedirs(args.directory)
    except OSError:
        # either directory exists (then we can ignore) or it will fail in the
        # next step.
        pass


    pkgpath = resource_filename('MAESTRO', 'Snakemake')
    template_file = os.path.join(pkgpath, "scRNA", "config_template.yaml")
    configfile = os.path.join(args.directory, "config.yaml")
    config_template = Template(open(template_file, "r").read(), trim_blocks=True, lstrip_blocks=True)
    if args.signature not in ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']:
        signature = os.path.abspath(args.signature)
    else:
        signature = args.signature

    if args.whitelist != "":
        whitelist = os.path.abspath(args.whitelist)
    else:
        whitelist = ""

    with open(configfile, "w") as configout:
        configout.write(config_template.render(
            #input_path = os.path.abspath(args.input_path),
            sample_file = args.sample_file,
            species = args.species,
            platform = args.platform,
            STARsolo_Features = args.STARsolo_Features,
            STARsolo_threads = args.STARsolo_threads,
            mergedname = args.mergedname,
            outprefix = args.outprefix,
            rseqc = args.rseqc,
            cores = args.cores,
            count = args.count_cutoff,
            gene = args.gene_cutoff,
            cell = args.cell_cutoff,
            signature = signature,
            lisadir = os.path.abspath(args.lisadir),
            mapindex = os.path.abspath(args.mapindex),
            rsem = os.path.abspath(args.rsem),
            whitelist = os.path.abspath(args.whitelist),
            barcodestart = args.barcode_start,
            barcodelength = args.barcode_length,
            umistart = args.umi_start,
            umilength = args.umi_length,
            trimr1 = args.trimR1,
            barcode = args.fastq_barcode,
            transcript = args.fastq_transcript))

    source = os.path.join(pkgpath, "scRNA", "Snakefile")
    rules = os.path.join(pkgpath, "scRNA", "rules")
    target = os.path.join(args.directory, "Snakefile")
    dest = os.path.join(args.directory, "rules")
    shutil.copy(source, target)
    shutil.copytree(rules, dest)

def integrate_config(args):
    """
    Generate integrate config.yaml file.
    """

    try:
        os.makedirs(args.directory)
    except OSError:
        # either directory exists (then we can ignore) or it will fail in the
        # next step.
        pass

    pkgpath = resource_filename('MAESTRO', 'Snakemake')
    template_file = os.path.join(pkgpath, "integrate", "config_template.yaml")
    configfile = os.path.join(args.directory, "config.yaml")
    config_template = Template(open(template_file, "r").read(), trim_blocks=True, lstrip_blocks=True)
    with open(configfile, "w") as configout:
        configout.write(config_template.render(
            rnaobject = os.path.abspath(args.rna_object),
            atacobject = os.path.abspath(args.atac_object),
            outprefix = args.outprefix))

    source = os.path.join(pkgpath, "integrate", "Snakefile")
    target = os.path.join(args.directory, "Snakefile")
    shutil.copy(source, target)

def multiome_config(args):
    """
    Generate multiome config.yaml file.
    """

    try:
        os.makedirs(args.directory)
    except OSError:
        # either directory exists (then we can ignore) or it will fail in the
        # next step.
        pass


    pkgpath = resource_filename('MAESTRO', 'Snakemake')
    template_file = os.path.join(pkgpath, "Multiome", "config_template.yaml")
    configfile = os.path.join(args.directory, "config.yaml")
    config_template = Template(open(template_file, "r").read(), trim_blocks=True, lstrip_blocks=True)
    if args.signature not in ['human.immune.CIBERSORT', 'mouse.brain.ALLEN', 'mouse.all.facs.TabulaMuris', 'mouse.all.droplet.TabulaMuris']:
        signature = os.path.abspath(args.signature)
    else:
        signature = args.signature

    if args.rna_whitelist != "":
        rna_whitelist = os.path.abspath(args.rna_whitelist)
    else:
        rna_whitelist = ""

    if args.atac_whitelist != "":
        atac_whitelist = os.path.abspath(args.atac_whitelist)
    else:
        atac_whitelist = ""

    with open(configfile, "w") as configout:
        configout.write(config_template.render(
            rna_fastqdir = os.path.abspath(args.rna_fastq_dir),
            #rna_fastqprefix = args.rna_fastq_prefix,
            atac_fastqdir = os.path.abspath(args.atac_fastq_dir),
            #atac_fastqprefix = args.atac_fastq_prefix,
            species = args.species,
            outprefix = args.outprefix,
            cores = args.cores,
            gzip = args.gzip,
            rna_count = args.rna_count_cutoff,
            rna_gene = args.rna_gene_cutoff,
            rna_cell = args.rna_cell_cutoff,
            lisadir = os.path.abspath(args.lisadir),
            giggleannotation = os.path.abspath(args.giggleannotation),
            rna_mapindex = os.path.abspath(args.rna_mapindex),
            atac_fasta = os.path.abspath(args.atac_fasta),
            atac_mapindex = os.path.abspath(args.atac_mapindex),
            mapping = args.mapping,
            rna_whitelist = rna_whitelist,
            atac_whitelist = atac_whitelist,
            rseqc = args.rseqc,
            atac_peak = args.atac_peak_cutoff,
            atac_count = args.atac_count_cutoff,
            atac_frip = args.atac_frip_cutoff,
            atac_cell = args.atac_cell_cutoff,
            annotation = args.annotation,
            method = args.method,
            signature = signature,
            custompeaks = args.custompeak,
            custompeaksloc = os.path.abspath(args.custompeak_file),
            shortpeaks = args.shortpeak,
            clusterpeaks = args.clusterpeak,
            rpmodel = args.rpmodel,
            genedistance = args.genedistance))

    source = os.path.join(pkgpath, "Multiome", "Snakefile")
    rules = os.path.join(pkgpath, "Multiome", "rules")
    target = os.path.join(args.directory, "Snakefile")
    dest = os.path.join(args.directory, "rules")
    shutil.copy(source, target)
    shutil.copytree(rules, dest)
