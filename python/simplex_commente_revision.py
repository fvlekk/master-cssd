# =====================================================================
#                 ALGORITHME DU SIMPLEXE (méthode des tableaux)
# =====================================================================
#
# Le programme résout deux types de problèmes :
#
#   1) MAX :  max f(x) = c1*x1 + ... + cn*xn
#             avec des contraintes  <=  et  x >= 0
#             -> on applique le simplexe directement.
#
#   2) MIN :  min f(y) = c1*y1 + ... + cn*yn      (le "primal")
#             avec des contraintes  >=  et  y >= 0
#             -> on écrit le "dual", qui est un problème de MAX :
#                  max f(x) = b1*x1 + ... + bm*xm
#                  avec les contraintes de A transposée  <=  c
#             -> on résout le dual avec le simplexe, puis on lit
#                la solution du primal (les yi) dans le dernier tableau.
#
# Règles du simplexe utilisées (comme le prof) :
#   - variable entrante : la PLUS GRANDE valeur de la ligne f
#     (on regarde seulement les colonnes des variables du problème,
#      pas celles des variables d'écart ; en cas d'égalité, la dernière)
#   - variable sortante : le plus petit rapport  b / coefficient
#     (seulement pour les coefficients > 0)
#   - on s'arrête quand toutes ces valeurs de la ligne f sont <= 0
#   - si à la fin une variable hors base a 0 dans la ligne f,
#     il existe une autre solution optimale : on fait un pivot de plus.
#
# Tous les calculs sont faits en fractions (20/3, 1/3...) comme sur papier.
#
# Disposition du tableau : b est dans la PREMIÈRE colonne (colonne 0),
# puis la colonne j contient la variable xj (x1 en colonne 1, x2 en 2...).
# =====================================================================

from fractions import Fraction   # module de Python de base pour les fractions


# ---------------------------------------------------------------------
# Affiche un tableau du simplexe
#   T    : le tableau (liste de lignes). Chaque ligne = [b, coefficients...]
#          La dernière ligne de T est la ligne f.
#   base : base[i] = numéro de la variable en base sur la ligne i
#          (= numéro de sa colonne : 1 pour x1, 2 pour x2...)
#   n    : nombre de variables du problème (sans les variables d'écart)
# ---------------------------------------------------------------------
def afficher(T, base, n):
    m = len(T) - 1                       # nombre de contraintes
    # noms des colonnes : x1..xn puis les variables d'écart x(n+1)..x(n+m)
    noms = ["x" + str(j) for j in range(1, n + m + 1)]

    # ligne d'en-tête : base, b, puis le nom de chaque variable
    print("  base       b" + "".join(f"{v:>8}" for v in noms))

    # les lignes des contraintes : nom de la variable en base, b, coefficients
    # (b est dans la colonne 0, les coefficients dans les colonnes 1, 2...)
    for i in range(m):
        print(f"{'x' + str(base[i]):>6}{str(T[i][0]):>8}"
              + "".join(f"{str(v):>8}" for v in T[i][1:]))

    # la ligne f : dans le calcul, la case b de f vaut -f,
    # donc on affiche son opposé pour avoir la valeur de f (comme le prof)
    print(f"{'f':>6}{str(-T[-1][0]):>8}"
          + "".join(f"{str(v):>8}" for v in T[-1][1:]))
    print()


# ---------------------------------------------------------------------
# Cherche la ligne de la variable sortante pour la colonne "col"
# = la ligne avec le plus petit rapport b / coefficient (coefficient > 0)
# Renvoie -1 si aucun coefficient n'est > 0 (problème non borné)
# ---------------------------------------------------------------------
def ligne_sortante(T, col):
    lig = -1
    for i in range(len(T) - 1):          # on ne regarde pas la ligne f
        if T[i][col] > 0:
            rapport = T[i][0] / T[i][col]
            if lig == -1 or rapport < T[lig][0] / T[lig][col]:
                lig = i
    return lig


