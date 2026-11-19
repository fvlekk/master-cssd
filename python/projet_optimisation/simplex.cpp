// =========================================================================
//  Methode du simplexe  -  resolution d'un programme lineaire
//
//  Deux formes acceptees :
//    MAX : maximiser c'x  sous  Ax <= b , x >= 0   -> simplexe direct
//    MIN : minimiser c'x  sous  Ax >= b , x >= 0   -> resolu via son dual
//
//  Ce seul fichier sert aux deux versions du programme :
//    g++ -O2 -o simplex simplex.cpp     -> programme en ligne de commande
//    em++ ... simplex.cpp               -> module WebAssembly pour la page web
//  (le main et le pont web sont separes par un #ifdef en bas du fichier)
// =========================================================================

#include <cmath>
#include <sstream>
#include <string>
#include <vector>

// Deux formes de problemes sont acceptees :
//   MAX : maximiser c'x  sous  Ax <= b , x >= 0   -> resolu directement
//   MIN : minimiser c'x  sous  Ax >= b , x >= 0   -> resolu via son dual
// Dans les deux cas le tableau final donne la solution du probleme pose
// ET celle de son dual, ce qui evite la phase 1 et les variables artificielles.
enum TypeProbleme { MAX = 1, MIN = 2 };

enum Statut { OPTIMAL, NON_BORNE, ERREUR_DONNEES };

struct Probleme {
    TypeProbleme type;
    int n;                                // nombre de variables
    int m;                                // nombre de contraintes
    std::vector<double> c;                // objectif, taille n
    std::vector<std::vector<double>> A;   // contraintes, taille m x n
    std::vector<double> b;                // second membre, taille m
};

// Instantane du tableau conserve pour l'affichage pas a pas.
struct Etape {
    std::vector<std::vector<double>> T;
    std::vector<int> base;          // indice de la variable basique de chaque ligne
    int lignePivot;                 // -1 pour le tableau initial et le tableau final
    int colonnePivot;               // -1 idem
};

struct Resultat {
    Statut statut;
    std::string message;
    double valeurOptimale;

    std::vector<double> solutionPrimale;  // x* : les variables du probleme pose
    std::vector<double> solutionDuale;    // y* : les variables de son dual

    bool passeParDual;                    // vrai quand le probleme pose est un MIN
    Probleme problemeResolu;              // ce qui a reellement ete donne au simplexe

    std::vector<Etape> etapes;
};

static const double EPS = 1e-9;

// ---------------------------------------------------------------------------
// Dual d'un probleme de minimisation
//
//   primal :  min c'x   sous  Ax >= b , x >= 0      (m contraintes, n variables)
//   dual   :  max b'y   sous  A'y <= c , y >= 0     (n contraintes, m variables)
//
// Le dual est en forme standard : c'est lui qu'on donne au simplexe.
// ---------------------------------------------------------------------------
Probleme construireDual(const Probleme& p) {
    Probleme d;
    d.type = MAX;
    d.n = p.m;              // une variable duale par contrainte du primal
    d.m = p.n;              // une contrainte duale par variable du primal
    d.c = p.b;              // l'objectif du dual est le second membre du primal
    d.b = p.c;              // et son second membre est l'objectif du primal

    // A' : la transposee de A
    d.A.assign(d.m, std::vector<double>(d.n, 0.0));
    for (int i = 0; i < d.m; i++)
        for (int j = 0; j < d.n; j++)
            d.A[i][j] = p.A[j][i];

    return d;
}

// ---------------------------------------------------------------------------
// Operation de pivot (Gauss-Jordan) autour de T[l][e]
// ---------------------------------------------------------------------------
static void pivoter(std::vector<std::vector<double>>& T, int l, int e) {
    int lignes = (int)T.size();
    int colonnes = (int)T[0].size();

    double p = T[l][e];
    for (int j = 0; j < colonnes; j++)
        T[l][j] /= p;                       // la ligne du pivot est normalisee

    for (int i = 0; i < lignes; i++) {
        if (i == l) continue;
        double f = T[i][e];
        if (std::fabs(f) < EPS) continue;       // coefficient deja nul
        for (int j = 0; j < colonnes; j++)
            T[i][j] -= f * T[l][j];         // on annule la colonne du pivot ailleurs
    }
}

