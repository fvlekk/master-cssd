// =====================================================================
//   Interface web du simplexe (la logique de calcul est dans simplex.js)
// =====================================================================

const $ = (sel) => document.querySelector(sel);
const MAX_N = 8;
const MAX_M = 8;

const EXEMPLES = [
  { type: "max", c: ["3", "3"], A: [["2", "3"], ["1", "1"]], b: ["20", "7"] },
  { type: "min", c: ["2", "3"], A: [["1", "2"], ["2", "1"]], b: ["10", "11"] },
];

const etat = {
  type: "max", n: 2, m: 2,
  c: [], A: [], b: [],
  resultat: null,
  pasAPas: false,
  position: 0,
};

// ---------------------------------------------------------------------
// Petits utilitaires d'affichage
// ---------------------------------------------------------------------
const echapper = (s) => String(s).replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
const ind = (lettre, j) => `${lettre}<sub>${j + 1}</sub>`;   // j = indice dans une liste (0 -> x1)
const xcol = (k) => `x<sub>${k}</sub>`;                      // k = numéro de colonne (1 -> x1)

function approx(fr) {
  if (fr.den === 1n) return "";
  return `<span class="approx">≈ ${fr.toNumber().toLocaleString("fr-FR", { maximumFractionDigits: 4 })}</span>`;
}

// "2y1 + 3y2" en évitant "+ -3" et les coefficients nuls
function expression(coefs, lettre) {
  let s = "";
  coefs.forEach((v, j) => {
    if (v.estNul()) return;
    const absV = v.signe() < 0 ? v.neg() : v;
    const coef = absV.eq(new Fraction(1)) ? "" : absV.toString();
    if (s === "") s = (v.signe() < 0 ? "-" : "") + coef + lettre + (j + 1);
    else s += (v.signe() < 0 ? " - " : " + ") + coef + lettre + (j + 1);
  });
  return s || "0";
}

// ---------------------------------------------------------------------
// Saisie du problème
// ---------------------------------------------------------------------
function ajusterTailles() {
  const vide = () => "";
  etat.c = Array.from({ length: etat.n }, (_, j) => etat.c[j] ?? "");
  etat.A = Array.from({ length: etat.m }, (_, i) =>
    Array.from({ length: etat.n }, (_, j) => (etat.A[i] && etat.A[i][j]) ?? vide()));
  etat.b = Array.from({ length: etat.m }, (_, i) => etat.b[i] ?? "");
}

function champ(cle, valeur, titre) {
  return `<input inputmode="decimal" autocomplete="off" data-cle="${cle}" value="${echapper(valeur)}" aria-label="${titre}" placeholder="0">`;
}

function afficherSaisie() {
  ajusterTailles();
  const v = etat.type === "max" ? "x" : "y";
  const signe = etat.type === "max" ? "≤" : "≥";

  let html = `<table class="grille"><tbody><tr><td class="nom">${etat.type} f(${v}) =</td>`;
  for (let j = 0; j < etat.n; j++) {
    if (j) html += `<td class="op">+</td>`;
    html += `<td>${champ(`c-${j}`, etat.c[j], `coefficient de ${v}${j + 1} dans f`)}<span class="var">${ind(v, j)}</span></td>`;
  }
  html += `</tr>`;
  for (let i = 0; i < etat.m; i++) {
    html += `<tr><td class="nom">contrainte ${i + 1}</td>`;
    for (let j = 0; j < etat.n; j++) {
      if (j) html += `<td class="op">+</td>`;
      html += `<td>${champ(`A-${i}-${j}`, etat.A[i][j], `contrainte ${i + 1}, coefficient de ${v}${j + 1}`)}<span class="var">${ind(v, j)}</span></td>`;
    }
    html += `<td class="sens">${signe}</td><td>${champ(`b-${i}`, etat.b[i], `second membre de la contrainte ${i + 1}`)}</td></tr>`;
  }
  html += `</tbody></table>`;
  $("#saisie").innerHTML = html;

  $("#n").textContent = etat.n;
  $("#m").textContent = etat.m;
  document.querySelectorAll("#type button").forEach((b) => b.classList.toggle("actif", b.dataset.type === etat.type));
}

