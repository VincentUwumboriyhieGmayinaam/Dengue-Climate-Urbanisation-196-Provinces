# GHSL R2023A province summaries: sums built-up surface and population within each province for 2010, 2015 and 2020
# (Mollweide 1 km grids read directly from the downloaded zips) -> data/P3_ghsl_province_epoch.csv. Run from the repository root.

if (!requireNamespace("terra", quietly = TRUE)) install.packages("terra", repos = "https://cloud.r-project.org")
library(terra)
terraOptions(progress = 0, memfrac = 0.6)

dl  <- Sys.getenv("GHSL_DIR", "data/raw/ghsl")   # folder with the six GHSL R2023A 1 km zips (BUILT_S and POP, 2010/2015/2020)
shpzip <- "data/boundaries/P3_provinces_ADM1_shapefile.zip"
stopifnot(file.exists(shpzip))
tmp <- file.path(tempdir(), "p3shp"); dir.create(tmp, showWarnings = FALSE); unzip(shpzip, exdir = tmp)
V <- vect(file.path(tmp, "P3_provinces_ADM1.shp"))
V <- project(V, "ESRI:54009")
cat("Provinces:", nrow(V), "\n")

out <- list()
for (kind in c("BUILT_S", "POP")) for (ep in c(2010, 2015, 2020)) {
  nm <- sprintf("GHS_%s_E%d_GLOBE_R2023A_54009_1000_V1_0", kind, ep)
  z <- file.path(dl, paste0(nm, ".zip")); stopifnot(file.exists(z))
  r <- rast(paste0("/vsizip/", normalizePath(z, winslash = "/"), "/", nm, ".tif"))
  vals <- numeric(nrow(V)); cells <- integer(nrow(V))
  for (iso in unique(V$iso3)) {                       # crop to each country to keep memory low
    i <- which(V$iso3 == iso); rc <- crop(r, ext(V[i]) + 2000)
    rc[rc < 0] <- NA
    e <- extract(rc, V[i], fun = sum, na.rm = TRUE, ID = FALSE)
    n <- extract(!is.na(rc), V[i], fun = sum, na.rm = TRUE, ID = FALSE)
    vals[i] <- e[[1]]; cells[i] <- n[[1]]
  }
  out[[paste(kind, ep)]] <- data.frame(iso3 = V$iso3, shapeID = V$shapeID, epoch = ep, kind = kind, value = vals, cells = cells)
  cat("done", kind, ep, "\n"); flush.console()
}
R <- do.call(rbind, out)
B <- R[R$kind == "BUILT_S", ]; P <- R[R$kind == "POP", ]
W <- merge(B[, c("iso3", "shapeID", "epoch", "value", "cells")], P[, c("shapeID", "epoch", "value")], by = c("shapeID", "epoch"))
names(W) <- c("shapeID", "epoch", "iso3", "built_m2", "land_km2", "pop")
W$built_fraction <- W$built_m2 / (W$land_km2 * 1e6)
f <- "data/P3_ghsl_province_epoch.csv"; write.csv(W, f, row.names = FALSE)
cat("\nSaved:", f, "\n"); print(aggregate(cbind(pop_millions = pop / 1e6) ~ iso3 + epoch, W, sum))
