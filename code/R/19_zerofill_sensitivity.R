# Sensitivity analysis: missing Colombian and Peruvian province-months treated as zero reported cases.
# OpenDengue files for Colombia and Peru contain no zero-case records, while their national weekly series is complete, so a
# missing department-month there most likely means zero reported cases. The zero-filled data (made by code/R/19a_make_zerofill_data.py)
# are run through 01_prepare.R, 17_bym2_matrix.R and 09_fit_v2.R (primary, anomaly, urban) in the folder given as argument
# (209 provinces eligible). This script evaluates those fits at the primary model's pooled values so that rows are comparable.
suppressPackageStartupMessages({library(data.table); library(dlnm); library(glmmTMB)})
d <- commandArgs(TRUE)[1]; if (is.na(d)) d <- "zerofill"
M0 <- readRDS("out/p3_model_data.rds")                      # primary data: pooled reference values
Z <- readRDS(file.path(d, "out/p3_model_data.rds"))
rt <- round(M0$ref_t, 1); rr <- round(M0$ref_r); kt <- round(M0$kt[c(1, 3)], 1); kr <- round(M0$kr[c(1, 3)])
f <- function(cp, x) sprintf("%.2f (%.2f–%.2f)", cp$allRRfit[as.character(x)], cp$allRRlow[as.character(x)], cp$allRRhigh[as.character(x)])
cpx <- function(m, cb, pre, cen, at) { b <- fixef(m)$cond; V <- vcov(m)$cond; i <- grep(paste0("^", pre, "cb"), names(b))
  crosspred(cb, coef = b[i], vcov = V[i, i], model.link = "log", cen = cen, at = at, cumul = TRUE) }
p <- readRDS(file.path(d, "out/v2_primary.rds")); m <- p$m
cT <- cpx(m, Z$cb_t, "cbT", rt, kt); cR <- cpx(m, Z$cb_r, "cbR", rr, kr)
a <- readRDS(file.path(d, "out/v2_anomaly.rds"))
u <- readRDS(file.path(d, "out/v2_urban.rds")); bu <- fixef(u$m)$cond; Vu <- vcov(u$m)$cond
lb <- log(Z$D$built_fraction); q <- quantile(lb, c(.25, .75), na.rm = TRUE); du <- diff((q - mean(lb, na.rm = TRUE)) / sd(lb, na.rm = TRUE))
i1 <- grep("^cbRu", names(bu)); cu <- crosspred(Z$cb_r, coef = bu[i1], vcov = Vu[i1, i1], model.link = "log", cen = rr, at = kr[2], cumul = TRUE)
ur <- sprintf("%.2f (%.2f–%.2f)", exp(cu$allfit * du), exp((cu$allfit - 1.96 * cu$allse) * du), exp((cu$allfit + 1.96 * cu$allse) * du))
out <- data.table(label = "zerofill", n = sum(!is.na(Z$D$dengue_cases)), provinces = uniqueN(Z$D$shapeID), AIC = AIC(m),
                  temp_ref = rt, temp_P10 = kt[1], temp_P90 = kt[2], RR_T10 = f(cT, kt[1]), RR_T90 = f(cT, kt[2]),
                  rain_ref = rr, rain_P10 = kr[1], rain_P90 = kr[2], RR_R10 = f(cR, kr[1]), RR_R90 = f(cR, kr[2]),
                  anomaly_plus1 = f(a$cpT, 1), urban_wet_ratio = ur, pdHess = m$sdr$pdHess)
fwrite(out, "out/zerofill_sensitivity.csv"); print(out)