$("#saisie").addEventListener("input", (e) => {
  const cle = e.target.dataset.cle;
  if (!cle) return;
  e.target.classList.remove("invalide");
  const [nom, i, j] = cle.split("-");
  if (nom === "c") etat.c[+i] = e.target.value;
  else if (nom === "b") etat.b[+i] = e.target.value;
  else etat.A[+i][+j] = e.target.value;
});

$("#saisie").addEventListener("keydown", (e) => {
  if (e.key === "Enter") resoudreProbleme();
});

document.querySelectorAll("#type button").forEach((bouton) =>
  bouton.addEventListener("click", () => { etat.type = bouton.dataset.type; afficherSaisie(); }));

document.querySelectorAll(".compteur").forEach((cpt) =>
  cpt.addEventListener("click", (e) => {
    const delta = +(e.target.dataset.delta || 0);
    if (!delta) return;
    const cible = cpt.dataset.cible;
    const max = cible === "n" ? MAX_N : MAX_M;
    etat[cible] = Math.min(max, Math.max(1, etat[cible] + delta));
    afficherSaisie();
  }));

document.querySelectorAll("[data-exemple]").forEach((bouton) =>
  bouton.addEventListener("click", () => chargerExemple(+bouton.dataset.exemple)));

$("#vider").addEventListener("click", () => {
  etat.c = []; etat.A = []; etat.b = [];
  afficherSaisie();
  $("#erreur").classList.add("cache");
  $("#resultats").innerHTML = "";
});

$("#resoudre").addEventListener("click", resoudreProbleme);

function chargerExemple(k) {
  const ex = EXEMPLES[k];
  etat.type = ex.type;
  etat.n = ex.c.length;
  etat.m = ex.A.length;
  etat.c = ex.c.slice();
  etat.A = ex.A.map((l) => l.slice());
  etat.b = ex.b.slice();
  afficherSaisie();
  resoudreProbleme();
}

// ---------------------------------------------------------------------
// Lecture + vérification, puis résolution
// ---------------------------------------------------------------------
function erreur(message) {
  const el = $("#erreur");
  el.textContent = message;
  el.classList.remove("cache");
}

function resoudreProbleme() {
  $("#erreur").classList.add("cache");
  let invalide = false;
  const lire = (texte, cle) => {
    try {
      return texte.trim() === "" ? new Fraction(0) : Fraction.lire(texte);
    } catch {
      invalide = true;
      document.querySelector(`[data-cle="${cle}"]`).classList.add("invalide");
      return new Fraction(0);
    }
  };
  const c = etat.c.map((v, j) => lire(v, `c-${j}`));
  const A = etat.A.map((l, i) => l.map((v, j) => lire(v, `A-${i}-${j}`)));
  const b = etat.b.map((v, i) => lire(v, `b-${i}`));

  if (invalide) return erreur("Certaines cases ne contiennent pas un nombre valide (exemples acceptés : 3, -2, 0.5, 1/2).");

  // le tableau de départ (écarts en base) n'est réalisable que si son second membre est >= 0
  if (etat.type === "max" && b.some((v) => v.signe() < 0)) {
    b.forEach((v, i) => v.signe() < 0 && document.querySelector(`[data-cle="b-${i}"]`).classList.add("invalide"));
    return erreur("En max, les seconds membres b doivent être ≥ 0 : sinon le tableau de départ (variables d'écart en base) n'est pas réalisable.");
  }
  if (etat.type === "min" && c.some((v) => v.signe() < 0)) {
    c.forEach((v, j) => v.signe() < 0 && document.querySelector(`[data-cle="c-${j}"]`).classList.add("invalide"));
    return erreur("En min, les coefficients de f doivent être ≥ 0 : ils deviennent le second membre du dual.");
  }

  etat.resultat = resoudre(etat.type, c, A, b);
  etat.position = 0;
  afficherResultats();
}

