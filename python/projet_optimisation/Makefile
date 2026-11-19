# make        -> programme en ligne de commande (g++)
# make web    -> module WebAssembly pour l'interface (em++)

CXXFLAGS = -O2 -std=c++17 -Wall

simplex: simplex.cpp
	g++ $(CXXFLAGS) -o simplex simplex.cpp

web: simplex.cpp
	em++ $(CXXFLAGS) simplex.cpp \
		-o web/simplex.js \
		-s EXPORTED_FUNCTIONS='["_resoudreTexte","_malloc","_free"]' \
		-s EXPORTED_RUNTIME_METHODS='["ccall","cwrap"]' \
		-s MODULARIZE=1 -s EXPORT_NAME=creerSimplex \
		-s SINGLE_FILE=1

clean:
	rm -f simplex web/simplex.js

.PHONY: web clean
