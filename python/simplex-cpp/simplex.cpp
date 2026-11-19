// =====================================================================
//                 ALGORITHME DU SIMPLEXE (méthode des tableaux)
//                       version C++ de simplex.py
// =====================================================================
//
// Même programme que la version Python, avec les mêmes fonctions :
//   afficher, ligne_sortante, pivoter, lire_solution, simplex
//
//   1) MAX :  max f(x) = c1*x1 + ... + cn*xn
//             avec des contraintes  <=  et  x >= 0
//             -> on applique le simplexe directement.
//
//   2) MIN :  min f(y) = c1*y1 + ... + cn*yn      (le "primal")
//             avec des contraintes  >=  et  y >= 0
//             -> on résout le dual (un problème de MAX) :
//                  max f(x) = b1*x1 + ... + bm*xm
//                  avec les contraintes de A transposée  <=  c
//             -> la solution du primal (les yi) se lit dans le dernier tableau.
//
// Règles du simplexe (comme le prof) :
//   - variable entrante : la PLUS GRANDE valeur de la ligne f
//     (colonnes des variables du problème seulement ; égalité -> la dernière)
//   - variable sortante : le plus petit rapport  b / coefficient  (coef > 0)
//   - on s'arrête quand toutes ces valeurs de la ligne f sont <= 0
//   - variable hors base avec 0 dans la ligne f -> autre solution optimale
//
// Disposition du tableau : b est dans la PREMIÈRE colonne (colonne 0),
// puis la colonne j contient la variable xj (x1 en colonne 1, x2 en 2...).
//
// Différence avec Python : pas de fractions en C++ de base, on calcule
// avec des nombres à virgule (double). Comme ils ont de petites erreurs
// d'arrondi, on considère qu'un nombre plus petit que EPS vaut 0.
//
// Compilation :  g++ simplex.cpp -o simplex
// Lancement   :  ./simplex
// =====================================================================

#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
#include <cmath>
#include <cstdlib>
using namespace std;

typedef vector<double> Ligne;        // une ligne du tableau
typedef vector<Ligne> Tableau;       // le tableau = une liste de lignes

const double EPS = 1e-9;             // en dessous de EPS, on considère que c'est 0


// ---------------------------------------------------------------------
// Pour l'affichage : remplace les tout petits nombres (ex : -0.0000001)
// par 0, sinon on verrait des "-0" à cause des arrondis
// ---------------------------------------------------------------------
double propre(double v) {
    if (fabs(v) < EPS) return 0;
    return v;
}


// ---------------------------------------------------------------------
// Affiche un tableau du simplexe
//   T    : le tableau. Chaque ligne = [b, coefficients...]
//          La dernière ligne de T est la ligne f.
//   base : base[i] = numéro de la variable en base sur la ligne i
//          (= numéro de sa colonne : 1 pour x1, 2 pour x2...)
//   n    : nombre de variables du problème (sans les variables d'écart)
// ---------------------------------------------------------------------
void afficher(const Tableau& T, const vector<int>& base, int n) {
    int m = T.size() - 1;                // nombre de contraintes

    // ligne d'en-tête : base, b, puis x1 ... x(n+m)
    cout << setw(6) << "base" << setw(10) << "b";
    for (int j = 1; j <= n + m; j++) cout << setw(10) << "x" + to_string(j);
    cout << endl;

    // les lignes des contraintes : variable en base, b, coefficients
    for (int i = 0; i < m; i++) {
        cout << setw(6) << "x" + to_string(base[i]);
        for (int j = 0; j <= n + m; j++) cout << setw(10) << propre(T[i][j]);
        cout << endl;
    }

    // la ligne f : la case b contient -f, on affiche son opposé (comme le prof)
    cout << setw(6) << "f" << setw(10) << propre(-T[m][0]);
    for (int j = 1; j <= n + m; j++) cout << setw(10) << propre(T[m][j]);
    cout << endl << endl;
}