// ---------------------------------------------------------------------------
// Simplexe sur un probleme deja en forme standard : max c'x, Ax <= b, b >= 0
//
// Disposition du tableau (m+1 lignes, n+m+1 colonnes) :
//   colonnes 0..n-1      : variables de decision
//   colonnes n..n+m-1    : variables d'ecart
//   colonne  n+m         : second membre
//   ligne    m           : objectif, garde les couts reduits (c_j - z_j)
// ---------------------------------------------------------------------------
static Resultat simplexeStandard(const Probleme& p) {
    Resultat r;
    r.statut = OPTIMAL;
    r.valeurOptimale = 0.0;
    r.passeParDual = false;
    r.problemeResolu = p;

    int n = p.n, m = p.m;
    int largeur = n + m + 1;
    int ligneObj = m;
    int colRhs = n + m;

    // Le second membre doit etre positif : sinon la base des variables d'ecart
    // n'est pas realisable et il faudrait une phase 1.
    for (int i = 0; i < m; i++) {
        if (p.b[i] < -EPS) {
            r.statut = ERREUR_DONNEES;
            r.message = "Le second membre doit etre positif ou nul "
                        "(forme standard, sans phase 1).";
            return r;
        }
    }

    std::vector<std::vector<double>> T(m + 1, std::vector<double>(largeur, 0.0));
    std::vector<int> base(m);

    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) T[i][j] = p.A[i][j];
        T[i][n + i] = 1.0;                  // variable d'ecart de la contrainte i
        T[i][colRhs] = p.b[i];
        base[i] = n + i;                    // base de depart : toutes les variables d'ecart
    }
    for (int j = 0; j < n; j++)
        T[ligneObj][j] = p.c[j];            // couts reduits initiaux : c_j - z_j avec z_j = 0

    Etape depart;
    depart.T = T;
    depart.base = base;
    depart.lignePivot = -1;
    depart.colonnePivot = -1;
    r.etapes.push_back(depart);

    // Garde-fou : en cas de degenerescence le simplexe pourrait tourner en rond.
    int maxIterations = 200 * (n + m) + 100;
    bool optimumAtteint = false;

    for (int iteration = 0; iteration < maxIterations; iteration++) {
        // --- choix de la colonne entrante : le c_j - z_j le plus positif ---
        int e = -1;
        double plusPositif = EPS;
        for (int j = 0; j < n + m; j++) {
            if (T[ligneObj][j] > plusPositif) {
                plusPositif = T[ligneObj][j];
                e = j;
            }
        }
        if (e == -1) { optimumAtteint = true; break; }  // plus aucun positif : optimum

        // --- choix de la ligne sortante (test du rapport minimal) -----------
        int l = -1;
        double meilleurRapport = 0.0;
        for (int i = 0; i < m; i++) {
            if (T[i][e] <= EPS) continue;   // on ignore les coefficients nuls ou negatifs
            double rapport = T[i][colRhs] / T[i][e];
            if (l == -1 || rapport < meilleurRapport) {
                meilleurRapport = rapport;
                l = i;
            }
        }
        if (l == -1) {
            // Aucune borne sur la variable entrante : l'objectif croit indefiniment.
            r.etapes.back().colonnePivot = e;
            r.statut = NON_BORNE;
            r.message = "Probleme non borne : l'objectif peut croitre indefiniment.";
            return r;
        }

        r.etapes.back().lignePivot = l;
        r.etapes.back().colonnePivot = e;

        pivoter(T, l, e);
        base[l] = e;

        Etape suivante;
        suivante.T = T;
        suivante.base = base;
        suivante.lignePivot = -1;
        suivante.colonnePivot = -1;
        r.etapes.push_back(suivante);
    }

    if (!optimumAtteint) {
        r.statut = ERREUR_DONNEES;
        r.message = "Le calcul n'a pas converge dans le nombre d'iterations autorise.";
        return r;
    }

    // --- lecture du tableau optimal -----------------------------------------
    // Avec la convention c_j - z_j, le coin de la ligne f contient -f.
    r.valeurOptimale = -T[ligneObj][colRhs];
    if (std::fabs(r.valeurOptimale) < EPS) r.valeurOptimale = 0.0;

    // Les variables de decision : valeur du second membre si elles sont en base.
    r.solutionPrimale.assign(n, 0.0);
    for (int i = 0; i < m; i++)
        if (base[i] < n) r.solutionPrimale[base[i]] = T[i][colRhs];

    // Les variables duales se lisent dans la ligne f, sous les variables d'ecart.
    r.solutionDuale.assign(m, 0.0);
    for (int i = 0; i < m; i++) {
        double y = -T[ligneObj][n + i];
        r.solutionDuale[i] = (std::fabs(y) < EPS) ? 0.0 : y;   // evite un "-0"
    }

    r.message = "Solution optimale trouvee.";
    return r;
}