// ---------------------------------------------------------------------
// Résultats
// ---------------------------------------------------------------------
function pastilles(lettre, valeurs) {
  return `<div class="pastilles">${valeurs.map((v, j) =>
    `<span class="pastille">${lettre}${j + 1} = ${v}</span>`).join("")}</div>`;
}

function carteResultat(res) {
  const s = res.simplexe;
  if (s.statut === "non_borne") {
    return `<section class="carte"><div class="bandeau"><div class="tuile ko"><span class="etiquette">Résultat</span>
      <div class="valeur">Problème non borné</div></div></div>
      <p class="note">${res.type === "max"
        ? "f peut augmenter sans limite : pas de solution finie."
        : "Le dual est non borné, donc le primal (min) n'a pas de solution réalisable."}</p></section>`;
  }
  if (s.statut === "trop_etapes") {
    return `<section class="carte"><div class="bandeau"><div class="tuile ko"><span class="etiquette">Résultat</span>
      <div class="valeur">Arrêt après ${s.etapes.length - 1} pivots</div></div></div>
      <p class="note">L'algorithme semble boucler (cyclage sur un tableau dégénéré).</p></section>`;
  }

  if (res.type === "max") {
    const plusieurs = s.solutions.length > 1;
    return `<section class="carte"><div class="bandeau">
      <div class="tuile ok"><span class="etiquette">f max</span><div class="valeur">${s.valeurs[0]}${approx(s.valeurs[0])}</div></div>
      ${s.solutions.map((x, k) => `<div class="tuile"><span class="etiquette">Solution optimale${plusieurs ? " " + (k + 1) : ""}</span>${pastilles("x", x)}</div>`).join("")}
      </div>
      ${plusieurs ? `<p class="note">Plusieurs solutions optimales : une variable hors base a 0 dans la ligne f du tableau final.
        Tout point du segment entre ces solutions donne aussi f = ${s.valeurs[0]}.</p>` : ""}
      <p class="note">${s.etapes.length - 1} pivot${s.etapes.length > 2 ? "s" : ""} · ${s.etapes.length} tableau${s.etapes.length > 1 ? "x" : ""}</p>
    </section>`;
  }

  return `<section class="carte"><div class="bandeau">
    <div class="tuile ok"><span class="etiquette">f min (primal)</span><div class="valeur">${res.fMin}${approx(res.fMin)}</div></div>
    <div class="tuile"><span class="etiquette">Solution du primal</span>${pastilles("y", res.y)}</div>
    <div class="tuile"><span class="etiquette">Solution du dual · f max = ${res.fDual}</span>${pastilles("x", res.xDual)}</div>
    </div>
    <p class="note">Dualité forte : f min du primal = f max du dual = ${res.fMin}. Les yⱼ se lisent dans la ligne f du dernier tableau, sous les variables d'écart, en changeant le signe.</p>
  </section>`;
}

function carteDual(res) {
  if (res.type !== "min") return "";
  const { n, m, c, A, b, tA } = res;
  const primal = [`min f(y) = ${expression(c, "y")}`,
    ...A.map((l, i) => `      ${expression(l, "y")} ≥ ${b[i]}`),
    `      y ≥ 0`].join("\n");
  const dual = [`max f(x) = ${expression(b, "x")}`,
    ...tA.map((l, j) => `      ${expression(l, "x")} ≤ ${c[j]}`),
    `      x ≥ 0`].join("\n");
  return `<section class="carte">
    <div class="carte-titre"><h2>Primal et dual</h2></div>
    <div class="deux-col">
      <div><span class="etiquette">Primal (${n} variables, ${m} contraintes ≥)</span><pre class="probleme">${echapper(primal)}</pre></div>
      <div><span class="etiquette">Dual (${m} variables, ${n} contraintes ≤) — résolu par le simplexe</span><pre class="probleme">${echapper(dual)}</pre></div>
    </div>
    <p class="fleche-dual">Le dual échange les rôles : les b du primal deviennent les coefficients de f, les c deviennent les seconds membres, et la matrice est transposée.
      Variables d'écart du dual : ${Array.from({ length: n }, (_, j) => ind("x", m + j)).join(", ")} (une par contrainte, donc une par yⱼ).</p>
  </section>`;
}