// ---------------------------------------------------------------------
// Cherche la ligne de la variable sortante pour la colonne "col"
// = la ligne avec le plus petit rapport b / coefficient (coefficient > 0)
// Renvoie -1 si aucun coefficient n'est > 0 (problème non borné)
// ---------------------------------------------------------------------
int ligne_sortante(const Tableau& T, int col) {
    int lig = -1;
    for (int i = 0; i < (int)T.size() - 1; i++) {     // pas la ligne f
        if (T[i][col] > EPS) {
            double rapport = T[i][0] / T[i][col];
            // "- EPS" : en cas d'égalité on garde la première ligne
            if (lig == -1 || rapport < T[lig][0] / T[lig][col] - EPS) {
                lig = i;
            }
        }
    }
    return lig;
}


// ---------------------------------------------------------------------
// Fait le pivot sur la case (lig, col) :
//   - on divise la ligne du pivot par le pivot (le pivot devient 1)
//   - sur les autres lignes : ligne = ligne - coefficient * ligne du pivot
//   - la variable de la colonne entre dans la base
//
// C'est la même chose que la règle du rectangle (multiplication croisée)
// du cours, mais écrite ligne par ligne :
//   (pivot*case - coin1*coin2) / pivot  =  case - coin1 * (coin2 / pivot)
// Comme le tableau est une liste de lignes, c'est plus simple de traiter
// une ligne entière d'un coup (et la ligne f se traite comme les autres).
// ---------------------------------------------------------------------
void pivoter(Tableau& T, vector<int>& base, int lig, int col) {
    double pivot = T[lig][col];
    for (int j = 0; j < (int)T[lig].size(); j++) {
        T[lig][j] = T[lig][j] / pivot;
    }

    for (int i = 0; i < (int)T.size(); i++) {
        if (i != lig) {
            double coef = T[i][col];
            for (int j = 0; j < (int)T[i].size(); j++) {
                T[i][j] = T[i][j] - coef * T[lig][j];
            }
        }
    }

    base[lig] = col;
}


// ---------------------------------------------------------------------
// Lit la solution dans un tableau :
//   une variable en base vaut la valeur de b sur sa ligne,
//   une variable hors base vaut 0
// ---------------------------------------------------------------------
Ligne lire_solution(const Tableau& T, const vector<int>& base, int n) {
    Ligne x(n, 0);
    for (int i = 0; i < (int)base.size(); i++) {
        if (base[i] <= n) {                  // on ignore les variables d'écart
            x[base[i] - 1] = T[i][0];        // xj est rangé à l'indice j-1
        }
    }
    return x;
}


// vrai si la variable j est dans la base
bool en_base(const vector<int>& base, int j) {
    for (int i = 0; i < (int)base.size(); i++) {
        if (base[i] == j) return true;
    }
    return false;
}

// vrai si la solution x est déjà dans la liste des solutions
bool deja_trouvee(const vector<Ligne>& solutions, const Ligne& x) {
    for (int k = 0; k < (int)solutions.size(); k++) {
        bool pareil = true;
        for (int j = 0; j < (int)x.size(); j++) {
            if (fabs(solutions[k][j] - x[j]) > EPS) pareil = false;
        }
        if (pareil) return true;
    }
    return false;
}


