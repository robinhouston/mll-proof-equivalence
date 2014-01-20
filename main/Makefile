all: mllequiv.pdf scratch-2.pdf scratch.pdf LICS.pdf

mllequiv.pdf: mllequiv.tex s_background.tex s_level_0.tex
	latexmk -pdf mllequiv.tex

%.pdf: %.tex mllequiv.sty refs.bib
	latexmk -pdf $<
