
# ==========================================================================================
# Methylation calling:
# 

rule merge_united_methcalls_pe_se_destrandT:
     input:
         [DIR_methcall+"methylBase_per_chrom/"+chrom+"/methylBase_merged_cpg_dT_"+chrom+".txt.bgz" for chrom in CHROMS_CANON]
     output:
         DIR_methcall+"methylBase_per_chrom/methylBase_merged_cpg_dT.txt.bgz"
     params:
         cores=20,
         outfile = DIR_methcall+"methylBase_per_chrom/methylBase_merged_cpg_dT.txt"
     benchmark:
         outputdir+"benchmarks/sth.merge_united_methcalls_pe_se_destrandT.benchmark.txt"
     shell:
       """
       {tools}/Rscript {DIR_scripts}/Merge_united_methcalls.R "{input}" {params.outfile} {params.cores}
       """
       
rule merge_united_methcalls_pe_se_destrandF:
     input:
         [DIR_methcall+"methylBase_per_chrom/"+chrom+"/methylBase_merged_cpg_dF_"+chrom+".txt.bgz" for chrom in CHROMS_CANON]
     output:
         DIR_methcall+"methylBase_per_chrom/methylBase_merged_cpg_dF.txt.bgz"
     params:
         cores=20,
         outfile = DIR_methcall+"methylBase_per_chrom/methylBase_merged_cpg_dF.txt"
     benchmark:
         outputdir+"benchmarks/sth.merge_united_methcalls_pe_se_destrandF.benchmark.txt"
     shell:
       """
       {tools}/Rscript {DIR_scripts}/Merge_united_methcalls.R "{input}" {params.outfile} {params.cores}
       """

rule unite_meth_calls_perchr_pe_se:
     input:
         [DIR_methcall+sample+"/per_chrom/"+sample+"_{chrom}_merged_cpg_filtered.txt.bgz" for sample in SAMPLES]
     output:
         destrandTfile_perchromT = DIR_methcall+"methylBase_per_chrom/{chrom}/methylBase_merged_cpg_dT_{chrom}.RDS",
         destrandFfile_perchromF = DIR_methcall+"methylBase_per_chrom/{chrom}/methylBase_merged_cpg_dF_{chrom}.RDS",
         destrandTfile_perchrom_tbxT = DIR_methcall+"methylBase_per_chrom/{chrom}/methylBase_merged_cpg_dT_{chrom}.txt.bgz", # snakemake pretends that this file doesnt exist and removes it
         destrandFfile_perchrom_tbxF = DIR_methcall+"methylBase_per_chrom/{chrom}/methylBase_merged_cpg_dF_{chrom}.txt.bgz"
     params:
         inputdir = DIR_methcall,
         samples = SAMPLES,
         treatments = TREATMENT,
         assembly=ASSEMBLY,
         cores=24,
         savedb=True,
         adbdir = DIR_methcall+"methylBase_per_chrom/{chrom}/",
         suffixT = "merged_cpg_dT_{chrom}",
         suffixF = "merged_cpg_dF_{chrom}",
     log: DIR_methcall+"methylBase_per_chrom/meth_merged_unite_cpg.log"
     benchmark:
         outputdir+"benchmarks/sth.{chrom}_unite_meth_calls_perchr_pe_se.benchmark.txt"
     shell:
       """
         {tools}/Rscript {DIR_scripts}/Unite_meth.R \
                 --inputfiles="{input}" \
                 --destrandTfile={output.destrandTfile_perchromT} \
                 --destrandFfile={output.destrandFfile_perchromF} \
                 --inputdir={params.inputdir} \
                 --samples="{params.samples}" \
                 --treatments="{params.treatments}" \
                 --assembly="{params.assembly}" \
                 --cores={params.cores} \
                 --savedb={params.savedb} \
                 --logFile={log} \
                 --adbdir={params.adbdir} \
                 --suffixT={params.suffixT} \
                 --suffixF={params.suffixF}
         """

