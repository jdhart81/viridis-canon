# Pre-change diffs

No source or parity-policy target has been changed when this preview is written.

## Run-112 paper.tex

Source before SHA256: 14069a39834b357e2586cd08baaead6f747527f0264bb6cc6ee29373998c47e1

Proposed after SHA256: 12c49694be025382470e33eb2a166bfb5babe4519ac3dbadda03476ba9ad239e

```diff
--- paper.tex
+++ paper.tex
@@ -444,11 +444,15 @@
 \begin{equation}
 d \;\ge\; d_{\min} = \frac{I\,\kB T\ln 2}{P\,D},
 \end{equation}
-and hence, via Corollary~\ref{cor:product},
-\begin{equation}
-\boxed{\;G \;\ge\; \lambda\,\frac{I\,\kB T \ln 2}{P\,D}\;}
-\end{equation}
-so that every doubling of monitoring power halves the attainable ghost floor.
+and hence, since $G$ is strictly increasing in $L$ in the stochastic order
+(Theorem~\ref{thm:frac}) and, to leading order, bounded above by the
+hazard--latency product (Corollary~\ref{cor:product}),
+\begin{equation}
+\boxed{\;G(d_{\min}) \;\le\; G(d) \;\le\; \lambda d\;}
+\end{equation}
+The attainable ghost fraction is therefore floored by $G(d_{\min})$, which to leading
+order is $\lambda\,I\,\kB T\ln 2/(P\,D)$: every doubling of monitoring power halves
+$d_{\min}$ and hence, to leading order, the attainable floor.
 
 Intellectual honesty requires stating how slack this bound is. At $D=1$,
 acquiring $10^{12}$ bits at $1$~kW takes $2.9\times10^{-12}$~s; the Landauer
```

## Run-113 paper.tex

Source before SHA256: 6fe6bef836f9d2c756fede65b24897f249ed325559ea5e07559b4546b8acbb33

Proposed after SHA256: 1695a87d1c67eb42ba73f071be502a054dfe2ecd1bdc200d595e820348b099d4

```diff
--- paper.tex
+++ paper.tex
@@ -213,8 +213,11 @@
 \begin{equation}
 T_{\mathrm{eff}} \;\geq\; T_a ,
 \end{equation}
-with equality if and only if $T_c = T_a$, $\varepsilon = \kB T_a \ln 2$ and
-$\phi = 0$. Consequently
+with equality if and only if $\phi = 0$, $\varepsilon(T_c) = \kB T_c \ln 2$
+(Landauer saturation at the \emph{operating} temperature), $T_c \leq T_a$, and
+$\eta_2 = 1$ whenever $T_c < T_a$. The equality locus is therefore the entire
+interval $T_c \in (0, T_a]$ at Carnot efficiency, not the single point
+$T_c = T_a$. Consequently
 \begin{equation}
 \boxed{\;\frac{dI}{dt} \;\leq\; \frac{P \cdot D}{\kB\, T_a \ln 2}\;}
 \label{eq:floor}
@@ -228,8 +231,13 @@
 $T_c \geq T_a$, the bracket is at least $T_c \geq T_a$. If $T_c < T_a$, the
 bracket is at least $T_c + (T_a - T_c)/\eta_2 \geq T_c + (T_a - T_c) = T_a$,
 since $\eta_2 \leq 1$. In both cases $T_{\mathrm{eff}} \geq \mu T_a \geq T_a$.
-Equality forces $\mu = 1$, $\phi = 0$ and $\eta_2 = 1$ with the bracket
-saturated, which occurs only at $T_c = T_a$.
+Equality forces $\mu = 1$ (Landauer saturation, $\varepsilon = \kB T_c \ln 2$),
+$\phi = 0$, and the bracket to equal $T_a$ exactly. For $T_c > T_a$ the bracket
+is $T_c > T_a$, so equality requires $T_c \leq T_a$; for $T_c < T_a$ the bracket
+is $T_c + (T_a - T_c)/\eta_2$, which equals $T_a$ if and only if $\eta_2 = 1$;
+at $T_c = T_a$ the bracket equals $T_a$ for every $\eta_2$. This is precisely the
+stated condition, and it is exactly the refrigeration-futility locus discussed
+below --- an interval, not a point.
 \end{proof}
 
 Two readings deserve emphasis. First, \emph{refrigeration futility}: at Carnot
```

## Run-113 README.md

Source before SHA256: 48ee85b291e89aa9984d444ee404b541290b5c7d98ee11e3ec3ae96d2e45a3ba

Proposed after SHA256: 6a13acdd91bf2a2da30048e3622d48a00e5e9e70d35b6ee1247ecc19bbe925c7

```diff
--- README.md
+++ README.md
@@ -25,7 +25,8 @@
 ```
 dI/dt ≤ P·D / (k_B · T_a · ln 2)     for EVERY refrigeration architecture
 ```
-with `T_eff ≥ T_a`, equality iff `T_c = T_a`, `ε = k_B T_a ln2`, `φ = 0`.
+with `T_eff ≥ T_a`, equality iff `φ = 0 ∧ ε = k_B T_c ln2 ∧ T_c ≤ T_a ∧ (T_c < T_a → η₂ = 1)`
+— the equality locus is the full interval `T_c ∈ (0, T_a]` at Carnot, not a point.
 *Refrigeration futility:* at `η₂ = 1` with a Landauer device, `T_eff = T_a` exactly
 at every operating temperature — 1 K, 77 K, 299 K alike.
 
```

## Narrow metadata exception

Only an extra regular file whose exact basename is .DS_Store and whose header is the Finder Bud1 format is ignored. Symlinks, proof-byte mismatches and differing metadata present on both sides still HOLD. Ignored hashes remain reported.

```diff
--- mirror_parity.py
+++ mirror_parity.py
@@ -45,6 +45,17 @@
         result['file_count'] = len(a)
         result['differences'] = [{'path': name, 'source_sha256': a.get(name), 'mirror_sha256': b.get(name)}
                                  for name in sorted(set(a) | set(b)) if a.get(name) != b.get(name)]
+        # User-approved narrow exception: an extra regular Finder .DS_Store
+        # with its format signature may differ in inventory, never proof bytes.
+        ignored=[];kept=[]
+        for difference in result['differences']:
+            name=difference['path']
+            extra=(source/name) if name in a and name not in b else (mirror/name) if name in b and name not in a else None
+            if extra is not None and Path(name).name=='.DS_Store' and extra.read_bytes()[:8]==b'\x00\x00\x00\x01Bud1':
+                ignored.append({**difference,'reason':'EXTRA_FINDER_METADATA_ONLY'})
+            else:kept.append(difference)
+        result['ignored_metadata_differences']=ignored
+        result['differences']=kept
         if not result['differences']:
             result['status'] = 'MATCH'
     except Exception as exc:
```