// ---------------------------------------------------------------------
// Un tableau du simplexe
// ---------------------------------------------------------------------
function tableau(T, base, n, opts = {}) {
  const m = T.length - 1;
  const { col = null, lig = null, rapports = null, lecture = [] } = opts;
  const classe = (j) => [j > n ? "ecart" : "", j === col ? "col-in" : ""].join(" ");

  let html = `<div class="defile"><table class="tab"><thead><tr><th class="coin">base</th><th class="b">b</th>`;
  for (let j = 1; j <= n + m; j++) html += `<th class="${classe(j)}">${xcol(j)}</th>`;
  if (rapports) html += `<th class="rapport">b ÷ ${xcol(col)}</th>`;
  html += `</tr></thead><tbody>`;

  // rapport minimal (le premier en cas d'égalité, comme ligne_sortante)
  for (let i = 0; i < m; i++) {
    html += `<tr class="${i === lig ? "lig-out" : ""}"><td class="base">${xcol(base[i])}</td><td class="b">${T[i][0]}</td>`;
    for (let j = 1; j <= n + m; j++) {
      const pivot = i === lig && j === col;
      html += `<td class="${classe(j)}${pivot ? " pivot" : ""}">${T[i][j]}</td>`;
    }
    if (rapports) {
      const r = rapports[i];
      html += r
        ? `<td class="rapport${i === lig ? " min" : ""}">${T[i][0]} ÷ ${T[i][col]} = ${r}${i === lig ? " ← min" : ""}</td>`
        : `<td class="rapport">—</td>`;
    }
    html += `</tr>`;
  }
  html += `<tr class="f"><td class="base">f</td><td class="b">${T[m][0].neg()}</td>`;
  for (let j = 1; j <= n + m; j++) {
    html += `<td class="${classe(j)}${lecture.includes(j) ? " lecture" : ""}">${T[m][j]}</td>`;
  }
  if (rapports) html += `<td class="rapport"></td>`;
  html += `</tr></tbody></table></div>`;
  return html;
}

// opérations sur les lignes faites par pivoter()
function operations(T, base, lig, col) {
  const m = T.length - 1;
  const L = (i) => `L(x${base[i]})`;
  const ops = [`${L(lig)} ← ${L(lig)} ÷ ${T[lig][col]}`];
  for (let i = 0; i <= m; i++) {
    if (i === lig || T[i][col].estNul()) continue;
    const coef = T[i][col];
    const nom = i === m ? "f" : L(i);
    const terme = coef.signe() > 0 ? `− ${coef}` : `+ ${coef.neg()}`;
    ops.push(`${nom} ← ${nom} ${terme} × ${L(lig)}`);
  }
  return ops.join(" &nbsp;·&nbsp; ");
}

