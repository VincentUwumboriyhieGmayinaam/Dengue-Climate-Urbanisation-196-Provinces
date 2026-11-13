# Out-of-sample skill, 2021-22 given zero weight in fitting (latent AR states carried forward). Compares the climate model with
# the same model without temperature and rainfall terms. Scores: CRPS of a Poisson predictive distribution at the predicted mean
# and MAE of log(cases + 1), by months ahead; province bootstrap for the overall skill interval.
suppressPackageStartupMessages({library(data.table)})
crps_pois <- function(y, mu) { mapply(function(y, m) { k <- 0:max(qpois(1 - 1e-9, m), y + 1); F <- ppois(k, m); sum((F - (k >= y))^2) }, y, mu) }
a <- readRDS("out/v2_hold_clim.rds")$hold; b <- readRDS("out/v2_hold_noclim.rds")$hold
H <- merge(a[, .(prov, tf, year, y, mu_clim = mu)], b[, .(prov, tf, mu_base = mu)], by = c("prov", "tf"))[!is.na(y)]
H[, ahead := as.integer(sub("^tf", "", as.character(tf))) - (2021 - 2009) * 12]      # 1 = Jan 2021
H[, `:=`(crps_clim = crps_pois(y, mu_clim), crps_base = crps_pois(y, mu_base),
         ae_clim = abs(log1p(y) - log1p(mu_clim)), ae_base = abs(log1p(y) - log1p(mu_base)))]
H[, window := cut(ahead, c(0, 3, 6, 12, 24), labels = c("1–3 months", "4–6 months", "7–12 months", "13–24 months"))]
S <- rbind(H[, .(window = "All 24 months", n = .N, CRPS_climate = mean(crps_clim), CRPS_baseline = mean(crps_base),
                 MAElog_climate = mean(ae_clim), MAElog_baseline = mean(ae_base))],
           H[, .(n = .N, CRPS_climate = mean(crps_clim), CRPS_baseline = mean(crps_base),
                 MAElog_climate = mean(ae_clim), MAElog_baseline = mean(ae_base)), by = window][order(window)])
S[, skill_CRPS_pct := 100 * (1 - CRPS_climate / CRPS_baseline)]; S[, skill_MAElog_pct := 100 * (1 - MAElog_climate / MAElog_baseline)]
# bootstrap by province for the skill score
set.seed(1); pv <- unique(H$prov)
bs <- replicate(500, { s <- sample(pv, replace = TRUE); h <- H[data.table(prov = s), on = "prov", allow.cartesian = TRUE]
  c(100 * (1 - mean(h$crps_clim) / mean(h$crps_base)), 100 * (1 - mean(h$ae_clim) / mean(h$ae_base))) })
S[1, `:=`(skill_CRPS_lo = quantile(bs[1, ], .025), skill_CRPS_hi = quantile(bs[1, ], .975),
          skill_MAElog_lo = quantile(bs[2, ], .025), skill_MAElog_hi = quantile(bs[2, ], .975))]
fwrite(S, "out/skill_holdout_2021_22.csv"); print(S, digits = 3)
# by country, and monthly country totals for plotting (supplementary)
Mx <- readRDS("out/p3_model_data.rds")$D; iso <- unique(Mx[, .(prov = shapeID, iso3)])
H <- merge(H, iso, by = "prov")
SC <- H[, .(n = .N, CRPS_climate = mean(crps_clim), CRPS_baseline = mean(crps_base), MAElog_climate = mean(ae_clim), MAElog_baseline = mean(ae_base)), by = iso3]
SC[, `:=`(skill_CRPS_pct = 100 * (1 - CRPS_climate / CRPS_baseline), skill_MAElog_pct = 100 * (1 - MAElog_climate / MAElog_baseline))]
fwrite(SC[order(iso3)], "out/skill_by_country.csv"); print(SC, digits = 3)
fwrite(H[, .(observed = sum(y), climate = sum(mu_clim), baseline = sum(mu_base)), by = .(iso3, ahead)][order(iso3, ahead)], "out/holdout_country_month.csv")
