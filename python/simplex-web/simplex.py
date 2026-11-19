# algorithme du simplexe
# max : simplexe direct
# min : passage par le dual

from fractions import Fraction


# affiche le tableau avec la base actuelle
def afficher(T,base,n):
    m = len(T)-1
    noms = ["x"+str(i) for i in range(1,n+m+1)]

    print("  base       b" + "".join(f"{x:>8}" for x in noms))

    for i in range(m):
        print(f"{'x'+str(base[i]):>6}{str(T[i][0]):>8}" + "".join(f"{x:>8}" for x in map(str,T[i][1:])))

    # dans la dernière ligne, la première valeur correspond à -f
    print(f"{'f':>6}{str(-T[-1][0]):>8}" + "".join(f"{x:>8}" for x in map(str,T[-1][1:])))
    print()


# cherche la ligne qui doit sortir de la base
def ligne_sortante(T,col):
    ligne = -1

    for i in range(len(T)-1):
        if T[i][col] > 0:
            rapport = T[i][0]/T[i][col]

            if ligne == -1 or rapport < T[ligne][0]/T[ligne][col]:
                ligne = i

    return ligne


# effectue le pivot sur une case du tableau
def pivoter(T,base,lig,col):
    pivot = T[lig][col]

    # on met le pivot à 1
    T[lig] = [x/pivot for x in T[lig]]

    # on met des 0 dans le reste de la colonne
    for i in range(len(T)):
        if i != lig:
            coef = T[i][col]
            T[i] = [T[i][j]-coef*T[lig][j]
                    for j in range(len(T[i]))]

    base[lig] = col


# récupère les valeurs des variables à partir du tableau final
def lire_solution(T,base,n):
    solution = [Fraction(0)]*n

    for i in range(len(base)):
        if base[i] <= n:
            solution[base[i]-1] = T[i][0]

    return solution


# algorithme principal du simplexe
def simplex(c,A,b):
    n = len(c)
    m = len(A)

    # création du premier tableau
    T = []

    for i in range(m):
        ligne = [b[i]]+A[i]+[Fraction(0)]*m

        # ajout de la variable d'écart
        ligne[n+1+i] = Fraction(1)
        T.append(ligne)

    T.append([Fraction(0)]+c+[Fraction(0)]*m)

    # au début, les variables d'écart sont dans la base
    base = [n+1+i for i in range(m)]

    etape = 0

    while True:
        print("Tableau",etape)
        afficher(T,base,n)

        # on cherche la variable qui entre dans la base
        f = T[-1]
        col = 1

        for j in range(1,n+1):
            if f[j] >= f[col]:
                col = j

        # si aucun coefficient n'est positif, on a terminé
        if f[col] <= 0:
            break

        # recherche de la variable qui sort
        lig = ligne_sortante(T,col)

        if lig == -1:
            print("Problème non borné.")
            return [],T

        pivoter(T,base,lig,col)
        etape += 1

    # on récupère la première solution optimale
    solutions = [lire_solution(T,base,n)]

    # vérifie s'il existe une autre solution optimale
    for j in range(1,n+m+1):
        if j not in base and T[-1][j] == 0:
            lig = ligne_sortante(T,j)

            if lig == -1:
                continue

            T2 = [ligne.copy() for ligne in T]
            base2 = base.copy()

            pivoter(T2,base2,lig,j)

            x = lire_solution(T2,base2,n)

            if x not in solutions:
                print("Autre solution optimale :")
                afficher(T2,base2,n)
                solutions.append(x)

    return solutions,T


# lit les nombres entrés par l'utilisateur
def lire_nombres(message,nombre):
    while True:
        valeurs = input(message).split()

        if len(valeurs) == nombre:
            return [Fraction(x) for x in valeurs]

        print("Il faut",nombre,"valeurs.")


print("""
=============================
       ALGORITHME SIMPLEXE
=============================

max : contraintes <=
min : contraintes >=

Les variables sont >= 0.

Exemple de saisie :

Type (max ou min) : max
Nombre de variables : 2
Nombre de contraintes : 2
f (x1 x2) : 3 3
contrainte 1 (x1 x2 b) : 2 3 20
contrainte 2 (x1 x2 b) : 1 1 7

Pour une variable absente, mettre 0.
Les fractions comme 1/2 sont acceptées.
=============================
""")


# demande le type de problème
type = ""

while type not in ("max","min"):
    type = input("Type (max ou min) : ").strip().lower()


v = "x" if type == "max" else "y"

n = int(input("Nombre de variables : "))
m = int(input("Nombre de contraintes : "))

noms = " ".join(f"{v}{i+1}" for i in range(n))

c = lire_nombres("f ("+noms+") : ",n)

A = []
b = []

# lecture des contraintes
for i in range(m):
    ligne = lire_nombres(
        "contrainte "+str(i+1)+" ("+noms+" b) : ",
        n+1
    )

    A.append(ligne[:n])
    b.append(ligne[n])

print()


if type == "max":

    # pour un problème max, on applique directement le simplexe
    solutions,T = simplex(c,A,b)

    for k,x in enumerate(solutions):
        print("Solution optimale",k+1,":")

        for j in range(n):
            print(" x"+str(j+1),"=",x[j])

        valeur = sum(c[j]*x[j] for j in range(n))
        print(" f max =",valeur)


else:

    # pour un problème min, on construit d'abord le dual
    tA = [[A[i][j] for i in range(m)] for j in range(n)]

    print(
        "Primal : min f(y) = "
        + " + ".join(f"{c[j]}y{j+1}" for j in range(n))
    )

    for i in range(m):
        print(
            "         "
            + " + ".join(
                f"{A[i][j]}y{j+1}" for j in range(n)
            )
            + f" >= {b[i]}"
        )

    print(
        "Dual : max f(x) = "
        + " + ".join(f"{b[i]}x{i+1}" for i in range(m))
    )

    for j in range(n):
        print(
            "         "
            + " + ".join(
                f"{tA[j][i]}x{i+1}" for i in range(m)
            )
            + f" <= {c[j]}"
        )

    print()

    # on applique le simplexe au problème dual
    solutions,T = simplex(b,tA,c)

    if solutions:

        x = solutions[0]

        print("Solution du dual :")

        for i in range(m):
            print(" x"+str(i+1),"=",x[i])

        valeur = sum(b[i]*x[i] for i in range(m))
        print(" f max =",valeur)

        # on retrouve la solution du primal dans le dernier tableau
        y = [-T[-1][m+1+j] for j in range(n)]

        print("Solution du primal :")

        for j in range(n):
            print(" y"+str(j+1),"=",y[j])

        valeur = sum(c[j]*y[j] for j in range(n))
        print(" f min =",valeur)
