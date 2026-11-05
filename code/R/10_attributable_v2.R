# RQ4 (revised after review): cases attributable to temperature and rainfall departing from each province's
# climatological expectation for that calendar month. Reference = mean over 2010–20 of the cross-basis contribution
# for the same province and calendar month (i.e. the average of f over the climatological distribution, not f of the
# mean). Weighted by FITTED cases; positive (excess) and negative (deficit) components reported separately.
# Intervals: 1000 draws of cross-basis coefficients (does not reflect model-specification or spatial clustering uncertainty).
suppressPackageStartupMessages({library(data.table); library(MASS); library(glmmTMB)})
M <- readRDS("out/p3_model_data.rds"); r <- readRDS(Sys.getenv("P3_FIT", "out/v2_primary.rds")); m <- r$m
b <- fixef(m)$cond; V <- vcov(m)$cond
iT <- grep("^cbT[^u]", names(b)); iR <- grep("^cbR[^u]", names(b))
D <- M$D[r$keep]; XT <- unclass(M$cb_t)[r$keep, ]; XR <- unclass(M$cb_r)[r$keep, ]
mu <- fitted(m); stopifnot(length(mu) == nrow(D)); ok <- !is.na(D$dengue_cases) & !is.na(mu); D <- D[ok]; XT <- XT[ok, ]; XR <- XR[ok, ]; mu <- mu[ok]
stopifnot(length(mu) == nrow(D))
grp <- paste(D$shapeID, D$month); base <- D$year %between% c(2010, 2020)
dev <- function(X, cf) { e <- as.vector(X %*% cf); ref <- ave(ifelse(base, e, NA), grp, FUN = function(v) mean(v, na.rm = TRUE)); e - ref }
an <- function(cT, cR) { dT <- dev(XT, cT); dR <- dev(XR, cR)
  data.table(iso3 = D$iso3, period = ifelse(D$year <= 2016, "2010–16", "2017–22"), mu = mu,
             aT = mu * (1 - exp(-dT)), aR = mu * (1 - exp(-dR)), dT = dT, dR = dR) }
agg <- function(x) {
  f <- function(z) z[, .(fitted = sum(mu), T_net = sum(aT), T_pos = sum(aT[dT > 0]), T_neg = sum(aT[dT < 0]),
                         R_net = sum(aR), R_pos = sum(aR[dR > 0]), R_neg = sum(aR[dR < 0]))]
  rbind(cbind(x[, f(.SD), by = .(iso3, period)]), cbind(iso3 = "All", x[, f(.SD), by = period]),
        cbind(iso3 = "All", period = "2010–22", f(x)), cbind(period = "2010–22", x[, f(.SD), by = iso3]), fill = TRUE) }
est <- agg(an(b[iT], b[iR]))
set.seed(2026); S <- mvrnorm(1000, b[c(iT, iR)], V[c(iT, iR), c(iT, iR)])
sims <- rbindlist(lapply(1:1000, function(s) agg(an(S[s, seq_along(iT)], S[s, length(iT) + seq_along(iR)]))[, sim := s]))
vars <- c("T_net", "T_pos", "T_neg", "R_net", "R_pos", "R_neg")
ci <- sims[, c(lapply(.SD, quantile, .025), lapply(.SD, quantile, .975)), by = .(iso3, period), .SDcols = vars]
setnames(ci, 3:14, c(paste0(vars, "_lo"), paste0(vars, "_hi")))
out <- merge(est, ci, by = c("iso3", "period"))
for (v in vars) for (s in c("", "_lo", "_hi")) out[[paste0("pct_", v, s)]] <- 100 * out[[paste0(v, s)]] / out$fitted
fwrite(out, sub("\\.rds$", "_attributable.csv", Sys.getenv("P3_FIT", "out/v2_primary.rds")))
p <- function(v) sprintf("%.1f (%.1f to %.1f)", out[[paste0("pct_", v)]], out[[paste0("pct_", v, "_lo")]], out[[paste0("pct_", v, "_hi")]])
print(data.table(iso3 = out$iso3, period = out$period, T_pos = p("T_pos"), T_neg = p("T_neg"), T_net = p("T_net"), R_pos = p("R_pos"), R_neg = p("R_neg"), R_net = p("R_net")))
# mean temperature departure by period (to check the claim that warming drove changes)
print(D[, .(mean_temp_departure = mean(power_tmean_c - ave(ifelse(base, power_tmean_c, NA), grp, FUN = function(v) mean(v, na.rm = TRUE)))), by = .(period = ifelse(year <= 2016, "2010–16", "2017–22"))])