function etapes(res) {
  const s = res.simplexe;
  const n = s.n;
  const derniere = s.etapes.length - 1;
  const liste = [];

  s.etapes.forEach((e, k) => {
    const f = e.T.at(-1);
    let badge = "";
    const lignes = [];
    let lecture = [];

    if (e.entrante !== null) {
      const vmax = f[e.entrante];
      const egal = f.slice(1, n + 1).filter((v) => v.eq(vmax)).length > 1;
      lignes.push(`<li>Variable entrante : <span class="var-nom">${xcol(e.entrante)}</span> — plus grande valeur de la ligne f parmi ${ind("x", 0)}…${ind("x", n - 1)} (${vmax})${egal ? ", égalité : on prend la dernière" : ""}.</li>`);
      if (e.sortante !== null) {
        lignes.push(`<li>Variable sortante : <span class="var-nom">${xcol(e.base[e.sortante])}</span> — plus petit rapport b ÷ coefficient (${e.rapports[e.sortante]}). Pivot = <strong>${e.T[e.sortante][e.entrante]}</strong>.</li>`);
        lignes.push(`<li class="ops">${operations(e.T, e.base, e.sortante, e.entrante)}</li>`);
      } else {
        badge = `<span class="badge ko">non borné</span>`;
        lignes.push(`<li>Aucun coefficient &gt; 0 dans la colonne ${xcol(e.entrante)} : pas de variable sortante, le problème est <strong>non borné</strong>.</li>`);
      }
    } else {
      badge = `<span class="badge ok">optimal</span>`;
      lignes.push(`<li>Toutes les valeurs de la ligne f sur ${ind("x", 0)}…${ind("x", n - 1)} sont ≤ 0 : le tableau est <strong>optimal</strong>.</li>`);
      const x = s.solutions[0];
      lignes.push(`<li>Lecture : variables en base = valeur de b, hors base = 0 → ${x.map((v, j) => `${ind("x", j)} = ${v}`).join(", ")} ; f = ${e.T.at(-1)[0].neg()}.</li>`);
      if (res.type === "min") {
        lecture = Array.from({ length: res.n }, (_, j) => s.m + 1 + j);
        lignes.push(`<li>Primal : ${res.y.map((v, j) => `${ind("y", j)} = −(${e.T.at(-1)[s.m + 1 + j]}) = <strong>${v}</strong>`).join(", ")} (ligne f sous ${lecture.map(xcol).join(", ")}).</li>`);
      }
      s.alternatives.forEach((a) =>
        lignes.push(`<li>${xcol(a.col)} est hors base avec 0 dans f → il existe une autre solution optimale (tableau suivant).</li>`));
    }

    liste.push(`<div class="etape">
      <div class="etape-titre"><h3>Tableau ${k}</h3>${badge}</div>
      ${tableau(e.T, e.base, n, { col: e.entrante, lig: e.sortante, rapports: e.entrante !== null ? e.rapports : null, lecture })}
      <ul class="explication">${lignes.join("")}</ul>
    </div>`);
  });

  s.alternatives.forEach((a) => {
    liste.push(`<div class="etape">
      <div class="etape-titre"><h3>Autre solution optimale</h3><span class="badge ok">optimal</span></div>
      ${tableau(a.T, a.base, n)}
      <ul class="explication">
        <li>On fait entrer ${xcol(a.col)} (0 dans f) à la place de ${xcol(a.sortante)} : la valeur de f ne change pas.</li>
        <li>Solution : ${a.x.map((v, j) => `${ind("x", j)} = ${v}`).join(", ")}.</li>
      </ul>
    </div>`);
  });

  return liste;
}

function carteTableaux(res) {
  const liste = etapes(res);
  const total = liste.length;
  etat.position = Math.min(etat.position, total - 1);
  const visibles = etat.pasAPas ? [liste[etat.position]] : liste;

  const controle = etat.pasAPas
    ? `<div class="controle">
         <button id="prec" ${etat.position === 0 ? "disabled" : ""}>◀ Précédent</button>
         <span class="position">${etat.position + 1} / ${total}</span>
         <button id="suiv" ${etat.position === total - 1 ? "disabled" : ""}>Suivant ▶</button>
         <button id="mode">Tout afficher</button>
       </div>`
    : `<div class="controle"><button id="mode">Pas à pas</button></div>`;

  return `<section class="carte" id="carte-tableaux">
    <div class="carte-titre"><h2>Tableaux du simplexe${res.type === "min" ? " (sur le dual)" : ""}</h2>${controle}</div>
    ${visibles.join("")}
  </section>`;
}

