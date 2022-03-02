
if config["whitelist"]:
    rule scatac_barcodecorrect:
        input:
            r2 = "Result/Tmp/{sample}/{sample}_R2.fastq",
            whitelist = config["whitelist"]
        output:
            bc_correct = "Result/Mapping/{sample}/barcode_correct.txt",
            bc_correct_uniq = "Result/Mapping/{sample}/barcode_correct_uniq.txt"
        params:
            outdir = "Result/Mapping/{sample}"
        benchmark:
            "Result/Benchmark/{sample}_BarcodeCorrect.benchmark"
        shell:
            "python " + SCRIPT_PATH + "/scATAC_10x_BarcodeCorrect.py -b {input.r2} -B {input.whitelist} -O {params.outdir};"
            "sort -k1,1 -k3,3 {output.bc_correct} | uniq > {output.bc_correct_uniq}"


else:
    rule scatac_barcodecorrect:
        input:
            r2 = "Result/Tmp/{sample}/{sample}_R2.fastq",
        output:
            bc_correct = "Result/Mapping/{sample}/barcode_correct.txt",
            bc_correct_uniq = "Result/Mapping/{sample}/barcode_correct_uniq.txt"
        params:
            outdir = "Result/Mapping/{sample}"
        benchmark:
            "Result/Benchmark/{sample}_BarcodeCorrect.benchmark"
        shell:
            "python " + SCRIPT_PATH + "/scATAC_10x_BarcodeCorrect.py -b {input.r2} -O {params.outdir};"
            "sort -k1,1 -k3,3 {output.bc_correct} | uniq > {output.bc_correct_uniq}"


rule scatac_fragmentcorrect:
    input:
        fragments = "Result/Mapping/{sample}/fragments.tsv",
        bc_correct = "Result/Mapping/{sample}/barcode_correct.txt"
    output:
        frag_count = "Result/Mapping/{sample}/fragments_corrected_count.tsv",
        frag_sort = temp("Result/Mapping/{sample}/fragments_corrected_sorted.tsv")
    params:
        outdir = "Result/Mapping/{sample}",
        frag_correct = "Result/Mapping/{sample}/fragments_corrected.tsv",
    benchmark:
        "Result/Benchmark/{sample}_FragCorrect.benchmark"
    shell:
        "python " + SCRIPT_PATH + "/scATAC_FragmentCorrect.py -F {input.fragments} -C {input.bc_correct} -O {params.outdir};"
        "sort -k1,1 -k2,2 -k3,3 -k4,4 -V {params.frag_correct} > {output.frag_sort};"
        "bedtools groupby -i {output.frag_sort} -g 1,2,3,4 -c 4 -o count | sort -k1,1 -k2,2n > {output.frag_count};"
        "rm {params.frag_correct}"