// ---------------------------------------------------------------------
// Le simplexe :  max c.x  avec  A x <= b  et  x >= 0
// Remplit "solutions" (vide si non borné) et renvoie le tableau final
// ---------------------------------------------------------------------
Tableau simplex(const Ligne& c, const Tableau& A, const Ligne& b, vector<Ligne>& solutions) {
    int n = c.size();                    // nombre de variables du problème
    int m = A.size();                    // nombre de contraintes

    // --- Construction du tableau de départ ---
    // chaque contrainte devient : [b | coefficients de A | variables d'écart]
    // la variable d'écart de la contrainte i, x(n+1+i), vaut 1 sur sa ligne
    Tableau T;
    for (int i = 0; i < m; i++) {
        Ligne ligne(1 + n + m, 0);
        ligne[0] = b[i];
        for (int j = 0; j < n; j++) ligne[1 + j] = A[i][j];
        ligne[n + 1 + i] = 1;
        T.push_back(ligne);
    }

    // ligne f : 0 dans la case b, les coefficients de f, puis des 0
    Ligne f(1 + n + m, 0);
    for (int j = 0; j < n; j++) f[1 + j] = c[j];
    T.push_back(f);

    // au départ, ce sont les variables d'écart x(n+1)..x(n+m) qui sont en base
    vector<int> base;
    for (int i = 0; i < m; i++) base.push_back(n + 1 + i);

    // --- Itérations ---
    int etape = 0;
    while (true) {
        cout << "Tableau " << etape << endl;
        afficher(T, base, n);

        // 1) Variable entrante : plus grande valeur de la ligne f
        //    (">=" pour prendre la dernière colonne en cas d'égalité)
        int col = 1;
        for (int j = 1; j <= n; j++) {
            if (T[m][j] >= T[m][col] - EPS) col = j;
        }

        // si la plus grande valeur est <= 0, on a fini
        if (T[m][col] <= EPS) break;

        // 2) Variable sortante
        int lig = ligne_sortante(T, col);
        if (lig == -1) {
            cout << "Problème non borné (pas de solution finie)." << endl;
            return T;                    // "solutions" reste vide
        }

        // 3) Pivot
        pivoter(T, base, lig, col);
        etape++;
    }

    // --- Solution(s) optimale(s) ---
    solutions.push_back(lire_solution(T, base, n));

    // Une variable hors base avec 0 dans la ligne f peut entrer sans changer
    // la valeur de f : on fait ce pivot pour trouver l'autre solution.
    // On travaille sur une copie (T2 = T copie tout le tableau en C++).
    for (int j = 1; j <= n + m; j++) {
        if (!en_base(base, j) && fabs(T[m][j]) < EPS) {
            int lig = ligne_sortante(T, j);
            if (lig == -1) continue;
            Tableau T2 = T;
            vector<int> base2 = base;
            pivoter(T2, base2, lig, j);
            Ligne x = lire_solution(T2, base2, n);
            if (!deja_trouvee(solutions, x)) {   // on n'affiche pas deux fois la même
                cout << "x" << j << " est hors base avec 0 dans f -> autre solution optimale :" << endl;
                afficher(T2, base2, n);
                solutions.push_back(x);
            }
        }
    }

    return T;
}


// ---------------------------------------------------------------------
// Lit une ligne de nombres séparés par des espaces (ex : "2 3 20")
// et redemande tant qu'il n'y a pas le bon nombre de valeurs.
// Accepte les entiers et les décimaux (0.5).
// ---------------------------------------------------------------------
Ligne lire_nombres(string message, int combien) {
    while (true) {
        cout << message;
        string texte;
        if (!getline(cin, texte)) exit(0);       // fin de la saisie

        istringstream flux(texte);
        Ligne valeurs;
        double v;
        while (flux >> v) valeurs.push_back(v);

        // flux.eof() : on a bien tout lu (pas de texte qui n'est pas un nombre)
        if ((int)valeurs.size() == combien && flux.eof()) return valeurs;
        cout << "  -> il faut " << combien << " nombres séparés par des espaces, recommence." << endl;
    }
}


