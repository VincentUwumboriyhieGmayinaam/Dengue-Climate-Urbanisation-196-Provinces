# Paper 3 – step 1: analytic data set, cross-bases and adjacency graph
# Runs without INLA. Output: out/p3_model_data.rds (data, cross-bases, graph, settings)
suppressPackageStartupMessages({library(data.table); library(dlnm); library(splines); library(sf); library(spdep)})
setwd(Sys.getenv("P3_DIR", "."))

D <- fread("data/P3_dengue_admin1_month_climate.csv")
D <- D[iso3 != "AUS"]
setorder(D, shapeID, year, month)

# ---- eligibility: >=80% of months reported in 2010-2022 (2009 kept only to supply lags) ----
comp <- D[year %between% c(2010, 2022), .(obs = mean(!is.na(dengue_cases))), by = shapeID]
keep <- comp[obs >= 0.8, shapeID]
D <- D[shapeID %in% keep]
stopifnot(uniqueN(D$shapeID) == 196)

# ---- optional population and urbanisation (after the Earth Engine merge) ----
popfile <- "data/P3_dengue_admin1_month_climate_pop_urban.csv"
HAS_POP <- file.exists(popfile)
if (HAS_POP) {
  P <- fread(popfile)[, .(shapeID, year, month, population, built_fraction, urban_tertile_within_country)]
  D <- merge(D, P, by = c("shapeID", "year", "month"), all.x = TRUE)
  setorder(D, shapeID, year, month)
}

# ---- indices ----
D[, t := (year - 2009) * 12 + month]                       # 1..168 (2009-01 = 1)
D[, prov_id := as.integer(factor(shapeID))]
D[, ctry_id := as.integer(factor(iso3))]
D[, cy_id := as.integer(factor(paste(iso3, year)))]
D[, year_c := year - 2016]                                 # centred year for the interim province trend

# ---- cross-bases (lags built within province on the full 2009-2022 series) ----
LAG <- 6
an <- D[year %between% c(2010, 2022)]                      # knots from the analysis period
kt <- quantile(an$power_tmean_c, c(.10, .50, .90), na.rm = TRUE)
kr <- quantile(an$power_precip_mm, c(.10, .50, .90), na.rm = TRUE)
ref_t <- median(an$power_tmean_c, na.rm = TRUE); ref_r <- median(an$power_precip_mm, na.rm = TRUE)

lagmat <- function(x, g, L) {                               # matrix of x at lags 0..L within group g
  M <- sapply(0:L, function(l) ave(x, g, FUN = function(v) shift(v, l)))
  colnames(M) <- paste0("l", 0:L); M
}
Tm <- lagmat(D$power_tmean_c, D$shapeID, LAG)
Rm <- lagmat(D$power_precip_mm, D$shapeID, LAG)
Om <- lagmat(D$oni_anomaly, D$shapeID, LAG)

argvar_t <- list(fun = "ns", knots = kt)
argvar_r <- list(fun = "ns", knots = kr)
arglag   <- list(fun = "ns", df = 3, intercept = TRUE)
cb_t <- crossbasis(Tm, lag = LAG, argvar = argvar_t, arglag = arglag)
cb_r <- crossbasis(Rm, lag = LAG, argvar = argvar_r, arglag = arglag)
colnames(cb_t) <- paste0("cbT.", colnames(cb_t)); colnames(cb_r) <- paste0("cbR.", colnames(cb_r))
colnames(Om) <- paste0("oni.", colnames(Om))

# ---- keep the analysis period ----
idx <- which(D$year %between% c(2010, 2022))
keep_cb <- function(cb, idx) {                              # subset rows, keep crossbasis attributes
  at <- attributes(cb); out <- cb[idx, , drop = FALSE]
  for (n in setdiff(names(at), c("dim", "dimnames"))) attr(out, n) <- at[[n]]
  attr(out, "dimnames") <- list(NULL, colnames(cb)); out }
D <- D[idx]; cb_t <- keep_cb(cb_t, idx); cb_r <- keep_cb(cb_r, idx); Om <- Om[idx, , drop = FALSE]
stopifnot(nrow(D) == 30576, !anyNA(cb_t), !anyNA(cb_r), !anyNA(Om))

# ---- adjacency graph: within country only; islands linked to nearest province in the same country ----
S <- st_read("/vsizip/data/boundaries/P3_provinces_ADM1_shapefile.zip/P3_provinces_ADM1.shp", quiet = TRUE)
S <- S[S$shapeID %in% keep, ]
S <- S[match(levels(factor(D$shapeID)), S$shapeID), ]
stopifnot(identical(S$shapeID, levels(factor(D$shapeID))))
sf_use_s2(FALSE)
nb <- poly2nb(S, snap = 0.01, queen = TRUE)
ctry <- S$iso3
for (i in seq_along(nb)) nb[[i]] <- as.integer(setdiff(nb[[i]][ctry[nb[[i]]] == ctry[i]], 0L))
cent <- suppressWarnings(st_coordinates(st_point_on_surface(S)))
d2 <- function(i, j) (cent[j, 1] - cent[i, 1])^2 + (cent[j, 2] - cent[i, 2])^2
iso <- 0L; added <- 0L
repeat {                                   # join components within each country, nearest pair of provinces
  nbx <- lapply(nb, function(v) if (length(v)) as.integer(v) else 0L); class(nbx) <- "nb"
  cmp <- n.comp.nb(nbx)$comp.id; done <- TRUE
  for (cc in unique(ctry)) {
    ii <- which(ctry == cc); comps <- unique(cmp[ii]); if (length(comps) < 2) next
    done <- FALSE
    a1 <- ii[cmp[ii] == comps[1]]; b1 <- ii[cmp[ii] != comps[1]]
    best <- c(NA, NA, Inf)
    for (i in a1) { dj <- d2(i, b1); k <- which.min(dj); if (dj[k] < best[3]) best <- c(i, b1[k], dj[k]) }
    i <- best[1]; j <- best[2]; nb[[i]] <- as.integer(sort(unique(c(nb[[i]], j)))); nb[[j]] <- as.integer(sort(unique(c(nb[[j]], i)))); added <- added + 1L
  }
  if (done) break
}
iso <- seq_len(added)
nb <- lapply(nb, function(v) if (length(v)) as.integer(v) else 0L); class(nb) <- "nb"
dir.create("out", showWarnings = FALSE)
nb2INLA("out/p3_graph.adj", nb)
comp_n <- n.comp.nb(nb)$nc
cat("Provinces:", nrow(S), " added links (islands and gaps):", added, " graph components:", comp_n,
    " (one per country expected = ", uniqueN(ctry), ")\n")

saveRDS(list(D = D, cb_t = cb_t, cb_r = cb_r, Om = Om, kt = kt, kr = kr, ref_t = ref_t, ref_r = ref_r,
             argvar_t = argvar_t, argvar_r = argvar_r, arglag = arglag, LAG = LAG, HAS_POP = HAS_POP),
        "out/p3_model_data.rds")
cat("Rows:", nrow(D), " provinces:", uniqueN(D$shapeID), " cross-basis columns:", ncol(cb_t), "+", ncol(cb_r),
    " population offset:", HAS_POP, "\nKnots temperature:", round(kt, 2), " rainfall:", round(kr, 1),
    "\nCentring: ", round(ref_t, 2), "°C, ", round(ref_r, 1), " mm\n")