// ---------------------------------------------------------------------------
Resultat resoudre(const Probleme& p) {
    if (p.type == MAX) {
        Resultat r = simplexeStandard(p);
        r.passeParDual = false;
        return r;
    }

    // MIN : on resout le dual, qui lui est en forme standard.
    Probleme d = construireDual(p);
    Resultat r = simplexeStandard(d);
    r.passeParDual = true;
    r.problemeResolu = d;

    // etapes vide : l'erreur vient du second membre, detectee avant la 1ere iteration.
    if (r.statut == ERREUR_DONNEES && r.etapes.empty()) {
        r.message = "Les coefficients de l'objectif doivent etre positifs ou nuls : "
                    "ils forment le second membre du dual.";
        return r;
    }
    if (r.statut != OPTIMAL) return r;

    // Le simplexe a travaille sur le dual, donc ses resultats sont inverses :
    //   la solution de base du tableau     -> y* (variables duales)
    //   les couts reduits sous les ecarts  -> x* (variables du probleme pose)
    std::vector<double> y = r.solutionPrimale;   // taille d.n == p.m
    std::vector<double> x = r.solutionDuale;     // taille d.m == p.n
    r.solutionPrimale = x;
    r.solutionDuale = y;
    // Par dualite forte, min c'x = max b'y : la valeur optimale est la meme.
    return r;
}

// ---------------------------------------------------------------------------
Probleme lireProbleme(std::istream& entree) {
    Probleme p;
    int type = 1;
    entree >> type;
    p.type = (type == 2) ? MIN : MAX;

    entree >> p.n >> p.m;
    if (p.n < 1) p.n = 0;
    if (p.m < 1) p.m = 0;

    p.c.assign(p.n, 0.0);
    for (int j = 0; j < p.n; j++) entree >> p.c[j];

    p.A.assign(p.m, std::vector<double>(p.n, 0.0));
    p.b.assign(p.m, 0.0);
    for (int i = 0; i < p.m; i++) {
        for (int j = 0; j < p.n; j++) entree >> p.A[i][j];
        entree >> p.b[i];
    }
    return p;
}

// ---------------------------------------------------------------------------
// Serialisation JSON, envoyee a la page web.
// ---------------------------------------------------------------------------
static std::string nombre(double v) {
    if (std::fabs(v) < EPS) v = 0.0;        // evite d'afficher "-0"
    std::ostringstream o;
    o.precision(10);
    o << v;
    return o.str();
}

static std::string ligneJson(const std::vector<double>& v) {
    std::string s = "[";
    for (size_t i = 0; i < v.size(); i++) {
        if (i > 0) s += ",";
        s += nombre(v[i]);
    }
    return s + "]";
}

static std::string matriceJson(const std::vector<std::vector<double>>& M) {
    std::string s = "[";
    for (size_t i = 0; i < M.size(); i++) {
        if (i > 0) s += ",";
        s += ligneJson(M[i]);
    }
    return s + "]";
}

std::string resultatEnJson(const Resultat& r) {
    std::string statut = "OPTIMAL";
    if (r.statut == NON_BORNE) statut = "NON_BORNE";
    else if (r.statut == ERREUR_DONNEES) statut = "ERREUR_DONNEES";

    // q : le probleme reellement passe au simplexe (le dual dans le cas MIN).
    const Probleme& q = r.problemeResolu;

    std::string s = "{";
    s += "\"statut\":\"" + statut + "\",";
    s += "\"message\":\"" + r.message + "\",";
    s += "\"passeParDual\":";
    s += (r.passeParDual ? "true," : "false,");
    s += "\"valeurOptimale\":" + nombre(r.valeurOptimale) + ",";
    s += "\"solutionPrimale\":" + ligneJson(r.solutionPrimale) + ",";
    s += "\"solutionDuale\":" + ligneJson(r.solutionDuale) + ",";
    s += "\"n\":" + std::to_string(q.n) + ",";
    s += "\"m\":" + std::to_string(q.m) + ",";
    s += "\"c\":" + ligneJson(q.c) + ",";
    s += "\"b\":" + ligneJson(q.b) + ",";
    s += "\"A\":" + matriceJson(q.A) + ",";

    s += "\"etapes\":[";
    for (size_t k = 0; k < r.etapes.size(); k++) {
        const Etape& e = r.etapes[k];
        if (k > 0) s += ",";
        s += "{\"lignePivot\":" + std::to_string(e.lignePivot);
        s += ",\"colonnePivot\":" + std::to_string(e.colonnePivot);
        s += ",\"base\":[";
        for (size_t i = 0; i < e.base.size(); i++) {
            if (i > 0) s += ",";
            s += std::to_string(e.base[i]);
        }
        s += "],\"T\":" + matriceJson(e.T) + "}";
    }
    s += "]}";

    return s;
}

