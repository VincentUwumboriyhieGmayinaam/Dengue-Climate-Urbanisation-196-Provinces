# Export curves and summary rows from revised (v2) fits. Usage: Rscript 13_export_v2.R
# Writes: out/curves_cum_v2_<label>.csv, out/curves_lag_v2_<label>.csv (integer lags), out/table2_v2.csv,
#         out/fit_summary_v2.csv (AIC, rho, sigma, n), out/anomaly_lag_by_country.csv
suppressPackageStartupMessages({library(data.table); library(dlnm); library(glmmTMB)})
M <- readRDS("out/p3_model_data.rds")
lab <- sub("^v2_(.*)\\.rds$", "\\1", list.files("out", "^v2_.*\\.rds$"))
lab <- setdiff(lab, c("hold_noclim"))
cum <- function(cp, ex) data.table(exposure = ex, value = as.numeric(names(cp$allRRfit)), RR = cp$allRRfit, lo = cp$allRRlow, hi = cp$allRRhigh)
near <- function(cp, x) names(cp$allRRfit)[which.min(abs(as.numeric(names(cp$allRRfit)) - x))]
lagc <- function(cp, ex, x, tag) { v <- near(cp, x); i <- seq_len(ncol(cp$matRRfit))
  data.table(exposure = ex, point = tag, value = as.numeric(v), lag = as.numeric(sub("lag", "", colnames(cp$matRRfit)[i])),
             RR = cp$matRRfit[v, i], lo = cp$matRRlow[v, i], hi = cp$matRRhigh[v, i]) }
fm <- function(cp, x) { v <- near(cp, x); sprintf("%.2f (%.2f–%.2f)", cp$allRRfit[v], cp$allRRlow[v], cp$allRRhigh[v]) }
S <- list(); T2 <- list(); AL <- list()
for (l in lab) {
  r <- readRDS(sprintf("out/v2_%s.rds", l)); m <- r$m
  vc <- VarCorr(m)$cond; ar <- vc[[grep("^prov", names(vc))[length(grep("^prov", names(vc)))]]]
  S[[l]] <- data.table(label = l, n = if (!is.null(m$frame$`(weights)`)) sum(m$frame$`(weights)` > 0) else nrow(m$frame), AIC = AIC(m), pdHess = m$sdr$pdHess, conv = m$fit$convergence == 0,
                       rho = attr(ar, "correlation")[1, 2], sigma_ar = attr(ar, "stddev")[1],
                       sd_prov = attr(vc$prov, "stddev")[1])
  if (is.null(r$cpT)) next
  anom <- grepl("^an", l) || l == "anomaly"
  kt <- if (!is.null(r$knots)) r$knots$t else M$kt; kr <- if (!is.null(r$knots)) r$knots$r else M$kr
  rt <- if (!is.null(r$ref)) r$ref["t"] else M$ref_t; rr <- if (!is.null(r$ref)) r$ref["r"] else M$ref_r
  fwrite(rbind(cum(r$cpT, "temperature"), cum(r$cpR, "rainfall")), sprintf("out/curves_cum_v2_%s.csv", l))
  if (anom) {
    fwrite(rbind(lagc(r$cpT, "temperature", 1, "+1"), lagc(r$cpT, "temperature", -1, "-1"),
                 lagc(r$cpR, "rainfall", 100, "+100"), lagc(r$cpR, "rainfall", -50, "-50")), sprintf("out/curves_lag_v2_%s.csv", l))
    AL[[l]] <- data.table(label = l, cum_plus1 = fm(r$cpT, 1), cum_plus2 = fm(r$cpT, 2), cum_minus1 = fm(r$cpT, -1),
                          rain_plus100 = fm(r$cpR, 100), rain_minus50 = fm(r$cpR, -50))
  } else {
    fwrite(rbind(lagc(r$cpT, "temperature", kt[3], "P90"), lagc(r$cpT, "temperature", kt[1], "P10"),
                 lagc(r$cpR, "rainfall", kr[3], "P90"), lagc(r$cpR, "rainfall", kr[1], "P10")), sprintf("out/curves_lag_v2_%s.csv", l))
    T2[[l]] <- data.table(label = l, temp_ref = round(rt, 1), temp_P10 = round(kt[1], 1), temp_P90 = round(kt[3], 1),
                          RR_T10 = fm(r$cpT, kt[1]), RR_T90 = fm(r$cpT, kt[3]),
                          rain_ref = rr, rain_P10 = kr[1], rain_P90 = kr[3], RR_R10 = fm(r$cpR, kr[1]), RR_R90 = fm(r$cpR, kr[3]))
  }
}
S <- rbindlist(S); fwrite(S, "out/fit_summary_v2.csv"); print(S, digits = 4)
T2 <- merge(rbindlist(T2), S[, .(label, n, AIC, rho)], by = "label"); fwrite(T2, "out/table2_v2.csv"); print(T2)
if (length(AL)) { AL <- rbindlist(AL); fwrite(AL, "out/anomaly_by_fit.csv"); print(AL) }