# ---------------------------------------------------------------------
# Fait le pivot sur la case (lig, col) :
#   - on divise la ligne du pivot par le pivot (le pivot devient 1)
#   - on fait apparaître des 0 dans la colonne du pivot sur les autres
#     lignes :  ligne = ligne - (coefficient de la colonne) * ligne du pivot
#   - la variable de la colonne entre dans la base à la place de l'ancienne
#
# C'est la même chose que la règle du rectangle du cours :
#   nouvelle case = case - coin1 * coin2 / pivot
# mais appliquée à une ligne entière d'un coup :
#   ligne = ligne - coin1 * (ligne du pivot / pivot)
# Comme le tableau est une liste de lignes, c'est plus simple de traiter
# une ligne entière d'un coup (et la ligne f se traite comme les autres).
# ---------------------------------------------------------------------
def pivoter(T, base, lig, col):
    pivot = T[lig][col]
    T[lig] = [v / pivot for v in T[lig]]

    for i in range(len(T)):
        if i != lig:
            coef = T[i][col]
            T[i] = [T[i][j] - coef * T[lig][j] for j in range(len(T[i]))]

    base[lig] = col


# ---------------------------------------------------------------------
# Lit la solution dans un tableau :
#   une variable en base vaut la valeur de b sur sa ligne,
#   une variable hors base vaut 0
# ---------------------------------------------------------------------
def lire_solution(T, base, n):
    x = [Fraction(0)] * n
    for i in range(len(base)):
        if base[i] <= n:                 # on ignore les variables d'écart
            x[base[i] - 1] = T[i][0]     # xj est rangé à l'indice j-1 de la liste x
    return x


# ---------------------------------------------------------------------
# Le simplexe :  max c.x  avec  A x <= b  et  x >= 0
# Renvoie : la liste des solutions optimales et le tableau final
# ---------------------------------------------------------------------
def simplex(c, A, b):
    n = len(c)                           # nombre de variables du problème
    m = len(A)                           # nombre de contraintes

    # --- Construction du tableau de départ ---
    # chaque contrainte devient : [b | coefficients de A | variables d'écart]
    # la variable d'écart de la contrainte i, x(n+1+i), vaut 1 sur sa ligne
    T = []
    for i in range(m):
        ligne = [b[i]] + A[i] + [Fraction(0)] * m
        ligne[n + 1 + i] = Fraction(1)
        T.append(ligne)

    # ligne f : 0 dans la case b, les coefficients de f tels quels, puis des 0
    T.append([Fraction(0)] + c + [Fraction(0)] * m)

    # au départ, ce sont les variables d'écart x(n+1)..x(n+m) qui sont en base
    base = [n + 1 + i for i in range(m)]

    # --- Itérations ---
    etape = 0
    while True:
        print("Tableau", etape)
        afficher(T, base, n)

        # 1) Variable entrante : plus grande valeur de la ligne f
        #    (">=" pour prendre la dernière colonne en cas d'égalité)
        f = T[-1]
        col = 1
        for j in range(1, n + 1):        # colonnes x1..xn
            if f[j] >= f[col]:
                col = j

        # si la plus grande valeur est <= 0, on a fini
        if f[col] <= 0:
            break

        # 2) Variable sortante
        lig = ligne_sortante(T, col)
        if lig == -1:
            print("Problème non borné (pas de solution finie).")
            return [], T

        # 3) Pivot
        pivoter(T, base, lig, col)
        etape += 1

    # --- Solution(s) optimale(s) ---
    solutions = [lire_solution(T, base, n)]

    # Une variable hors base avec 0 dans la ligne f peut entrer sans changer
    # la valeur de f : on fait ce pivot pour trouver l'autre solution.
    # On travaille sur une copie pour garder le tableau final intact.
    for j in range(1, n + m + 1):        # toutes les colonnes de variables
        if j not in base and T[-1][j] == 0:
            lig = ligne_sortante(T, j)
            if lig == -1:
                continue
            T2 = [ligne[:] for ligne in T]
            base2 = base[:]
            pivoter(T2, base2, lig, j)
            x = lire_solution(T2, base2, n)
            if x not in solutions:       # on n'affiche pas deux fois la même
                print(f"x{j} est hors base avec 0 dans f -> autre solution optimale :")
                afficher(T2, base2, n)
                solutions.append(x)

    return solutions, T


