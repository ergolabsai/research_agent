// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

/**
 * Graph analysis fixture data for the demo paper:
 * "Ultrafast isomerization initiated by X-ray core ionization"
 *
 * Parsed from validation_results.md GRAPH ANALYSIS section.
 * Served by the mock /pipeline/analysis/:jobId endpoint.
 */

import type { GraphAnalysis } from "../types";

export const graphAnalysisResult: GraphAnalysis = {
  node_counts: {
    steps: 20,
    evidence: 97,
    figures: 3,
    math: 7,
    related_papers: 0,
  },
  steps_without_evaluation: [
    {
      step_number: 4,
      description:
        "C2D2 (deuterated acetylene) was used instead of C2H2 to eliminate potential background contamination from water/contaminant protons.",
    },
  ],
  contradicted_steps: [
    {
      step_number: 1,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not display any explicit information about the 2.3 eV barrier height, the 60 fs timescale, or the predicted vibrational excitation levels relative to the barrier.",
        "The figure does not show or annotate any timescale information (neither the 60 fs upper limit nor picosecond predictions from transition-state theory).",
        "The double-well minimum structure visible in the \u00b9\u03a3_g\u207a curve appears to show a relatively small barrier between the two minima, which does not obviously convey the 2.3 eV barrier magnitude.",
        "The figure does not include any indication of the degree of vibrational excitation expected after Auger decay relative to the barrier height.",
      ],
    },
    {
      step_number: 2,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure is a static excitation scheme diagram and does not contain any time-resolved information, comparison with optical strong-field experiments, or depiction of the ~90 fs timescale.",
        "The figure does not show or compare the dicationic state distributions produced by strong-field ionization versus core ionization; it only depicts the core ionization pathway.",
        "The expected description mentions a 'variable delay' between pump and probe pulses, but the actual figure does not appear to indicate a time delay.",
      ],
    },
    {
      step_number: 3,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not display the pulse duration ('up to 10 fs') or pulse energy ('100 \u03bcJ') parameters; only the 400 eV photon energy is labeled.",
        "The figure does not show any indication of a variable time delay between the pump and probe pulses.",
        "The figure does not explicitly indicate that C\u2082D\u2082\u2074\u207a has no bound states or that it Coulomb-explodes.",
        "The figure does not explicitly reference LCLS or identify this as a time-resolved experiment.",
      ],
    },
    {
      step_number: 5,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not depict or reference any alternative ionization pathways that could lead to the 4+ charge state.",
        "The figure does not include any quantitative information about cross-sections, branching ratios, or relative probabilities of different ionization pathways.",
        "The figure does not explicitly indicate that reaching 4+ from a single X-ray photon is 'nearly impossible.'",
        "The figure does not show or label any shake ionization processes or L-shell ionization channels.",
      ],
    },
    {
      step_number: 6,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not depict or illustrate the coincidence detection apparatus, momentum imaging setup, or any detector geometry.",
        "The figure does not show or illustrate the application of momentum conservation constraints or charge conservation filtering.",
        "The figure does not specifically show the four-body breakup channel C\u207a/C\u207a/D\u207a/D\u207a.",
        "The actual figure does not appear to depict a detection or analysis stage beyond showing the C\u2082D\u2082\u2074\u207a charge state.",
      ],
    },
    {
      step_number: 10,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not contain any information about Auger electron energies or coincidence measurements that would directly demonstrate isomerization occurs exclusively from the 1\u03c0_u\u207b\u00b2 configuration.",
        "The figure shows the \u00b9\u0394_g state alongside \u00b9\u03a3_g\u207a as both being 1\u03c0_u\u207b\u00b2 states, but the claim specifically attributes isomerization to the 'lowest singlet states' \u2014 introducing ambiguity.",
        "The figure does not provide direct evidence that the dicationic state distributions are identical between this experiment and Osipov et al.",
      ],
    },
    {
      step_number: 16,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not depict or indicate any nuclear/geometric dynamics occurring during the core-hole lifetime of the C\u2082D\u2082\u207a state.",
        "The figure does not show or reference the ~6 fs carbon 1s core-hole lifetime that is central to the claim.",
        "The figure does not distinguish between light nuclei (deuterons/protons) and heavier nuclei in terms of their response to the core ionization.",
        "The figure does not include any potential energy surface for the core-excited C\u2082D\u2082\u207a* state.",
        "The variable delay between pump and probe pulses is not indicated in the figure.",
      ],
    },
    {
      step_number: 19,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not display the 2.3 eV isomerization barrier on the \u00b9\u03a3_g\u207a potential energy surface; curves are plotted along the C\u2013C dissociation coordinate rather than the isomerization coordinate.",
        "The figure does not show the potential energy surface of the core-excited singly charged ion along the bending coordinate.",
        "The figure does not depict any time-dependent dynamics, wavepacket evolution, or nuclear motion during the core-hole lifetime.",
        "The figure does not provide any comparison between the transition-state theory prediction and the observed ultrafast isomerization timescale.",
        "The potential energy curves are along the C\u2013C dissociation coordinate and primarily illustrate fragmentation channels rather than the isomerization pathway.",
      ],
    },
    {
      step_number: 20,
      figure: "excitation_scheme.jpg",
      contradictions: [
        "The figure does not depict or indicate a variable time delay between the pump and probe pulses.",
        "The figure does not show or reference four-particle coincident detection or fragment momentum analysis.",
        "The figure does not contain any information about radiation damage in biomolecules or single-molecule diffraction experiments.",
        "The figure does not show any time-dependent data, molecular geometry evolution, or 'molecular movie' snapshots.",
        "The figure does not indicate that this is the first use of four-particle coincident detection at an X-ray FEL.",
        "The figure does not explicitly connect the depicted excitation scheme to hydrocarbon isomerization models.",
      ],
    },
    {
      step_number: 11,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The actual figure description does not explicitly confirm that panel (b) represents '0 fs.'",
        "The description does not explicitly characterize panel (b) as showing 'maximum localization' or connect it to near-linear geometry.",
        "The claim about 'turning points of the CCD bending mode' requires knowledge of the neutral potential energy surface not directly depicted.",
        "Panel (i) shows the wavepacket broadening only up to 9 fs on the cation surface, not on the neutral surface relevant to the claim.",
      ],
    },
    {
      step_number: 12,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The actual figure description does not explicitly label the panels with their time delays (0, 12, 25, 50, 100 fs).",
        "The description of panel (c) does not explicitly mention an increase in CCD angle or spread.",
        "The claim states 'progressive delocalization' but the expected description notes non-monotonic behavior at 25 fs, suggesting vibrational coherence.",
        "The description of panel (d) at 25 fs does not indicate whether it represents more or less delocalization than panel (c).",
        "Neither the actual nor expected figure descriptions explicitly confirm increased spread at 12 fs specifically.",
      ],
    },
    {
      step_number: 13,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The actual figure description does not clearly confirm an increase from 0 fs to 12 fs; the described trajectory does not explicitly mention the 12 fs data point.",
        "The figure reports only ~4-5 data points with substantial error bars (\u00b10.05-0.1), limiting confidence in the vibrational coherence interpretation.",
        "The figure description does not explicitly identify the signal ratio as the ratio of region 1 to region 2 signal.",
      ],
    },
    {
      step_number: 14,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The figure does not contain any data from the three-fragment (C+/C+/D+) coincidence channel; all panels show four-fragment results only.",
        "The three-fragment corroborating evidence is in Supplementary Fig. 2, not shown in this figure.",
        "No panel provides a side-by-side comparison between the four-fragment and three-fragment coincidence results.",
      ],
    },
    {
      step_number: 15,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The figure does not contain any direct visual indicator showing cross-correlation effects on the zero-delay point.",
        "The figure does not show any evidence of double-core-hole signatures or their suppression.",
        "The figure provides no comparison between equal-charge-sharing and unequal-charge-sharing channels.",
        "Panel (b) at 0 fs does not appear anomalous, showing maximum localization as expected without obvious distortion.",
      ],
    },
    {
      step_number: 16,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "Panel (i) does not explicitly label the cation state with spectroscopic term symbols.",
        "The figure description does not explicitly mention Auger relaxation or its interruption of geometric evolution.",
        "Panel (h) shows the signal ratio trajectory ambiguously compared to the expected description of an increase at 12 fs.",
      ],
    },
    {
      step_number: 17,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The figure labels the blue curve simply as 'Cation' without specifying it as the core-excited singly charged ion.",
        "The claim states the potential is 'more anharmonic' in the cation, but the figure characterizes the cation curve as having a 'parabolic shape' suggesting relatively harmonic behavior.",
        "The figure does not explicitly connect the wavepacket broadening to 'Auger relaxation' timescale.",
      ],
    },
    {
      step_number: 18,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "Panel (i) shows wavepacket evolution only up to 9 fs and does not show subsequent Franck-Condon projection onto dication states.",
        "The figure does not contain any direct comparison of Franck-Condon overlaps computed with versus without core-hole dynamics.",
        "Panel (i) does not show the dication potential energy surface or the isomerization barrier height (~2.3 eV).",
        "Panel (i) labels the curves generically as 'Cation' and 'Neutral' without spectroscopic term symbols.",
      ],
    },
    {
      step_number: 19,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "Panel (i) shows wavepacket evolution only up to 9 fs, and the spreading appears modest.",
        "The figure does not show any direct comparison between the TST prediction and observed dynamics.",
        "Panel (i) does not display the dication potential energy surface or its 2.3 eV isomerization barrier.",
        "Panel (h) has substantial error bars on only 4-5 data points, limiting statistical confidence.",
        "The non-monotonic behavior in panel (h) could be consistent with vibrational coherence on the dication surface itself.",
      ],
    },
    {
      step_number: 20,
      figure: "temporal_evolution_of_the_deuteron_momenta.jpg",
      contradictions: [
        "The figure does not contain any explicit information about radiation damage modeling or single-molecule diffraction experiments.",
        "The error bars are substantial (\u00b10.05\u20130.1), with only 4\u20135 data points spanning 0\u2013100 fs.",
        "The figure does not directly demonstrate that this is the 'first time' four-particle coincident detection was used at an X-ray FEL.",
        "Panel (g) appears to show a single molecular structure diagram rather than clearly distinguishable separate depictions.",
        "The time delays sampled are relatively sparse, and the 'molecular movie' metaphor implies continuous coverage.",
      ],
    },
    {
      step_number: 6,
      figure: "acetylene-vinylidene_differentiation.jpg",
      contradictions: [
        "The figure does not explicitly label or indicate the specific ion species (C+/C+/D+/D+).",
        "The figure does not display any information about the momentum conservation filtering process.",
        "The figure does not show any comparison with unfiltered data or background.",
        "The figure provides no direct visual confirmation that the data specifically arise from C2D2^4+ Coulomb explosion.",
      ],
    },
    {
      step_number: 7,
      figure: "acetylene-vinylidene_differentiation.jpg",
      contradictions: [
        "The figure does not display or indicate the additional constraint from Equation 2 requiring the two C+ ions to depart nearly back-to-back.",
        "The actual figure labels the x-axis as 'CCD angle (rad)' rather than explicitly as \u03b8 or referencing Equation 1.",
        "The figure does not provide any information about deuterium or deuteron momenta specifically.",
      ],
    },
    {
      step_number: 8,
      figure: "acetylene-vinylidene_differentiation.jpg",
      contradictions: [
        "The figure does not contain any visual annotation conveying the caveat about \u03b8 being only an approximate measure.",
        "The figure does not provide any means to distinguish genuine V-like isomerization events from those arising from CCD\u207a fragment rotation.",
      ],
    },
    {
      step_number: 9,
      figure: "acetylene-vinylidene_differentiation.jpg",
      contradictions: [
        "The claim states V-like events have a 'narrower distribution' but the figure shows the V-like distribution as 'broader, more structured.' This directly contradicts the claim.",
        "The paper text indicates the A-like channel should be broader, yet the figure appears to show the V-like distribution as broader or comparably broad.",
        "The phrase 'several electronvolts' in the claim may understate the actual difference visible in the figure (10\u201320 eV peak separation).",
      ],
    },
    {
      step_number: 10,
      figure: "acetylene-vinylidene_differentiation.jpg",
      contradictions: [
        "The figure does not contain any Auger electron energy information used by Osipov et al. to assign the isomerization signal.",
        "There is a discrepancy regarding KER distribution widths between the expected and actual figure descriptions.",
        "The experiment uses four-body fragmentation rather than the two-body channels studied by Osipov et al., making direct mapping non-self-evident.",
        "The figure uses deuterated acetylene rather than C\u2082H\u2082, and different nuclear masses could affect fragmentation dynamics.",
      ],
    },
    {
      step_number: 11,
      figure: "acetylene-vinylidene_differentiation.jpg",
      contradictions: [
        "The claim refers to Fig. 3 (temporal evolution), but this figure (Fig. 2) shows KER vs. CCD angle integrated over all time delays.",
        "Figure 2 contains no temporal information; it is 'data integrated over all time delays.'",
        "The figure does not display deuteron momentum distributions in parallel and perpendicular components as described for Fig. 3.",
        "The claim about turning points of the CCD bending mode requires time-resolved data not available in this time-integrated figure.",
      ],
    },
  ],
};
