### for multiple scATACseq samples, some samples maybe much more deeply sequenced
### let's downsample every fragment file to a certain number, and call peaks
### using all fragment files by macs2 to get a peak set. Then go back to the original fragment
### file to get the counts in the peak set.

_downsample_threads = 4


rule scatac_downsample_batch:
    input:
        frag_dedup = "Result/Mapping/{sample}/fragments_corrected_dedup_count.tsv",
    output:
        frag_downsample = "Result/Mapping/{sample}/{sample}_fragment_corrected_downsample.tsv"
    threads:
        _downsample_threads
    message:
        "downsampling {input}"
    params:
        source_dir = os.path.dirname(os.path.dirname(srcdir("Snakefile")))
    log:
        "Result/Log/{sample}_downsample_batch.log"
    benchmark:
        "Result/Benchmark/{sample}_downsample_batch.benchmark"
    run:
        import re
        from subprocess import check_output
        total_reads = check_output("wc -l {frag_dedup}".format(frag_dedup = input.frag_dedup), shell = True).decode('utf8').strip().split()[0]
        total_reads = int(total_reads)
        if config.get("downsample"):
            target_reads = config['target_reads']
            if total_reads > target_reads:
                down_rate = target_reads/total_reads
            else:
                down_rate = 1
            shell("perl -ne 'print if (rand() <= {down_rate})' {infrag} \
                > {outfrag} 2> {log}".format(infrag = input.frag_dedup, down_rate = down_rate, outfrag = output.frag_downsample, log = log))
        else: #if set downsample to False, just make symbolic link for peak calling
            shell("ln -s {infrag} {outfrag}".format(infrag = params.source_dir + "/" + input.frag_dedup, outfrag = output.frag_downsample))



rule scatac_downsample_peak_call:
    input:
        frags = expand("Result/Mapping/{sample}/{sample}_fragment_corrected_downsample.tsv", sample = ALL_SAMPLES)
    output:
        peak = "Result/Analysis/Batch/all_samples_peaks.narrowPeak"
    params:
        name = "all_samples",
        genome = macs2_genome
    log:
        "Result/Log/scatac_batch_downsample_macs2_allpeak.log"
    benchmark:
        "Result/Benchmark/batch_downsample_AllPeakCall.benchmark"
    shell:
        "macs2 callpeak -f BEDPE -g {params.genome} --outdir Result/Analysis/Batch -n {params.name} -B -q 0.05 --nomodel --extsize=50 --keep-dup all -t {input.frags}"


rule scatac_countpeak_batch:
    input:
        finalpeak = "Result/Analysis/Batch/all_samples_peaks.narrowPeak",
        validbarcode = "Result/QC/{sample}/{sample}_scATAC_validcells.txt",
        frag = "Result/Mapping/{sample}/fragments_corrected_dedup_count.tsv"
    output:
        counts = "Result/Analysis/Batch/{sample}/{sample}_peak_count.h5"
    params:
        peakcount = temp("Result/Analysis/{sample}/{sample}_sorted_peakcount.tsv"),
        species = config["species"],
        outdir = "Result/Analysis/Batch/{sample}",
        outpre = "{sample}"
    threads:
        _countpeak_threads
    benchmark:
        "Result/Benchmark/{sample}_PeakCount_batch.benchmark"
    shell:
        """
        LC_ALL=C fgrep -f {input.validbarcode} -w {input.frag} | bedtools intersect -sorted -wa -wb -a {input.finalpeak} -b - | sort -k1,1 -k2,2 -k3,3 -k7,7 - | bedtools groupby -g 1,2,3,7 -c 7 -o count > {params.peakcount};
        MAESTRO scatac-peakcount --binary --filtered_count {params.peakcount} --species {params.species} --directory {params.outdir} --outprefix {params.outpre}
        """
