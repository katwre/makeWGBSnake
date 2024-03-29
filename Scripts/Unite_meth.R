# PiGx BSseq Pipeline.
#
# Copyright © 2018 Alexander Gosdschan <alexander.gosdschan@mdc-berlin.de>,
# Katarzyna Wreczycka katarzyna.wreczycka@mdc-berlin.de
#
# This file is part of the PiGx BSseq Pipeline.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Collect arguments
args <- commandArgs(TRUE)

## Default setting when no arguments passed
if(length(args) < 1) {
  args <- c("--help")
}

## Help section
if("--help" %in% args) {
  cat("
      Render to report
      
      Arguments:
      --inBam location of input bam file
      --assembly assembly used to map the reads
      --mincov minimum coverage (default: 10)
      --minqual minimum base quality (default: 20)
      --rds name of the RDS output file
      --logFile file to print the logs to
      --help              - print this text
      
      Example:
      ./test.R --arg1=1 --arg2='output.txt' --arg3=TRUE \n\n")
  
  q(save="no")
}

## Parse arguments (we expect the form --arg=value)
parseArgs <- function(x) strsplit(sub("^--", "", x), "=")

argsDF <- as.data.frame(do.call("rbind", parseArgs(args)))
argsL <- as.list(as.character(argsDF$V2))

names(argsL) <- argsDF$V1
# saveRDS(argsL, "~/argsL.RDS") ##############################################################
#argsL=readRDS("~/argsL.RDS")

# ## catch output and messages into log file
out <- file(argsL$logFile, open = "wt")
sink(out,type = "output")
sink(out, type = "message")


library(methylKit)

## Load variables
inputs    <- strsplit(argsL$inputfiles, " ", fixed = FALSE, perl = FALSE, useBytes = FALSE)[[1]]
destrandTfile <- argsL$destrandTfile
destrandFfile <- argsL$destrandFfile
inputdir <- argsL$inputdir
samples <- strsplit(argsL$samples, " ", fixed = FALSE, perl = FALSE, useBytes = FALSE)[[1]]
treatments <- as.numeric( strsplit(argsL$treatments, " ", fixed = FALSE, perl = FALSE, useBytes = FALSE)[[1]] )
cores <- as.numeric(argsL$cores)
assembly = argsL$assembly
save.db = argsL$savedb
suffixT= argsL$suffixT
suffixF= argsL$suffixF
dbdir= argsL$dbdir

# dir.create(dbdir)
# destrandTfile='/fast/work/projects/peifer_wgs/work/2017-12-19_WGBS/Project/Results/cardiac/06_methyl_calls_bwameth/methylBase/methylBase_CpG_dT.RDS'
# destrandFfile='/fast/work/projects/peifer_wgs/work/2017-12-19_WGBS/Project/Results/cardiac/06_methyl_calls_bwameth/methylBase/methylBase_CpG_dF.RDS'
# inputdir='/fast/work/projects/peifer_wgs/work/2017-12-19_WGBS/Project/Results/cardiac/06_methyl_calls_bwameth/'
# dbdir="~/scratch/"

# SAMPLES = 
# c(
#  'AC10',
#  'AC2',
#  'AC3',
#  'AC4',
#  'AC5',
#  'AC6',
#  'AC7',
#  'AC8',
#  'AC9',
#  'N1',
#  'N2',
#  'N3',
#  'N4',
#  'N5',
#  'N6'
# )

DIR_methcall="/fast/work/projects/peifer_wgs/work/2017-12-19_WGBS/Project/Results/cardiac/06_methyl_calls_bwameth/"

inputs= sapply(SAMPLES, function(sample) paste0(DIR_methcall,sample,"/tabix_CpG/",sample,"_CpG_filtered.txt.bgz"))

library(methylKit)

## Read data
methylRawDB.list.obj_filtered = mclapply(1:length(inputs), function(i)
                 methRead(inputs[i], 
                          samples[i] , 
                          assembly, 
                          dbtype='tabix'), 
                 mc.cores=cores)
methylRawListDB.obj_filtered <- as(methylRawDB.list.obj_filtered, "methylRawListDB")
#methylRawListDB.obj_filtered@treatment = treatments
methylRawListDB.obj_filtered@treatment = 1:length(treatments)


# check if sorted



## Unite
if( length(methylRawListDB.obj_filtered)>1 ){
  # destranded=TRUE
  meth.deT=unite(methylRawListDB.obj_filtered, 
                 destrand=TRUE, 
                 save.db = save.db,
                 suffix = suffixT,
                 dbdir=dbdir)

# Error in value[[3L]](cond) :
#   internal: samtools invoked 'exit(1)'; see warnings() and restart R
#   file: /fast/work/projects/peifer_wgs/work/2017-12-19_WGBS/Project/Results/cardiac/06_methyl_calls_bwameth/AC10/tabix_CpG/AC10_CpG_filtered_destrand.txt.bgz
# In addition: Warning message:
# In doTryCatch(return(expr), name, parentenv, handler) :
#   [ti_index_core] the file out of order at line 1518394


  # its faster to save methylBaseDB object into RDS and then to read it
  # than save it again as a list of tabix files.
  saveRDS(meth.deT, destrandTfile)
  
  # destranded=FALSE
  meth.deF=unite(methylRawListDB.obj_filtered, 
                 destrand=FALSE, 
                 save.db = save.db,
                 suffix = suffixF,
                 dbdir=dbdir)
  saveRDS(meth.deF, destrandFfile)
}else{ # is there is only 1 sample
  

  #treatments = 0 # there is only 1 treatment
  methylRawDB.2.methylBase = function(object, 
                                      sample.ids="sampleid",
                                      treatments=0, 
                                      destranded=TRUE,
                                      resolution="base"){
    
    new("methylBase",getData(object),
        sample.ids=sample.ids,
        assembly=object@assembly,
        context=object@context,
        treatment=treatments,
        coverage.index=5,
        numCs.index=6,
        numTs.index=7,
        destranded=destranded,
        resolution=resolution
    )
  }
  # destranded=TRUE
  object = methylRawListDB.obj_filtered[[1]]
  meth.deT = methylRawDB.2.methylBase(object, 
                                      sample.ids=samples, 
                                      treatments=treatments, 
                                      destranded=TRUE)
  
  # save as RDS
  saveRDS(meth.deT, destrandTfile)
  
  # save as tabix
  my.make.tabix = function(obj, dbpath, suffix){
    
    meth.de.data = obj@.Data
    meth.de.data[[1]] = as.character(meth.de.data[[1]]) # chromosome
    mydf = as.data.frame(do.call("cbind",meth.de.data))
    colnames(mydf) = obj@names
    meth.deDB = methylKit:::makeMethylBaseDB(mydf,
                                              dbpath=dbpath,
                                              dbtype="tabix",
                                              obj@sample.ids, obj@assembly ,obj@context,
                                              obj@resolution,obj@treatment,obj@coverage.index,
                                              obj@numCs.index,obj@numTs.index,obj@destranded,
                                              suffix=suffix)
    return(meth.deDB)
  }
  
  meth.deTDB = my.make.tabix(meth.deT, dbdir, suffixT)
  
  
  # destranded=FALSE
  meth.deF = methylRawDB.2.methylBase(object, 
                                      sample.ids=samples, 
                                      treatments=treatments, 
                                      destranded=FALSE)
  # save as RDS
  saveRDS(meth.deF, destrandFfile)
  
  # save as tabix file
  meth.deFDB = my.make.tabix(meth.deF, dbdir, suffixF)
  
}




