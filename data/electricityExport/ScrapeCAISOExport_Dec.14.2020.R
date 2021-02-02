#install.packages('xlsx') #make sure package is stalled!
library(xlsx)

#NOTES
#5 forecasts available for RE forecasts: 
#ACTUAL, DAM, HASP [hour ahead of RT mkt], RTD [5 min], AND RTDP [15 min]. 
#"ALL" market ID downloads all markets together
#Data is available on OASIS under System Demand. This generation is only for Elig Intermit Recs (EIR)
#Don't need input node; will automatically download for all zones.

#SET PARAMETERS
inputMarket <- 'RTM'
inputYear <- 2019
rootDir = "/Users/meiyewang/Desktop/code/data/electricity export"

#Set and create dir to write to
writeDir = file.path(rootDir,inputMarket)
dir.create(writeDir,showWarnings = TRUE)
writeDir = file.path(rootDir,inputMarket,inputYear)
dir.create(writeDir,showWarnings = TRUE)

# test <- getCAISOlmp(startdate=year+0101, enddate=year+0103, market_run_id=inputMarket, node=inputNode, writeDir=writeDir)

#Call function for each month
year <- inputYear*10000

# fetch CAISO LMP data from OASIS (see "Interface Specification for OASIS API")

getCAISOData <- function(startdate, enddate, market_run_id, writeDir){
  require(xlsx)
  options(timeout = 6000)
  #setInternet2(use = TRUE)
  
  #Set query name
  query <- "ENE_SLRS"
  
  #Save start and end dates
  start <- startdate
  end <- enddate
  
  # Initialize data frame with starting day
  activeDay <- start
  
  #define base URL
  baseURL <- "http://oasis.caiso.com/oasisapi/SingleZip?"
  
  #Set counter
  count <- 1
  #http://oasis.caiso.com/oasisapi/SingleZip?queryname=ENE_SLRS&market_run_id=RTM&tac_zone_name=ALL&schedule=ALL&startdatetime=20190919T07:00-0000&enddatetime=20190920T07:00-0000&version=1
  
  while(activeDay <= end){
    # assemble url for electricity import
    if ((activeDay == end) && (start%%10000 == 1201)) { #%% is mod division
      getURL <- paste(baseURL,"resultformat=6&queryname=",query,
                      "&market_run_id=",market_run_id,'&tac_zone_name=Caiso_Totals&schedule=Export',"&startdatetime=",activeDay,"T08:00-0000",
                      "&enddatetime=",start%/%10000+1,"0101T08:00-0000","&version=1",sep="")
      #Add 1 to month entry of start date so go to day 1 of next month!
    } else if (activeDay == end) {
      getURL <- paste(baseURL,"resultformat=6&queryname=",query,
                      "&market_run_id=",market_run_id,'&tac_zone_name=Caiso_Totals&schedule=Export',"&startdatetime=",activeDay,"T08:00-0000",
                      "&enddatetime=",startdate+100,"T08:00-0000","&version=1",sep="")
    } else {
      getURL <- paste(baseURL,"resultformat=6&queryname=",query,
                      "&market_run_id=",market_run_id,'&tac_zone_name=Caiso_Totals&schedule=Export',"&startdatetime=",activeDay,"T08:00-0000",
                      "&enddatetime=",activeDay+1,"T08:00-0000","&version=1",sep="")
    }
    
    temp <- tempfile() #create temp file
    
    # Download file and re-try if failure
    r <- NULL
    attempt <- 0
    while(is.null(r) && attempt <= 20) {
      attempt <- attempt + 1
      if (attempt > 1) {
        Sys.sleep(5)
      }
      try(
        #if successfully downloads, r becomes integer; data goes into 'temp'
        r <- download.file(getURL,temp,mode="wb",quiet=TRUE) 
      )
      if (attempt == 21) {
        stop()
      }
    } 
    print(paste("Downloaded",activeDay))
    print(getURL)
    
    #Read data from file
    tempdata <- read.table(unzip(temp), sep = ",", header=TRUE)
    unlink(temp) #deletes 'temp' file
    
    #Write raw data for single day
    write.csv(x=tempdata,file=file.path(writeDir,paste("EleImport",market_run_id,activeDay,".csv",sep="")))
    
    #Increment data and wait
    activeDay <- activeDay + 1
    count <- count + 1
    Sys.sleep(5)
  }
}

jan <- getCAISOData(startdate=year+0101, enddate=year+0131, market_run_id=inputMarket, writeDir=writeDir)
if (inputYear == 2004 || inputYear == 2008 || inputYear == 2012 || inputYear == 2016) { #leap years
  feb <- getCAISOData(startdate=year+0201, enddate=year+0229, market_run_id=inputMarket, writeDir=writeDir)
} else { #non-leap years
  feb <- getCAISOData(startdate=year+0201, enddate=year+0228, market_run_id=inputMarket, writeDir=writeDir)
}
mar <- getCAISOData(startdate=year+0301, enddate=year+0331, market_run_id=inputMarket, writeDir=writeDir)
apr <- getCAISOData(startdate=year+0401, enddate=year+0430, market_run_id=inputMarket, writeDir=writeDir)
may <- getCAISOData(startdate=year+0501, enddate=year+0531, market_run_id=inputMarket, writeDir=writeDir)
jun <- getCAISOData(startdate=year+0601, enddate=year+0630, market_run_id=inputMarket, writeDir=writeDir)
jul <- getCAISOData(startdate=year+0701, enddate=year+0731, market_run_id=inputMarket, writeDir=writeDir)
aug <- getCAISOData(startdate=year+0801, enddate=year+0831, market_run_id=inputMarket, writeDir=writeDir)
sep <- getCAISOData(startdate=year+0901, enddate=year+0930, market_run_id=inputMarket, writeDir=writeDir)
oct <- getCAISOData(startdate=year+1001, enddate=year+1031, market_run_id=inputMarket, writeDir=writeDir)
nov <- getCAISOData(startdate=year+1101, enddate=year+1130, market_run_id=inputMarket, writeDir=writeDir)
dec <- getCAISOData(startdate=year+1201, enddate=year+1231, market_run_id=inputMarket, writeDir=writeDir)