// =====================================================================
//                          PROGRAMME PRINCIPAL
// =====================================================================
int main() {
    // --- Guide pour l'utilisateur ---
    cout << R"(
=====================================================
              ALGORITHME DU SIMPLEXE
=====================================================
Deux types de problèmes :
  max : max f(x) = c1x1 + ... + cnxn   contraintes <=
  min : min f(y) = c1y1 + ... + cnyn   contraintes >=
        (résolu en passant par le dual)
Les variables sont toujours >= 0.

Comment saisir :
  - f : les coefficients sur une ligne, séparés par des espaces
  - chaque contrainte sur une ligne :
    les coefficients, puis le second membre b à la fin

Exemple 1 :  max f(x) = 3x1 + 3x2
             2x1 + 3x2 <= 20
              x1 +  x2 <= 7
   type        : max
   variables   : 2
   contraintes : 2
   f           : 3 3
   contrainte 1: 2 3 20
   contrainte 2: 1 1 7

Exemple 2 :  min f(y) = 2y1 + 3y2
              y1 + 2y2 >= 10
             2y1 +  y2 >= 11
   type        : min
   variables   : 2
   contraintes : 2
   f           : 2 3
   contrainte 1: 1 2 10
   contrainte 2: 2 1 11

Si une variable n'apparaît pas dans une contrainte, mets 0.
Décimaux acceptés (0.5).
=====================================================
)" << endl;

    // --- Saisie du problème ---
    string type_pb;
    while (type_pb != "max" && type_pb != "min") {
        cout << "Type (max ou min) : ";
        if (!getline(cin, type_pb)) return 0;
    }

    string v = (type_pb == "max") ? "x" : "y";             // nom des variables

    int n = (int)lire_nombres("Nombre de variables : ", 1)[0];
    int m = (int)lire_nombres("Nombre de contraintes : ", 1)[0];

    string noms;                                            // ex : "x1 x2"
    for (int j = 1; j <= n; j++) noms += v + to_string(j) + " ";

    Ligne c = lire_nombres("f  (" + noms + ") : ", n);

    Tableau A;
    Ligne b;
    for (int i = 0; i < m; i++) {
        Ligne ligne = lire_nombres("contrainte " + to_string(i + 1) + "  (" + noms + "b) : ", n + 1);
        b.push_back(ligne[n]);           // le dernier nombre : le second membre b
        ligne.pop_back();                // on l'enlève, il reste les n coefficients
        A.push_back(ligne);
    }
    cout << endl;

    vector<Ligne> solutions;

    // --- Cas MAX : simplexe directement ---
    if (type_pb == "max") {
        simplex(c, A, b, solutions);
        for (int k = 0; k < (int)solutions.size(); k++) {
            cout << "Solution optimale " << k + 1 << " :" << endl;
            double fmax = 0;
            for (int j = 0; j < n; j++) {
                cout << "  x" << j + 1 << " = " << propre(solutions[k][j]) << endl;
                fmax += c[j] * solutions[k][j];
            }
            cout << "  f max = " << propre(fmax) << endl;
        }
    }

    // --- Cas MIN : on passe par le dual ---
    else {
        // Dual : max b.x  avec  (A transposée) x <= c
        // A transposée : la ligne j contient les coefficients de yj
        // dans chaque contrainte du primal
        Tableau tA(n, Ligne(m));
        for (int j = 0; j < n; j++)
            for (int i = 0; i < m; i++)
                tA[j][i] = A[i][j];

        // on affiche le dual pour pouvoir le comparer à celui du cours
        cout << "Primal : min f(y) = ";
        for (int j = 0; j < n; j++) cout << (j ? " + " : "") << c[j] << "y" << j + 1;
        cout << endl;
        for (int i = 0; i < m; i++) {
            cout << "         ";
            for (int j = 0; j < n; j++) cout << (j ? " + " : "") << A[i][j] << "y" << j + 1;
            cout << " >= " << b[i] << endl;
        }
        cout << "Dual   : max f(x) = ";
        for (int i = 0; i < m; i++) cout << (i ? " + " : "") << b[i] << "x" << i + 1;
        cout << endl;
        for (int j = 0; j < n; j++) {
            cout << "         ";
            for (int i = 0; i < m; i++) cout << (i ? " + " : "") << tA[j][i] << "x" << i + 1;
            cout << " <= " << c[j] << endl;
        }
        cout << endl;

        // on résout le dual (les rôles de b et c sont échangés)
        Tableau T = simplex(b, tA, c, solutions);

        if (!solutions.empty()) {
            // solution du dual : lue dans la colonne b, comme d'habitude
            Ligne x = solutions[0];
            cout << "Solution du dual :" << endl;
            double fmax = 0;
            for (int i = 0; i < m; i++) {
                cout << "  x" << i + 1 << " = " << propre(x[i]) << endl;
                fmax += b[i] * x[i];
            }
            cout << "  f max = " << propre(fmax) << endl;

            // solution du primal : lue dans la ligne f du dernier tableau,
            // sous les colonnes des variables d'écart, en changeant le signe.
            // (la variable d'écart de la contrainte j du dual est x(m+j+1),
            //  elle se trouve donc dans la colonne m+j+1)
            cout << "Solution du primal (ligne f, colonnes d'écart, signe changé) :" << endl;
            double fmin = 0;
            for (int j = 0; j < n; j++) {
                double y = -T.back()[m + 1 + j];     // T.back() = la ligne f (comme T[-1] en Python)
                cout << "  y" << j + 1 << " = " << propre(y) << endl;
                fmin += c[j] * y;
            }
            cout << "  f min = " << propre(fmin) << endl;
        }
    }

    return 0;
}