# ---------------------------------------------------------------------
# Lit une ligne de nombres séparés par des espaces (ex : "2 3 20")
# et redemande tant qu'il n'y a pas le bon nombre de valeurs.
# Accepte les entiers, les décimaux (0.5) et les fractions (1/2).
# ---------------------------------------------------------------------
def lire_nombres(message, combien):
    while True:
        valeurs = input(message).split()
        if len(valeurs) == combien:
            return [Fraction(v) for v in valeurs]
        print(f"  -> il faut {combien} nombres séparés par des espaces, recommence.")


# =====================================================================
#                          PROGRAMME PRINCIPAL
# =====================================================================

# --- Guide pour l'utilisateur ---
print("""
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
Fractions (1/2) et décimaux (0.5) acceptés.
=====================================================
""")

# --- Saisie du problème ---
type_pb = ""
while type_pb not in ("max", "min"):
    type_pb = input("Type (max ou min) : ").strip().lower()

v = "x" if type_pb == "max" else "y"            # nom des variables
signe = "<=" if type_pb == "max" else ">="      # sens des contraintes

n = int(input("Nombre de variables : "))
m = int(input("Nombre de contraintes : "))

noms = " ".join(f"{v}{j+1}" for j in range(n))   # ex : "x1 x2"
c = lire_nombres(f"f  ({noms}) : ", n)

A = []
b = []
for i in range(m):
    ligne = lire_nombres(f"contrainte {i+1}  ({noms} b) : ", n + 1)
    A.append(ligne[:n])          # les n premiers nombres : les coefficients
    b.append(ligne[n])           # le dernier nombre : le second membre b
print()

# --- Cas MAX : simplexe directement ---
if type_pb == "max":
    solutions, T = simplex(c, A, b)
    for k, x in enumerate(solutions):
        print(f"Solution optimale {k+1} :")
        for j in range(n):
            print(f"  x{j+1} = {x[j]}")
        print(f"  f max = {sum(c[j] * x[j] for j in range(n))}")

# --- Cas MIN : on passe par le dual ---
else:
    # Dual : max b.x  avec  (A transposée) x <= c
    # A transposée : la ligne j contient les coefficients de yj
    # dans chaque contrainte du primal
    tA = [[A[i][j] for i in range(m)] for j in range(n)]

    # on affiche le dual pour pouvoir le comparer à celui du cours
    print("Primal : min f(y) = " + " + ".join(f"{c[j]}y{j+1}" for j in range(n)))
    for i in range(m):
        print("         " + " + ".join(f"{A[i][j]}y{j+1}" for j in range(n)) + f" >= {b[i]}")
    print("Dual   : max f(x) = " + " + ".join(f"{b[i]}x{i+1}" for i in range(m)))
    for j in range(n):
        print("         " + " + ".join(f"{tA[j][i]}x{i+1}" for i in range(m)) + f" <= {c[j]}")
    print()

    # on résout le dual (les rôles de b et c sont échangés)
    solutions, T = simplex(b, tA, c)

    if solutions:
        # solution du dual : lue dans la colonne b, comme d'habitude
        x = solutions[0]
        print("Solution du dual :")
        for i in range(m):
            print(f"  x{i+1} = {x[i]}")
        print(f"  f max = {sum(b[i] * x[i] for i in range(m))}")

        # solution du primal : lue dans la ligne f du dernier tableau,
        # sous les colonnes des variables d'écart, en changeant le signe.
        # (la variable d'écart de la contrainte j du dual est x(m+j+1),
        #  elle se trouve donc dans la colonne m+j+1)
        y = [-T[-1][m + 1 + j] for j in range(n)]
        print("Solution du primal (ligne f, colonnes d'écart, signe changé) :")
        for j in range(n):
            print(f"  y{j+1} = {y[j]}")
        print(f"  f min = {sum(c[j] * y[j] for j in range(n))}")
