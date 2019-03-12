library(plyr)

pass_versus_fail <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  significant <- data[which(data$NEL > 0 & data$NWL > 0),]
  count(significant, "test_status")
}

state_start_and_command_counting <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  significant <- data[which(data$test_status=='FAIL'),]
  if (length(significant) > 0) {
    count(significant, c("Ss", "CMD"))
  }
}

http_200_with_fail <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  count(data, c("http_code", "test_status"))
}