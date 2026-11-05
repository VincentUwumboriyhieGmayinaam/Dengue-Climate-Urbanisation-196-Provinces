# Secondary RQ3 measure: cumulative RR by within-country tertile of built-up fraction, and the ratio tertile 3 / tertile 1,
# at the pooled 10th and 90th percentiles of temperature and rainfall (centred on the pooled medians).
suppressPackageStartupMessages({library(data.table); library(dlnm); library(glmmTMB)})
r <- readRDS("out/v2_urbtert.rds"); m <- r$m; M <- readRDS("out/p3_model_data.rds")
b <- fixef(m)$cond; V <- vcov(m)$cond; out <- list()
for (ex in c("T", "R")) {
  cb <- if (ex == "T") M$cb_t else M$cb_r; ref <- if (ex == "T") M$ref_t else M$ref_r
  at <- round((if (ex == "T") M$kt else M$kr)[c(1, 3)], if (ex == "T") 1 else 0)
  i1 <- grep(paste0("^cb", ex, "cb"), names(b))
  for (tt in 1:3) {
    i <- if (tt == 1) i1 else grep(paste0("^cb", ex, "t", tt, "cb"), names(b))
    if (tt == 1) { cf <- b[i1]; vv <- V[i1, i1] } else { cf <- b[i1] + b[i]; vv <- V[i1, i1] + V[i, i] + V[i1, i] + V[i, i1] }
    cp <- crosspred(cb, coef = cf, vcov = vv, model.link = "log", cen = ref, at = at, cumul = TRUE)
    out[[paste(ex, tt)]] <- data.table(exposure = ex, tertile = tt, value = at, RR = cp$allRRfit, lo = cp$allRRlow, hi = cp$allRRhigh)
    if (tt == 3) { cr <- crosspred(cb, coef = b[i], vcov = V[i, i], model.link = "log", cen = ref, at = at, cumul = TRUE)
      out[[paste(ex, "ratio")]] <- data.table(exposure = ex, tertile = "3 vs 1", value = at, RR = cr$allRRfit, lo = cr$allRRlow, hi = cr$allRRhigh) }
  }
}
O <- rbindlist(out); print(O, digits = 3); fwrite(O, "out/urban_tertiles.csv")
