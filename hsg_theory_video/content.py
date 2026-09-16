# Slide content + narration for the HSG explainer video.
# Each slide: id, kind (used by render.py to pick a layout), title, body data, narration text.
# "plain" is a short, jargon-free one-line takeaway shown on-slide for a general audience.
# Written for a general audience: short sentences, everyday analogies, terms defined on first use.

SLIDES = [
    dict(
        id="01_title",
        kind="title",
        title="Harmonic Substrate Gravity",
        subtitle="A gravity mix-up, fixed — explained for everyone",
        footer="Based on the HSG sign-convention corrections and analysis report",
        narration=(
            "Imagine one invisible thing, filling all of space, that does two completely different jobs. "
            "Up close, near a planet or a star, it pulls things together — that's gravity. "
            "Far away, across the whole universe, it pushes things apart — that's called dark energy. "
            "One theory, nicknamed H S G, says both of those are really the same thing in disguise. "
            "While double-checking the math, researchers found a small but important mistake: a plus sign where "
            "there should have been a minus sign. This video walks through, in plain English, what that mistake was, "
            "how it got fixed, and what it means."
        ),
    ),
    dict(
        id="02_fabric",
        kind="fabric_well",
        title="Picture gravity as a stretched-out sheet",
        plain="A heavy ball on a trampoline sinks down and pulls nearby marbles toward it — that's the classic gravity picture.",
        caption="This is the everyday picture of gravity: mass dents the sheet, and nearby objects roll inward.",
        narration=(
            "Let's start with a picture you've probably seen before. Imagine space as a big, stretchy trampoline sheet. "
            "Drop a bowling ball onto it, and it sinks down, making a dip. "
            "Now roll a marble nearby, and it curves inward, toward the dip — it looks like it's being pulled toward the ball. "
            "That dip is the standard picture of what gravity is: mass bends the space around it, and nearby things "
            "roll toward that bend. Any theory of gravity has to reproduce this picture, or it isn't describing gravity at all."
        ),
    ),
    dict(
        id="03_balloon",
        kind="balloon_expansion",
        title="Now picture the whole universe as a balloon",
        plain="Blow up a balloon with dots drawn on it, and every dot drifts away from every other dot — that's cosmic expansion.",
        caption="This is the everyday picture of dark energy: space itself stretches, carrying galaxies apart.",
        narration=(
            "Now here's a second picture, for something that looks like the opposite of gravity. "
            "Draw a few dots on a deflated balloon, then blow it up. As the balloon inflates, every dot moves away "
            "from every other dot — not because the dots are moving through the balloon, but because the balloon's "
            "surface itself is stretching. That's very close to what's happening to our universe. Galaxies are drifting "
            "apart because space itself is expanding. Astronomers call whatever is causing that stretching “dark energy,” "
            "and nobody fully knows what it is."
        ),
    ),
    dict(
        id="04_concept",
        kind="bullets",
        title="HSG's big idea: one field, two jobs",
        plain="One invisible field plays both roles — the dip in the sheet, and the stretch of the balloon.",
        bullets=[
            "One invisible field, called δf, is said to fill all of space — like an invisible fabric.",
            "Near a mass, this field creates the “dip” we feel as gravity.",
            "Across the whole universe, the very same field creates the “stretch” we call dark energy.",
            "A single number, related to the golden ratio (the famous 1.618... proportion), controls how the field settles down over time.",
            "It's a tidy idea: one thing, doing both jobs. But the local-gravity math needs to be checked carefully.",
        ],
        narration=(
            "H S G's big idea is that one single field does both jobs at once: it's the dip near a mass, "
            "and it's the stretch across the universe. A special number, tied to the golden ratio — that famous "
            "one point six one eight proportion that shows up in art and nature — controls how this field gradually "
            "settles into a steady state over cosmic time. It's a tidy, elegant idea. But before trusting any idea like this, "
            "you have to check the boring but essential part: does the math actually reproduce ordinary gravity, "
            "the marble rolling into the dip? That check is where the mistake turned up."
        ),
    ),
    dict(
        id="05_setup",
        kind="equation_block",
        title="The checkup: does the math roll the marble in, or out?",
        plain="A simple math checkup: plug the theory's own formula in, and see which way objects move.",
        lines=[
            (r"$g_{00} = -(1 + 2\psi)$", "the standard formula for “how bent is space”"),
            (r"$\Phi_N = -\dfrac{GM}{r}$", "for ordinary gravity, this number is negative near a mass"),
            (r"$\psi = \delta f$", "HSG's own rule for plugging its field into that formula"),
        ],
        note="If δf is positive near a mass, does the marble roll in, or fly out?",
        narration=(
            "Here's the checkup, in plain terms. There's a standard formula, from ordinary physics, for how bent "
            "space is near a mass — and for everyday gravity, a certain number in that formula always works out negative. "
            "H S G plugs its own field directly into that same formula. So the test is simple: using the sign the "
            "theory originally used, positive near a mass, does the marble roll into the dip, the way gravity should work, "
            "or does it fly away instead?"
        ),
    ),
    dict(
        id="06_bug",
        kind="diagram_force",
        title="The mistake: the marble flies away",
        plain="With the original math, the marble gets flung outward — the opposite of gravity.",
        direction="outward",
        color="#e05252",
        eq=r"$\delta f = +\dfrac{GM}{rc^2}\ \Rightarrow\ a_x = +\dfrac{GMx}{r^3}$",
        caption="Checked with computer algebra, step by step: this version of the math pushes things away.",
        narration=(
            "Here's what the checkup found. Using the sign originally published, the math says objects get pushed "
            "away from a mass, not pulled toward it. Picture the trampoline turned into a hill instead of a dip — "
            "anything nearby rolls off and away. In plain terms: instead of falling toward a planet, you'd go flying "
            "off into space. That's the opposite of gravity as we know it. This wasn't a hunch — it was checked "
            "with computer algebra, one careful step at a time, to make sure it wasn't just a one-off slip."
        ),
    ),
    dict(
        id="07_fix",
        kind="diagram_force",
        title="The fix: one sign, flipped",
        plain="Flip a single plus to a minus, and the marble correctly rolls inward again.",
        direction="inward",
        color="#2dd4bf",
        eq=r"$\delta f = -\dfrac{GM}{rc^2}\ \Rightarrow\ a_x = -\dfrac{GMx}{r^3}$",
        caption="Now it matches ordinary gravity exactly — not approximately, exactly.",
        narration=(
            "The fix is refreshingly simple: flip that one sign near a mass, from positive to negative. "
            "Redo the exact same math, and now the marble rolls back into the dip, toward the mass, "
            "exactly matching ordinary gravity — not roughly, exactly. One sign, chosen consistently and carried "
            "through the whole theory, is the entire correction needed here."
        ),
    ),
    dict(
        id="08_table",
        kind="table",
        title="The same fix, applied everywhere",
        plain="One consistent rule, applied everywhere it shows up in the theory.",
        headers=["Where", "Before (wrong)", "After (fixed)"],
        rows=[
            ["Near a mass M", "δf = +GM/rc²", "δf = −GM/rc²"],
            ["Across the universe", "δf = −H₀r/c", "δf = +H₀r/c"],
            ["The far-future resting value", "δf = −1/φ", "δf = +1/φ"],
            ["A black hole's edge", "δf = 1/2", "δf = −1/2"],
        ],
        narration=(
            "That one decision ripples through every other place in the theory where this field shows up, "
            "so each one gets flipped to match. Near a mass, the field is now negative instead of positive. "
            "Across the universe, it's positive instead of negative — the exact opposite pattern. "
            "The far-future resting value flips too, and so does the description of a black hole's edge. "
            "Same rule, applied consistently, everywhere."
        ),
    ),
    dict(
        id="09_unaffected",
        kind="bullets",
        title="The good news: most of it didn't need fixing",
        plain="Good news: most of the theory’s hard results survive completely untouched.",
        bullets=[
            "The field's energy math depends on the field multiplied by itself — and multiplying a negative by itself gives a positive, same as a positive times itself.",
            "So the field's density, pressure, and “springiness” number stay exactly the same as before.",
            "The core equations and the golden-ratio constant don't move at all.",
            "The upper limit on how strong this effect can be doesn't change either — a sign doesn't change a size limit.",
            "And one whole prediction — that time-shifts look the same run forward or backward — still holds, untouched.",
        ],
        narration=(
            "Here's the reassuring part. A lot of the theory's central results depend on this field multiplied by itself, "
            "and multiplying a negative number by itself gives a positive result, just like multiplying a positive "
            "number by itself does — the sign disappears. So the field's energy, its pressure, its “springiness” number, "
            "the core equations, the golden-ratio constant, the strength limits, and one whole prediction about "
            "time running the same forward and backward — none of that needed to change. This was a small, "
            "local fix, not a rewrite of the whole theory."
        ),
    ),
    dict(
        id="10_eq_change",
        kind="equation_block",
        title="The one thing that DOES change: a timing prediction",
        plain="One testable number flips — from “clocks run a touch fast” to “clocks run a touch slow.”",
        lines=[
            (r"$1 + \kappa\delta f = 1 + \kappa/\varphi$", "the far-future value now adds a bit, not subtracts"),
            (r"$S = \dfrac{-\kappa\,\Phi_{\mu\nu}u^{\mu}\Delta x^{\nu}}{1+\kappa/\varphi}$", "the full timing formula"),
            (r"$\Delta t_{HSG} = \Delta t_{SR}\times(1-\kappa/\varphi)$", "the simplified result — flipped from a plus to a minus"),
        ],
        note=None,
        narration=(
            "One thing does change, and it's the part you could actually go measure with a clock: a small correction "
            "to exactly when two distant events appear to happen at the same time. Because the far-future resting "
            "value flipped sign, this correction flips too — what used to nudge the timing a little bit one way "
            "now nudges it the same small amount the other way."
        ),
    ),
    dict(
        id="11_prediction6",
        kind="bar_compare",
        title="The headline prediction flips: early → late",
        plain="The theory now predicts a clock running slightly behind schedule, not ahead of it.",
        left_label="Before (wrong)",
        left_value=0.340,
        right_label="After (fixed)",
        right_value=-0.340,
        unit="days",
        caption="For one example scenario → fixed prediction: 10.660 days instead of 11.000",
        narration=(
            "This is the number you could actually put to the test. For one example scenario, the old, uncorrected "
            "theory predicted a clock running zero point three four zero of a day ahead of schedule — early. "
            "The corrected theory predicts the opposite: the same clock runs zero point three four zero of a day "
            "behind schedule — late. That's a real, practical difference. An experiment built to look for an early "
            "clock would now need to look for a late one instead. Finding the old “early” result would actually "
            "disprove the corrected theory."
        ),
    ),
    dict(
        id="12_arithmetic",
        kind="bullets",
        title="A second, unrelated slip in the numbers",
        plain="A basic arithmetic check turned up a mismatch — unrelated to the sign mix-up.",
        bullets=[
            "The paper's own example used a distance and a small speed difference to predict an 11-day gap.",
            "Redoing that arithmetic gives 4.27 days, not 11 — about two and a half times smaller.",
            "Matching the claimed 11 days needs a speed difference over twice as large as what was written down.",
            "This slip has nothing to do with the sign mix-up — it was already sitting in the original paper.",
        ],
        narration=(
            "Completely separate from the sign issue, there's a plain arithmetic slip in that same example. "
            "Plugging the paper's own numbers into its own formula gives a gap of about four and a quarter days, "
            "not the eleven days the paper claims — a mismatch of about two and a half times. "
            "To actually reach eleven days, the speed difference would need to be more than double what's written. "
            "Either the speed or the day count needs correcting, and this one has nothing to do with anything else in this video."
        ),
    ),
    dict(
        id="13_cosmology",
        kind="donut",
        title="A missing ingredient: ordinary stuff",
        plain="The cosmology model forgot to count ordinary matter — stars, gas, dark matter — as part of the universe.",
        center_label="today's\nuniverse",
        slices=[
            dict(label="This field\n(dark energy)", value=70, color="#d4af37"),
            dict(label="Ordinary + dark matter", value=30, color="#5b8def"),
        ],
        caption="Earlier math assumed the field alone fills the universe; real data says matter is still about 30% today.",
        narration=(
            "A second, independent slip turned up in the cosmology part of the calculation: it left out ordinary "
            "matter entirely — stars, gas, dark matter, all of it. Without matter to compete with, the field's "
            "influence races all the way to its extreme, far-future strength immediately. But real observations "
            "say matter still makes up around thirty percent of the universe's energy today. Putting that thirty "
            "percent back into the equations gives a more moderate, more realistic prediction for how this field "
            "is behaving right now. The original extreme number wasn't wrong — it just describes the very distant "
            "future, not today."
        ),
    ),
    dict(
        id="14_desi",
        kind="grouped_bar",
        title="How does it hold up against real telescope data?",
        plain="Tested against real data from the DESI telescope survey: it's competitive, not disproven.",
        categories=["+Pantheon+", "+DES-Dovekie", "+DESY5", "+Union3"],
        series_a=dict(label="HSG", values=[3.3, 3.2, 1.5, 2.5], color="#d4af37"),
        series_b=dict(label="Standard model", values=[2.0, 2.6, 3.4, 3.3], color="#5b8def"),
        ylabel="tension with data (lower is better)",
        caption="Neither model is ruled out; each fits some supernova datasets better than others.",
        narration=(
            "So how does the corrected theory actually hold up against real observations? Researchers compared it "
            "to the standard cosmology model, across four different collections of supernova measurements, "
            "combined with results from the DESI telescope survey. Shorter bars mean a better fit to the data. "
            "H S G fits one dataset, called DESY5, better than the standard model does. It fits another, called "
            "Pantheon-plus, worse than the standard model does. Bottom line: neither model is ruled out here — "
            "they're genuinely competitive with each other."
        ),
    ),
    dict(
        id="15_caveats",
        kind="bullets",
        title="Being upfront about what's still unresolved",
        plain="Three open questions the theory still has to answer.",
        bullets=[
            "Real data wants dark energy's strength to change over time faster than this kind of field is able to.",
            "Part of the statistical comparison used a careful estimate, not the full official telescope dataset.",
            "The golden-ratio number is currently chosen to fit the answer — not yet derived from a deeper reason.",
            "The relative comparison (this theory vs. the standard model) is solid; the exact confidence numbers may shift.",
        ],
        narration=(
            "A few honest caveats, to be upfront about. First, this kind of field has a built-in mathematical speed "
            "limit on how quickly its strength can change over time, and the real data seem to want it to change a "
            "little faster than that limit allows. Second, part of the statistical comparison used a careful estimate "
            "rather than the full, official telescope dataset, so the exact confidence numbers may shift once that's "
            "redone properly. And third, that famous golden-ratio number at the heart of this theory is currently "
            "chosen specifically to produce the right answer, rather than coming from some deeper, independent reason. "
            "That's an open problem, and it's stated plainly rather than hidden."
        ),
    ),
    dict(
        id="16_close",
        kind="bullets",
        title="What happens next",
        plain="A clear, honest to-do list — the mark of a theory being taken seriously.",
        bullets=[
            "1. Fix the day-count slip in the example prediction.",
            "2. Apply the sign fix consistently through the whole paper.",
            "3. Re-derive the timing-prediction equations with the corrected sign.",
            "4. Publish the corrected, more moderate present-day prediction.",
            "5. Redo the telescope-data comparison with the full, official dataset.",
            "6. Either explain the golden-ratio number from first principles, or say plainly that it's fitted.",
        ],
        footer="Reviewers respond well to an author who finds and reports their own mistake.",
        narration=(
            "So here's the path forward: fix the arithmetic slip, apply the sign fix consistently everywhere, "
            "re-derive the timing predictions, publish the corrected, more moderate result, redo the telescope "
            "comparison with the full official data, and either explain that golden-ratio number properly or say "
            "plainly that it's fitted for now. None of this breaks the theory. If anything, it's a theory that found "
            "its own mistake, carefully checked what still held up, and came out the other side with a sharper, "
            "more testable, and more honest prediction. That's exactly how good science is supposed to work."
        ),
    ),
]
