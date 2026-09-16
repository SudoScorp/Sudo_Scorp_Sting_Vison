# Slide content + narration for the HSG explainer video.
# Each slide: id, kind (used by render.py to pick a layout), title, body data, narration text.
# "plain" is a short, jargon-free one-line takeaway shown on-slide for a general audience.

SLIDES = [
    dict(
        id="01_title",
        kind="title",
        title="Harmonic Substrate Gravity",
        subtitle="A sign-convention correction, explained simply",
        footer="Based on the HSG sign-convention corrections and analysis report",
        narration=(
            "Imagine one invisible field filling all of space, and imagine that the very same field "
            "is responsible both for gravity pulling things together, and for dark energy pushing the universe apart. "
            "That is the idea behind a theory called Harmonic Substrate Gravity, or H S G. "
            "While checking the math behind it, researchers found a sign mistake, plus and minus flipped, "
            "in how that field creates ordinary gravity. This video walks through what the mistake was, "
            "how it was fixed, what stayed the same, and what it means for testing this theory against real data."
        ),
    ),
    dict(
        id="02_concept",
        kind="bullets",
        title="The core idea of HSG",
        plain="One field. Two jobs: gravity up close, dark energy far away.",
        bullets=[
            "One field, called δf, fills space — think of it like an invisible, stretchy fabric.",
            "Near a mass, the fabric's shape is what we feel as gravity: ψ = δf.",
            "The field also behaves like a fluid: it has a density, a pressure, and a “stiffness” number w.",
            "A single constant, α = √3/φ (φ is the golden ratio), slowly pulls the field toward a steady resting value.",
            "Same field, two roles: curve spacetime near mass, and stretch the universe apart at large scales.",
        ],
        narration=(
            "Here's the concept in plain terms. Picture one invisible field, called delta f, spread through all of space, "
            "like a stretchy fabric. Near a planet or a star, the shape of that fabric is what we experience as gravity. "
            "Far away, on the scale of the whole universe, the same field is what pushes galaxies apart — "
            "what astronomers call dark energy. One constant, alpha, tied to the golden ratio, slowly pulls the field "
            "toward a steady, long-term value. It's an elegant idea: one thing doing gravity's job and dark energy's job at once. "
            "But when the local-gravity math was checked carefully, a sign got flipped — plus where it should have been minus."
        ),
    ),
    dict(
        id="03_setup",
        kind="equation_block",
        title="Testing the weak-field limit",
        plain="Simple check: does the math actually pull objects together, or push them apart?",
        lines=[
            (r"$g_{00} = -(1 + 2\psi)$", "the standard weak-field metric"),
            (r"$\Phi_N = -\dfrac{GM}{r}$", "Newton's potential is negative near a mass"),
            (r"$\psi = \delta f$", "HSG's identification of the metric potential"),
        ],
        note="If δf is positive near a mass, does this combination pull, or push?",
        narration=(
            "Before trusting any new theory of gravity, there's a basic test: does it reproduce ordinary, "
            "everyday Newtonian gravity for something simple, like an apple falling, or a planet orbiting a star? "
            "That's the test applied here. Standard general relativity already tells us, mathematically, what "
            "attractive gravity has to look like near a mass. H S G plugs its own field directly into that formula. "
            "So the question becomes very concrete: with the sign the paper originally used, does the resulting force "
            "pull a test object inward, toward the mass, or push it away?"
        ),
    ),
    dict(
        id="04_bug",
        kind="diagram_force",
        title="The bug: repulsive gravity",
        plain="With the original sign, the equations predict objects get pushed away from mass — the opposite of gravity.",
        direction="outward",
        color="#e05252",
        eq=r"$\delta f = +\dfrac{GM}{rc^2}\ \Rightarrow\ a_x = +\dfrac{GMx}{r^3}$",
        caption="Verified symbolically with SymPy: this sign gives repulsion, not attraction.",
        narration=(
            "Here's what the check found. Using the sign originally published, working through the math step by step, "
            "gives an acceleration that points away from the mass, not toward it. In plain terms: instead of "
            "falling toward a planet, an object would be pushed away from it. That's the opposite of gravity as we know it. "
            "This wasn't a guess or a rough estimate — it was checked symbolically, term by term, using computer algebra, "
            "to make sure it wasn't a one-off arithmetic slip."
        ),
    ),
    dict(
        id="05_fix",
        kind="diagram_force",
        title="The fix: flip one sign",
        plain="Flip a single plus to a minus, and the theory correctly predicts ordinary attractive gravity.",
        direction="inward",
        color="#2dd4bf",
        eq=r"$\delta f = -\dfrac{GM}{rc^2}\ \Rightarrow\ a_x = -\dfrac{GMx}{r^3}$",
        caption="This matches the Newtonian target exactly.",
        narration=(
            "The fix turns out to be simple: flip that one sign near a mass, from positive to negative. "
            "Redo the exact same calculation, and now the acceleration points inward, toward the mass — "
            "and it matches everyday Newtonian gravity exactly, not approximately. One sign, chosen consistently "
            "and carried through the whole theory, is the entire correction needed at this level."
        ),
    ),
    dict(
        id="06_table",
        kind="table",
        title="The sign flip, region by region",
        plain="One consistent rule, applied everywhere it shows up in the theory.",
        headers=["Region", "Old (v1–v4)", "Corrected (v5)"],
        rows=[
            ["Near a mass M", "δf = +GM/rc²", "δf = −GM/rc²"],
            ["Cosmic expansion", "δf = −H₀r/c", "δf = +H₀r/c"],
            ["Cosmological ground state", "δf = −1/φ", "δf = +1/φ"],
            ["Black hole horizon", "δf = 1/2", "δf = −1/2"],
        ],
        narration=(
            "That one decision ripples through every other sign statement in the theory, so each one had to be "
            "flipped to match. Near a mass, the field is now negative instead of positive. Out in cosmic expansion, "
            "it's positive instead of negative — the exact opposite pattern. The long-term resting value of the "
            "universe flips too, and so does the condition describing a black hole's edge, its event horizon. "
            "It's the same rule, applied consistently everywhere."
        ),
    ),
    dict(
        id="07_unaffected",
        kind="bullets",
        title="What does NOT change",
        plain="Good news: most of the theory’s hard results survive completely untouched.",
        bullets=[
            "The field's energy content — it depends on the field squared, and squaring erases the sign.",
            "Density, pressure, and the “stiffness” number w = −1/φ (the whole earlier derivation survives).",
            "The core equations, the constant α = √3/φ, and the long-term resting value.",
            "The bound on the coupling strength κ — a sign doesn't change a size limit.",
            "Prediction 7 (that time runs the same forward and backward): still holds.",
        ],
        narration=(
            "Here's the reassuring part. Several of the theory's central results are built from the field "
            "multiplied by itself — and squaring a number always erases its sign, whether it started positive or negative. "
            "So the field's energy and pressure, and the key number describing how “stiff” it is, are completely unaffected. "
            "The core equations, the golden-ratio constant, the long-term resting value, the strength limits, and the prediction "
            "that time-shifts look the same forwards and backwards — all of that survives untouched. "
            "This is a narrow, local fix, not a rewrite of the whole theory."
        ),
    ),
    dict(
        id="08_eq_change",
        kind="equation_block",
        title="What DOES change: a timing prediction",
        plain="One testable number flips sign — from “clocks run a bit fast” to “clocks run a bit slow.”",
        lines=[
            (r"$1 + \kappa\delta f = 1 + \kappa/\varphi$", "ground state now adds, not subtracts"),
            (r"$S = \dfrac{-\kappa\,\Phi_{\mu\nu}u^{\mu}\Delta x^{\nu}}{1+\kappa/\varphi}$", "equation (16)"),
            (r"$\Delta t_{HSG} = \Delta t_{SR}\times(1-\kappa/\varphi)$", "equation (18) — was (1 + κ/φ)"),
        ],
        note=None,
        narration=(
            "One thing does change, and it's the part you could actually go out and measure: a small correction "
            "to how simultaneous two events appear to be, compared to plain old special relativity. "
            "Because the long-term resting value flipped sign, this correction flips too — "
            "what used to add a small amount to the timing difference now subtracts that same small amount."
        ),
    ),
    dict(
        id="09_prediction6",
        kind="bar_compare",
        title="The headline prediction flips: excess → deficit",
        plain="The theory now predicts clocks running slightly behind schedule, not ahead of it.",
        left_label="Old (v1–v4)",
        left_value=0.340,
        right_label="Corrected (v5)",
        right_value=-0.340,
        unit="days",
        caption="For one example scenario → corrected prediction: 10.660 days instead of 11.000",
        narration=(
            "This is the number you could actually test in an experiment. For one example scenario, "
            "the old, uncorrected theory predicted that a clock would run zero point three four zero of a day ahead of schedule. "
            "The corrected theory predicts the opposite: the same clock runs zero point three four zero of a day behind schedule. "
            "That's a real, practical difference. An experiment built to look for clocks running fast would now need "
            "to look for clocks running slow instead — finding the old “fast” result would actually disprove the corrected theory."
        ),
    ),
    dict(
        id="10_arithmetic",
        kind="bullets",
        title="A second, separate mistake in the numbers",
        plain="A basic arithmetic check turned up a mismatch — unrelated to the sign error.",
        bullets=[
            "The paper's example used a distance and a small speed difference to predict an 11-day gap.",
            "Redoing that arithmetic gives 4.27 days, not 11 — about a factor of 2.6 off.",
            "Matching the claimed 11 days needs a speed difference over twice as large as stated.",
            "This mistake has nothing to do with the sign flip — it was already there in the original paper.",
        ],
        narration=(
            "Separate from the sign issue entirely, there's a plain arithmetic mistake in the same example. "
            "Plugging the paper's own numbers — a distance and a small difference in speed — into its own formula "
            "gives a gap of about four and a quarter days, not the eleven days the paper claims. "
            "To actually reach eleven days, the speed difference would need to be more than double what's stated. "
            "Either the speed or the day count needs correcting, independent of everything else in this video."
        ),
    ),
    dict(
        id="11_cosmology",
        kind="bullets",
        title="A missing ingredient: ordinary matter",
        plain="The cosmology model forgot to include normal matter — stars, gas, dark matter — in its equations.",
        bullets=[
            "The earlier result assumed the field completely dominates the universe's energy budget.",
            "That's only true in the very distant future — today, ordinary matter still matters a lot.",
            "Adding matter back in, using the observed amount (about 30% of the universe's energy):",
            "the prediction shifts from an extreme value to a more moderate, realistic one.",
            "The original number is still correct — just as a description of the far future, not of today.",
        ],
        narration=(
            "A second, independent bug turned up in the cosmology calculation: it left out ordinary matter — "
            "stars, gas, dark matter, all of it. Without matter slowing things down, the field races all the way to its "
            "extreme, far-future value immediately, which only makes sense if matter made up almost nothing of the universe's "
            "energy. But observations put matter at around thirty percent of the total, today. Putting matter back into "
            "the equations, at that observed thirty percent, gives a more moderate, more realistic prediction for how dark "
            "energy is behaving right now. The original extreme value isn't wrong — it's just a description of the "
            "distant future, not of the present day."
        ),
    ),
    dict(
        id="12_desi",
        kind="grouped_bar",
        title="How does it compare to real telescope data?",
        plain="Tested against real data from the DESI telescope survey: it's competitive, not disproven.",
        categories=["+Pantheon+", "+DES-Dovekie", "+DESY5", "+Union3"],
        series_a=dict(label="HSG", values=[3.3, 3.2, 1.5, 2.5], color="#d4af37"),
        series_b=dict(label="ΛCDM (standard model)", values=[2.0, 2.6, 3.4, 3.3], color="#5b8def"),
        ylabel="tension with data (lower is better)",
        caption="Neither model is ruled out; each fits some supernova datasets better than others.",
        narration=(
            "So how does the corrected theory actually hold up against real observations? "
            "Researchers compared it to the standard cosmological model across four different collections of "
            "supernova measurements, combined with results from the DESI telescope survey. Shorter bars here mean "
            "a better fit to the data. H S G fits one dataset, called DESY5, better than the standard model does. "
            "It fits another, called Pantheon-plus, worse than the standard model does. Bottom line: "
            "neither model is ruled out by this comparison — they're genuinely competitive with each other."
        ),
    ),
    dict(
        id="13_caveats",
        kind="bullets",
        title="Being honest about the remaining weak spots",
        plain="Three open questions the theory still has to answer.",
        bullets=[
            "The theory can't easily match how sharply dark energy's behavior seems to be changing over time.",
            "The statistical comparison used an estimate, not the full, official telescope dataset.",
            "The golden-ratio constant is currently chosen to fit the answer — not yet derived from first principles.",
            "The relative comparison (HSG vs. standard model) is solid; the exact confidence numbers still need refining.",
        ],
        narration=(
            "A few honest caveats, to be upfront about. First, this type of field has a built-in mathematical limit "
            "on how quickly its behavior can change over time, and the real data seem to want it to change a bit faster "
            "than that limit allows. Second, part of the statistical comparison used a reasonable estimate rather than "
            "the full, official telescope dataset, so the exact confidence numbers may shift once that's redone properly. "
            "And third, the famous golden-ratio constant at the heart of this theory is currently chosen specifically "
            "to produce the right answer, rather than being derived independently from some deeper principle. "
            "That's an open problem, not a hidden one."
        ),
    ),
    dict(
        id="14_close",
        kind="bullets",
        title="What happens next",
        plain="A clear, honest to-do list — the mark of a theory being taken seriously.",
        bullets=[
            "1. Fix the day-count arithmetic mistake in the example prediction.",
            "2. Apply the sign correction consistently throughout the paper.",
            "3. Re-derive the timing-prediction equations with the corrected sign.",
            "4. Publish the corrected, more moderate present-day prediction.",
            "5. Redo the telescope-data comparison with the full, official dataset.",
            "6. Either derive the golden-ratio constant from first principles, or say plainly that it's fitted.",
        ],
        footer="Reviewers respond well to an author who finds and reports their own error.",
        narration=(
            "So, here's the path forward: fix the arithmetic mistake, apply the sign correction consistently everywhere, "
            "re-derive the timing predictions, publish the corrected, more moderate result, redo the telescope comparison "
            "with the full official data, and either derive that golden-ratio constant properly or say plainly that it's fitted for now. "
            "None of this breaks the theory. If anything, it's a theory that found its own mistake, checked carefully what "
            "still held up, and came out the other side with a sharper, more testable, and more honest prediction. "
            "That's exactly how good science is supposed to work."
        ),
    ),
]