// ---------------------------------------------------------------------
function afficherResultats() {
  const res = etat.resultat;
  if (!res) return;
  $("#resultats").innerHTML = carteResultat(res) + carteDual(res) + carteTableaux(res);
}

$("#resultats").addEventListener("click", (e) => {
  const id = e.target.id;
  if (id === "mode") { etat.pasAPas = !etat.pasAPas; etat.position = 0; }
  else if (id === "prec") etat.position--;
  else if (id === "suiv") etat.position++;
  else return;
  afficherResultats();
  if (etat.pasAPas) $("#carte-tableaux").scrollIntoView({ block: "nearest", behavior: "smooth" });
});

// ---------------------------------------------------------------------
// Onglets + code Python
// ---------------------------------------------------------------------
document.querySelectorAll(".onglet").forEach((onglet) =>
  onglet.addEventListener("click", () => {
    document.querySelectorAll(".onglet").forEach((o) => o.classList.toggle("actif", o === onglet));
    document.querySelectorAll(".panneau").forEach((p) => p.classList.toggle("cache", p.id !== onglet.dataset.onglet));
    if (onglet.dataset.onglet === "code") chargerCode();
  }));

// coloration simple : commentaires, chaînes, mots-clés, nombres
const LANGAGES = {
  python: {
    fichier: "simplex.py",
    motif: /(?<com>#[^\n]*)|(?<str>"""[\s\S]*?"""|[fr]?"(?:[^"\\\n]|\\.)*"|[fr]?'(?:[^'\\\n]|\\.)*')|\b(?<id>[A-Za-z_]\w*)\b|\b(?<num>\d+)\b/g,
    mots: new Set("def return for in if else elif while break continue not and or import from as True False None lambda pass class try except with is".split(" ")),
  },
};

function colorer(code, langage) {
  const { motif, mots } = LANGAGES[langage];
  motif.lastIndex = 0;
  let html = "", dernier = 0, apresDef = false, m;
  while ((m = motif.exec(code))) {
    html += echapper(code.slice(dernier, m.index));
    dernier = motif.lastIndex;
    const t = echapper(m[0]);
    const g = m.groups;
    if (g.com) html += `<span class="tk-com">${t}</span>`;
    else if (g.str) html += `<span class="tk-str">${t}</span>`;
    else if (g.id) {
      if (apresDef) { html += `<span class="tk-def">${t}</span>`; apresDef = false; }
      else if (mots.has(g.id)) { html += `<span class="tk-mot">${t}</span>`; apresDef = g.id === "def"; }
      else html += t;
    } else html += `<span class="tk-num">${t}</span>`;
  }
  return html + echapper(code.slice(dernier));
}

let codeCharge = false;
function chargerCode() {
  if (codeCharge) return;
  codeCharge = true;
  for (const [langage, { fichier }] of Object.entries(LANGAGES)) {
    const cible = $(`#source-${langage}`);
    fetch(fichier)
      .then((r) => { if (!r.ok) throw new Error(); return r.text(); })
      .then((texte) => { cible.innerHTML = colorer(texte, langage); })
      .catch(() => { cible.textContent = `Impossible de charger ${fichier} (ouvre le site via un serveur, pas en double-cliquant le fichier).`; });
  }
}


// ---------------------------------------------------------------------
// au démarrage : exemple donné dans l'URL (#ex=2), sinon le premier
const exUrl = location.hash.match(/ex=(\d+)/);
chargerExemple(exUrl && EXEMPLES[+exUrl[1] - 1] ? +exUrl[1] - 1 : 0);

// ouvre directement un onglet si l'URL le demande (#code, #methode, #apropos)
const ongletUrl = document.querySelector(`.onglet[data-onglet="${location.hash.slice(1)}"]`);
if (ongletUrl) ongletUrl.click();
