# Merge GHSL province epochs (2010, 2015, 2020; from P3_ghsl_zonal_run_on_PC.R) into the province-month file.
# Population: log-linear interpolation between epochs; 2021–22 extrapolated with each province's 2015–20 log-linear trend.
# Built-up fraction: linear interpolation; 2021–22 extrapolated with the 2015–20 linear trend (bounded to [0, 1]).
# Tertiles of the 2015 built-up fraction are defined within each country.
suppressPackageStartupMessages(library(data.table))
G <- fread(commandArgs(TRUE)[1]); stopifnot(all(c(2010, 2015, 2020) %in% G$epoch))
yrs <- 2009:2022
Y <- G[, { lp <- approx(epoch, log(pmax(pop, 1)), xout = yrs, rule = 2)$y
           b <- approx(epoch, built_fraction, xout = yrs, rule = 2)$y
           s_lp <- (log(pmax(pop[epoch == 2020], 1)) - log(pmax(pop[epoch == 2015], 1))) / 5
           s_b <- (built_fraction[epoch == 2020] - built_fraction[epoch == 2015]) / 5
           lp[yrs > 2020] <- log(pmax(pop[epoch == 2020], 1)) + s_lp * (yrs[yrs > 2020] - 2020)
           b[yrs > 2020] <- pmin(pmax(built_fraction[epoch == 2020] + s_b * (yrs[yrs > 2020] - 2020), 0), 1)
           b[yrs < 2010] <- built_fraction[epoch == 2010]
           .(year = yrs, population = exp(lp), built_fraction = b) }, by = .(iso3, shapeID)]
T15 <- G[epoch == 2015, .(shapeID, iso3, b15 = built_fraction)]
T15[, urban_tertile_within_country := as.integer(cut(rank(b15, ties.method = "first"), 3, labels = FALSE)), by = iso3]
Y <- merge(Y, T15[, .(shapeID, urban_tertile_within_country)], by = "shapeID")
C <- fread("data/P3_dengue_admin1_month_climate.csv")
X <- merge(C, Y[, .(shapeID, year, population, built_fraction, urban_tertile_within_country)], by = c("shapeID", "year"), all.x = TRUE)
fwrite(X, "data/P3_dengue_admin1_month_climate_pop_urban.csv")
an <- X[year %between% c(2010, 2022)]
cat("rows", nrow(X), "; missing population in 2010–22:", an[is.na(population), uniqueN(shapeID)], "provinces\n")
print(an[year == 2015 & month == 1, .(pop_millions = round(sum(population, na.rm = TRUE) / 1e6, 1),
                                       built_pct_median = round(100 * median(built_fraction, na.rm = TRUE), 2)), by = iso3])
