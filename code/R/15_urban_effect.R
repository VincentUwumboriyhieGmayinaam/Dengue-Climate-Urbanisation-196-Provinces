# Effect modification by built-up fraction (continuous, standardised). Primary estimand: ratio of cumulative RRs
# (lags 0–6) between the 75th and 25th percentiles of built-up fraction, at the 10th and 90th percentiles of temperature
# and rainfall, against the pooled median. Also writes curves at P25 and P75 of built-up fraction, restricted to the
# exposure range shared by provinces below the 25th and above the 75th percentile.
suppressPackageStartupMessages({library(data.table); library(dlnm); library(glmmTMB)})
f <- commandArgs(TRUE)[1]; if (is.na(f)) f <- "out/v2_urban.rds"
r <- readRDS(f); m <- r$m; M <- readRDS("out/p3_model_data.rds"); D <- M$D
b <- fixef(m)$cond; V <- vcov(m)$cond
RAW <- grepl("raw", f); bf <- if (RAW) D$built_fraction else log(D$built_fraction); mu_b <- mean(bf, na.rm = TRUE); sd_b <- sd(bf, na.rm = TRUE)
q <- quantile(bf, c(.25, .75), na.rm = TRUE); u <- (q - mu_b) / sd_b
res <- list(); cur <- list()
for (ex in c("T", "R")) {
  cb <- if (ex == "T") M$cb_t else M$cb_r; ref <- if (ex == "T") M$ref_t else M$ref_r; k <- if (ex == "T") M$kt else M$kr
  col <- if (ex == "T") "power_tmean_c" else "power_precip_mm"
  i0 <- grep(paste0("^cb", ex, "cb"), names(b)); i1 <- grep(paste0("^cb", ex, "u"), names(b)); stopifnot(length(i0) == length(i1))
  lo_sh <- max(quantile(D[[col]][bf <= q[1]], .05, na.rm = TRUE), quantile(D[[col]][bf >= q[2]], .05, na.rm = TRUE))
  hi_sh <- min(quantile(D[[col]][bf <= q[1]], .95, na.rm = TRUE), quantile(D[[col]][bf >= q[2]], .95, na.rm = TRUE))
  at <- sort(unique(round(c(seq(lo_sh, hi_sh, length.out = 80), k[c(1, 3)]), if (ex == "T") 1 else 0)))
  for (j in 1:2) {
    cf <- b[i0] + u[j] * b[i1]; vv <- V[i0, i0] + u[j]^2 * V[i1, i1] + u[j] * (V[i0, i1] + V[i1, i0])
    cp <- crosspred(cb, coef = cf, vcov = vv, model.link = "log", cen = ref, at = at, cumul = TRUE)
    cur[[paste(ex, j)]] <- data.table(exposure = ex, built = c("P25", "P75")[j], value = cp$predvar, RR = cp$allRRfit, lo = cp$allRRlow, hi = cp$allRRhigh)
  }
  # ratio P75 / P25 = exp((u75 - u25) * B(x) gamma), B centred at ref
  du <- u[2] - u[1]; cp1 <- crosspred(cb, coef = b[i1], vcov = V[i1, i1], model.link = "log", cen = ref, at = round(k[c(1, 3)], if (ex == "T") 1 else 0), cumul = TRUE)
  lr <- cp1$allfit * du; se <- cp1$allse * abs(du)
  res[[ex]] <- data.table(exposure = ex, point = c("P10", "P90"), value = cp1$predvar, ratio = exp(lr), lo = exp(lr - 1.96 * se), hi = exp(lr + 1.96 * se),
                          shared_range = sprintf("%.1f–%.1f", lo_sh, hi_sh), within_shared = cp1$predvar >= lo_sh & cp1$predvar <= hi_sh)
}
R <- rbindlist(res); print(R, digits = 3); tg <- sub("^v2_", "", sub("\\.rds$", "", basename(f))); fwrite(R, sprintf("out/urban_ratio_P75_P25_%s.csv", tg)); fwrite(rbindlist(cur), sprintf("out/urban_curves_%s.csv", tg))
cat("built-up fraction P25/P75 (%):", round(100 * (if (RAW) q else exp(q)), 3), "%; AIC with interaction", round(AIC(m)), "\n")
