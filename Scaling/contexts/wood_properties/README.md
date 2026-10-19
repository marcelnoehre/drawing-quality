# Wood properties

`wood_properties.cxt` — 29 kinds of wood (German names: tanne fir, kiefer pine, eiche
oak, rbuche common beech, wbuche hornbeam, …) and 28 abbreviated attributes
(*fpor, brüchig, lspaltb, arbs, dauer, zäh, gpor, r, schwspaltb, gjähr, reißt, k_r,
weich, biegs, n_elas, harzr, elas, arbw, fjähr, s, k, l, schnit, n_dauer, k_s, r_s,
mhart, hart*). Imported unchanged from the surrounding repository, which took it from
conexp-clj's `testing-data/Wood-Properties.ctx`.

## Source

conexp-clj's context descriptions: "found in lecture notes of Gerd Stumme", "a
context about properties of different kinds of wood" (https://github.com/tomhanika/conexp-clj/blob/master/testing-data/context-descriptions.org). No codebook for the
abbreviations was found in conexp-clj, in the public FCA context repository, or
elsewhere online.

Many decode plausibly from German wood science -- *fpor/gpor* fine- or coarse-pored,
*lspaltb/schwspaltb* easy or hard to split, *fjähr/gjähr* narrow or wide annual
rings, *dauer/n_dauer* durable or not, *elas/n_elas*, *weich/mhart/hart*, *harzr*
resinous, *biegs* flexible -- but *r, s, k, l, k_r, k_s, r_s, arbs, arbw, schnit*
cannot be decoded with confidence (*k, r, s* may be heartwood, ripewood and sapwood
types). Scales chosen by meaning need the meanings, so this context is not scaled
until a codebook of the abbreviations is available.
