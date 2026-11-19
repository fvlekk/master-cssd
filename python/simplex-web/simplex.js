// =====================================================================
//   ALGORITHME DU SIMPLEXE — portage JavaScript de simplex.py
// =====================================================================
// Mêmes fonctions, mêmes règles que le programme Python :
//   - variable entrante : la plus grande valeur de la ligne f
//     (colonnes des variables du problème seulement, égalité -> la dernière)
//   - variable sortante : le plus petit rapport b / coefficient (coef > 0)
//   - arrêt quand toutes ces valeurs de f sont <= 0
//   - variable hors base avec 0 dans f -> pivot de plus (autre solution)
// La seule différence : au lieu d'afficher avec print(), chaque tableau
// est enregistré pour être dessiné par l'interface.
// Disposition : b dans la colonne 0, puis la colonne j contient xj.
// =====================================================================

// ---------------------------------------------------------------------
// Fractions exactes (équivalent de fractions.Fraction en Python)
// ---------------------------------------------------------------------
function pgcd(a, b) {
  if (a < 0n) a = -a;
  if (b < 0n) b = -b;
  while (b !== 0n) [a, b] = [b, a % b];
  return a;
}

class Fraction {
  constructor(num, den = 1n) {
    num = BigInt(num);
    den = BigInt(den);
    if (den === 0n) throw new Error("division par zéro");
    if (den < 0n) { num = -num; den = -den; }
    const g = pgcd(num, den) || 1n;
    this.num = num / g;
    this.den = den / g;
  }

  // Accepte "3", "-2", "0.5", "0,5" et "1/2" (comme Fraction("1/2") en Python)
  static lire(texte) {
    const s = String(texte).trim().replace(",", ".");
    let r = s.match(/^([+-]?\d+)\s*\/\s*(\d+)$/);
    if (r) return new Fraction(r[1], r[2]);
    r = s.match(/^([+-]?)(\d*)(?:\.(\d*))?$/);
    if (r && (r[2] || r[3])) {
      const decimales = r[3] || "";
      const num = BigInt((r[2] || "0") + decimales) * (r[1] === "-" ? -1n : 1n);
      return new Fraction(num, 10n ** BigInt(decimales.length));
    }
    throw new Error(`« ${texte} » n'est pas un nombre`);
  }

  add(f) { return new Fraction(this.num * f.den + f.num * this.den, this.den * f.den); }
  sub(f) { return new Fraction(this.num * f.den - f.num * this.den, this.den * f.den); }
  mul(f) { return new Fraction(this.num * f.num, this.den * f.den); }
  div(f) { return new Fraction(this.num * f.den, this.den * f.num); }
  neg()  { return new Fraction(-this.num, this.den); }

  cmp(f) {
    const d = this.num * f.den - f.num * this.den;
    return d > 0n ? 1 : d < 0n ? -1 : 0;
  }
  eq(f) { return this.num === f.num && this.den === f.den; }
  estNul() { return this.num === 0n; }
  signe() { return this.num > 0n ? 1 : this.num < 0n ? -1 : 0; }

  toNumber() { return Number(this.num) / Number(this.den); }
  toString() { return this.den === 1n ? String(this.num) : `${this.num}/${this.den}`; }
}

const ZERO = new Fraction(0);
const UN = new Fraction(1);

const copier = (T) => T.map((ligne) => ligne.slice());

// ---------------------------------------------------------------------
// Ligne de la variable sortante pour la colonne "col"
// = plus petit rapport b / coefficient (coefficient > 0), -1 si aucun
// ---------------------------------------------------------------------
function ligne_sortante(T, col) {
  let lig = -1;
  for (let i = 0; i < T.length - 1; i++) {          // pas la ligne f
    if (T[i][col].signe() > 0) {
      const rapport = T[i][0].div(T[i][col]);
      if (lig === -1 || rapport.cmp(T[lig][0].div(T[lig][col])) < 0) lig = i;
    }
  }
  return lig;
}

// ---------------------------------------------------------------------
// Pivot sur la case (lig, col)
// ---------------------------------------------------------------------
function pivoter(T, base, lig, col) {
  const pivot = T[lig][col];
  T[lig] = T[lig].map((v) => v.div(pivot));

  for (let i = 0; i < T.length; i++) {
    if (i !== lig) {
      const coef = T[i][col];
      T[i] = T[i].map((v, j) => v.sub(coef.mul(T[lig][j])));
    }
  }
  base[lig] = col;
}