rule merge_filtered_methcall_pe_se:
     input:
       [DIR_methcall+"{sample}/per_chrom/{sample}_"+chrom+"_merged_cpg_filtered.txt.bgz" for chrom in CHROMS_CANON]
     output:
       tabixfile=DIR_methcall+"{sample}/{sample}_merged_cpg_filtered.txt.bgz"
     params:
       treatment = TREATMENT,
       sample = "{sample}",
       assembly = ASSEMBLY,
       cores = 4,
       rdsfile = DIR_methcall+"{sample}/{sample}_merged_cpg_filtered.RDS",
       tabixfile=DIR_methcall+"{sample}/{sample}_merged_cpg_filtered.txt"
     benchmark:
         outputdir+"benchmarks/{sample}.merge_filtered_methcall_pe_se.benchmark.txt"
     run:
        R("""
     
     inputfiles = "{input}"
     outtabix="{params.tabixfile}"
     outrds = "{params.rdsfile}"
     sample = "{params.sample}"
     assembly = "{params.assembly}"
     cores = "{params.cores}"
     
     inputs <- strsplit(inputfiles, " ", fixed = FALSE, perl = FALSE, useBytes = FALSE)[[1]]

     library(methylKit)
     
     ## Read data
     methylRawDB.list.obj_filtered = mclapply(1:length(inputs), function(i)
                 methRead(inputs[i],
                          sample,
                          assembly, 
                          dbtype='tabix'), 
                 mc.cores=cores)
     
     ## Join list of methylRaw objects per chromsoome 
     ## to one methylRaw object for a given sample
     list.meth.data = mclapply(methylRawDB.list.obj_filtered, 
                           function(x) getData(x), mc.cores=cores  )
     mydf = do.call("rbind", list.meth.data)
     
     new.methylRaw =  new("methylRaw", mydf, 
       sample.id = sample, 
       assembly = assembly,
       context="CpG",
       resolution="base") 
       
     ## Save   
     saveRDS(new.methylRaw, outrds)
     methylKit:::df2tabix(mydf, outtabix)

        """)  
       

rule filter_and_canon_chroms_perchr_pe_se:
     input:
         tabixfile     =  DIR_methcall+"{sample}/per_chrom/{sample}_{chrom}_merged_cpg.txt.bgz"
     output:
         outputfile    = DIR_methcall+"{sample}/per_chrom/{sample}_{chrom}_merged_cpg_filtered.txt.bgz"
     params:
         mincov      = MINCOV,
         save_folder = DIR_methcall+"{sample}/per_chrom/",
         sample_id = "{sample}_{chrom}_merged_cpg",
         canon_chrs_file = chromcanonicalfile,
         assembly    = ASSEMBLY,
         hi_perc=99.9,
         cores=10
     log:
         DIR_methcall+"{sample}/per_chrom/{sample}_{chrom}_merged.meth_calls_filter.log"
     message: ""
     benchmark:
         outputdir+"benchmarks/{sample}.{chrom}_filter_and_canon_chroms_perchr_pe_se.benchmark.txt"
     shell:
       """
         {tools}/Rscript {DIR_scripts}/Filter_meth.R \
                 --tabixfile={input.tabixfile} \
                 --mincov={params.mincov} \
                 --hi_perc={params.hi_perc} \
                 --save_folder={params.save_folder} \
                 --sample_id={params.sample_id} \
                 --assembly={params.assembly} \
                 --cores={params.cores} \
                 --canon_chrs_file={params.canon_chrs_file} \
                 --logFile={log}
         """

        
         
rule methCall_CpG_perchr_pe_se:
     input:
         bamfile = DIR_deduped_picard+"{sample}/per_chrom/{sample}_{chrom}_merged.dedup.sorted.bam"
     output:
         callFile = DIR_methcall+"{sample}/per_chrom/{sample}_{chrom}_merged_cpg.txt.bgz"
     params:
         assembly    = ASSEMBLY,
         mincov      = MINCOV,
         minqual     = MINQUAL,
         context     = "CpG",
         save_db      = True,
         save_folder = DIR_methcall+"{sample}/per_chrom/",
         sample_id = "{sample}_{chrom}_merged"
     log:
         DIR_methcall+"{sample}/per_chrom/{sample}_{chrom}_merged.meth_calls.log"
     message: "Extract methylation calls from bam file."
     benchmark:
         outputdir+"benchmarks/{sample}.{chrom}_methCall_CpG_perchr_pe_se.benchmark.txt"
     threads: 2
     shell:
       """
          {tools}/Rscript {DIR_scripts}/methCall.R \
                 --inBam={input.bamfile} \
                 --assembly={params.assembly} \
                 --mincov={params.mincov} \
                 --minqual={params.minqual} \
                 --context={params.context} \
                 --save_db={params.save_db}  \
                 --save_folder={params.save_folder}  \
                 --sample_id={params.sample_id} \
                 --logFile={log}
       """