// =========================================================================
//  Point d'entree : celui du navigateur, ou celui de la ligne de commande.
// =========================================================================
#ifdef __EMSCRIPTEN__

// --- version web : le JavaScript envoie le probleme, recoit le JSON --------
#include <emscripten/emscripten.h>

extern "C" {

EMSCRIPTEN_KEEPALIVE
const char* resoudreTexte(const char* entree) {
    // Conserve la chaine entre deux appels : le JavaScript lit le pointeur
    // apres le retour de la fonction.
    static std::string sortie;

    std::istringstream flux(entree);
    Probleme p = lireProbleme(flux);
    Resultat r = resoudre(p);
    sortie = resultatEnJson(r);

    return sortie.c_str();
}

}

#else

// --- version ligne de commande --------------------------------------------
#include <iomanip>
#include <iostream>

// Les variables d'ecart continuent la numerotation : x1, x2 de decision,
// puis x3, x4, x5 pour les ecarts.
static std::string nomColonne(int j, const Resultat& r) {
    std::string lettre = r.passeParDual ? "y" : "x";
    return lettre + std::to_string(j + 1);
}

static void afficherTableau(const Etape& e, const Resultat& r, int numero) {
    const Probleme& q = r.problemeResolu;
    int colRhs = q.n + q.m;

    std::cout << "\n--- Tableau " << numero << " ---\n";
    std::cout << std::setw(6) << "" << std::setw(10) << "bi";   // coin vide
    for (int j = 0; j < colRhs; j++)
        std::cout << std::setw(10) << nomColonne(j, r);
    std::cout << "\n";

    for (size_t i = 0; i < e.T.size(); i++) {
        bool estObjectif = (i + 1 == e.T.size());
        std::cout << std::setw(6) << (estObjectif ? "f" : nomColonne(e.base[i], r));
        // largeur fixe : c'est ce qui aligne les colonnes les unes sous les autres
        std::cout << std::fixed << std::setprecision(3);

        // le second membre a gauche ; sur la ligne f le coin vaut -f
        double bi = estObjectif ? -e.T[i][colRhs] : e.T[i][colRhs];
        if (std::fabs(bi) < EPS) bi = 0.0;
        std::cout << std::setw(10) << bi;

        for (int j = 0; j < colRhs; j++)
            std::cout << std::setw(10) << e.T[i][j];
        std::cout << "\n";
    }

    if (e.lignePivot >= 0 && e.colonnePivot >= 0) {
        std::cout << "pivot : ligne " << (e.lignePivot + 1)
                  << ", colonne " << nomColonne(e.colonnePivot, r) << "\n";
    }
}

int main() {
    std::cout << "Entrez le probleme, dans cet ordre :\n"
              << "  1 pour un max (contraintes <=) ou 2 pour un min (contraintes >=)\n"
              << "  le nombre de variables, puis le nombre de contraintes\n"
              << "  les coefficients de l'objectif\n"
              << "  chaque contrainte : ses coefficients, puis le second membre\n\n";

    Probleme p = lireProbleme(std::cin);
    Resultat r = resoudre(p);

    if (r.passeParDual) {
        std::cout << "\nProbleme de minimisation : resolution par le dual "
                     "(max b'y sous A'y <= c).\n";
    }

    for (size_t k = 0; k < r.etapes.size(); k++)
        afficherTableau(r.etapes[k], r, (int)k);

    std::cout << "\n=== Resultat ===\n" << r.message << "\n";
    if (r.statut != OPTIMAL) return 0;

    std::cout << "Valeur optimale : " << r.valeurOptimale << "\n";

    std::cout << (r.passeParDual ? "Solution du primal (min)  : " : "Solution du primal (max)  : ");
    for (size_t j = 0; j < r.solutionPrimale.size(); j++)
        std::cout << "x" << (j + 1) << "=" << r.solutionPrimale[j] << "  ";
    std::cout << "\n";

    std::cout << "Solution du dual          : ";
    for (size_t i = 0; i < r.solutionDuale.size(); i++)
        std::cout << "y" << (i + 1) << "=" << r.solutionDuale[i] << "  ";
    std::cout << "\n";

    return 0;
}

#endif