// ---------------------------------------------------------------------
// Solution lue dans un tableau (variables en base = b, les autres = 0)
// ---------------------------------------------------------------------
function lire_solution(T, base, n) {
  const x = Array.from({ length: n }, () => ZERO);
  for (let i = 0; i < base.length; i++) {
    if (base[i] <= n) x[base[i] - 1] = T[i][0];   // on ignore les écarts
  }
  return x;
}

const memeSolution = (x, y) => x.every((v, j) => v.eq(y[j]));

// ---------------------------------------------------------------------
// Le simplexe : max c.x  avec  A x <= b  et  x >= 0
// Renvoie tout ce qu'il faut pour afficher les étapes.
// ---------------------------------------------------------------------
function simplex(c, A, b, maxEtapes = 200) {
  const n = c.length;
  const m = A.length;

  // --- Tableau de départ : [b | A | écarts], puis la ligne f ---
  const T = [];
  for (let i = 0; i < m; i++) {
    const ligne = [b[i], ...A[i], ...Array(m).fill(ZERO)];
    ligne[n + 1 + i] = UN;
    T.push(ligne);
  }
  T.push([ZERO, ...c, ...Array(m).fill(ZERO)]);

  // au départ, ce sont les variables d'écart x(n+1)..x(n+m) qui sont en base
  const base = Array.from({ length: m }, (_, i) => n + 1 + i);

  // --- Itérations ---
  const etapes = [];
  let statut = "optimal";
  while (true) {
    const etape = { T: copier(T), base: base.slice(), entrante: null, sortante: null, rapports: null };
    etapes.push(etape);

    // 1) Variable entrante : plus grande valeur de f (">=" -> la dernière)
    const f = T.at(-1);
    let col = 1;
    for (let j = 1; j <= n; j++) if (f[j].cmp(f[col]) >= 0) col = j;

    // si la plus grande valeur est <= 0, on a fini
    if (f[col].signe() <= 0) break;

    // 2) Variable sortante
    etape.entrante = col;
    etape.rapports = T.slice(0, -1).map((ligne) =>
      ligne[col].signe() > 0 ? ligne[0].div(ligne[col]) : null);
    const lig = ligne_sortante(T, col);
    if (lig === -1) { statut = "non_borne"; break; }
    etape.sortante = lig;

    // garde-fou (le programme Python n'en a pas : risque de boucle si cyclage)
    if (etapes.length > maxEtapes) { statut = "trop_etapes"; break; }

    // 3) Pivot
    pivoter(T, base, lig, col);
  }

  if (statut !== "optimal") return { n, m, etapes, statut, solutions: [], alternatives: [], T, base };

  // --- Solution(s) optimale(s) ---
  const solutions = [lire_solution(T, base, n)];
  const alternatives = [];

  // variable hors base avec 0 dans f -> autre solution optimale (sur une copie)
  for (let j = 1; j <= n + m; j++) {
    if (!base.includes(j) && T.at(-1)[j].estNul()) {
      const lig = ligne_sortante(T, j);
      if (lig === -1) continue;
      const T2 = copier(T);
      const base2 = base.slice();
      pivoter(T2, base2, lig, j);
      const x = lire_solution(T2, base2, n);
      if (!solutions.some((s) => memeSolution(s, x))) {
        alternatives.push({ col: j, lig, sortante: base[lig], T: T2, base: base2, x });
        solutions.push(x);
      }
    }
  }

  return { n, m, etapes, statut, solutions, alternatives, T, base };
}

// ---------------------------------------------------------------------
// Problème complet (max direct, ou min par le dual) — comme le
// "programme principal" de simplex.py
// ---------------------------------------------------------------------
function resoudre(type, c, A, b) {
  const n = c.length;
  const m = A.length;
  const somme = (u, v) => u.reduce((s, ui, k) => s.add(ui.mul(v[k])), ZERO);

  if (type === "max") {
    const r = simplex(c, A, b);
    r.valeurs = r.solutions.map((x) => somme(c, x));
    return { type, n, m, c, A, b, simplexe: r };
  }

  // Dual : max b.x  avec  (A transposée) x <= c
  const tA = Array.from({ length: n }, (_, j) => Array.from({ length: m }, (_, i) => A[i][j]));
  const r = simplex(b, tA, c);
  const res = { type, n, m, c, A, b, tA, simplexe: r };
  if (r.solutions.length) {
    res.xDual = r.solutions[0];
    res.fDual = somme(b, res.xDual);
    // primal : ligne f du dernier tableau, colonnes d'écart, signe changé
    res.y = Array.from({ length: n }, (_, j) => r.T.at(-1)[m + 1 + j].neg());
    res.fMin = somme(c, res.y);
  }
  return res;
}

if (typeof module !== "undefined") module.exports = { Fraction, simplex, resoudre, ligne_sortante, pivoter, lire_solution };
